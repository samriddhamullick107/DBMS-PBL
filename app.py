import os
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-this-development-key")

def get_db():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "smart_traffic_db"),
        port=int(os.environ.get("DB_PORT", "3306")),
    )

def query_all(sql, params=()):
    conn = get_db()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def execute(sql, params=()):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        return cur.lastrowid
    finally:
        cur.close()
        conn.close()

@app.route("/")
def dashboard():
    try:
        stats = query_all("""
            SELECT
              (SELECT COUNT(*) FROM drivers) AS drivers,
              (SELECT COUNT(*) FROM vehicles) AS vehicles,
              (SELECT COUNT(*) FROM violation_records) AS violations,
              (SELECT COALESCE(SUM(fine_amount), 0) FROM violation_records) AS total_fines
        """)[0]
        recent = query_all("""
            SELECT vr.record_id, v.registration_no, vi.violation_type,
                   vr.violation_date, vr.location, vr.fine_amount, vr.status
            FROM violation_records vr
            JOIN vehicles v ON v.vehicle_id = vr.vehicle_id
            JOIN violation_types vi ON vi.violation_type_id = vr.violation_type_id
            ORDER BY vr.record_id DESC LIMIT 5
        """)
        return render_template("dashboard.html", stats=stats, recent=recent)
    except Error as e:
        return render_template("setup_error.html", error=str(e))

@app.route("/drivers", methods=["GET", "POST"])
def drivers():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        license_no = request.form.get("license_no", "").strip()
        phone = request.form.get("phone", "").strip()
        if not name or not license_no:
            flash("Driver name and license number are required.", "error")
        else:
            try:
                execute("INSERT INTO drivers (name, license_no, phone) VALUES (%s, %s, %s)",
                        (name, license_no, phone or None))
                flash("Driver added successfully.", "success")
                return redirect(url_for("drivers"))
            except Error as e:
                flash(f"Could not add driver. Check that the license number is unique. Details: {e}", "error")
    return render_template("drivers.html", drivers=query_all("SELECT * FROM drivers ORDER BY driver_id DESC"))

@app.route("/drivers/<int:driver_id>/edit", methods=["GET", "POST"])
def edit_driver(driver_id):
    rows = query_all("SELECT * FROM drivers WHERE driver_id=%s", (driver_id,))
    if not rows:
        flash("Driver not found.", "error")
        return redirect(url_for("drivers"))
    driver = rows[0]
    if request.method == "POST":
        try:
            execute("UPDATE drivers SET name=%s, license_no=%s, phone=%s WHERE driver_id=%s",
                    (request.form["name"].strip(), request.form["license_no"].strip(),
                     request.form.get("phone", "").strip() or None, driver_id))
            flash("Driver updated successfully.", "success")
            return redirect(url_for("drivers"))
        except Error as e:
            flash(f"Could not update driver: {e}", "error")
    return render_template("edit_driver.html", driver=driver)

@app.route("/drivers/<int:driver_id>/delete", methods=["POST"])
def delete_driver(driver_id):
    try:
        execute("DELETE FROM drivers WHERE driver_id=%s", (driver_id,))
        flash("Driver deleted. Drivers linked to existing vehicles cannot be deleted.", "success")
    except Error:
        flash("Cannot delete this driver because a vehicle is linked to it.", "error")
    return redirect(url_for("drivers"))

@app.route("/vehicles", methods=["GET", "POST"])
def vehicles():
    if request.method == "POST":
        reg = request.form.get("registration_no", "").strip().upper()
        vtype = request.form.get("vehicle_type", "").strip()
        driver_id = request.form.get("driver_id") or None
        if not reg or not vtype:
            flash("Registration number and vehicle type are required.", "error")
        else:
            try:
                execute("INSERT INTO vehicles (registration_no, vehicle_type, driver_id) VALUES (%s, %s, %s)",
                        (reg, vtype, driver_id))
                flash("Vehicle added successfully.", "success")
                return redirect(url_for("vehicles"))
            except Error as e:
                flash(f"Could not add vehicle. Registration numbers must be unique. Details: {e}", "error")
    return render_template("vehicles.html",
        vehicles=query_all("""SELECT v.*, d.name AS driver_name FROM vehicles v
                              LEFT JOIN drivers d ON d.driver_id=v.driver_id
                              ORDER BY v.vehicle_id DESC"""),
        drivers=query_all("SELECT driver_id, name, license_no FROM drivers ORDER BY name"))

@app.route("/vehicles/<int:vehicle_id>/edit", methods=["GET", "POST"])
def edit_vehicle(vehicle_id):
    rows = query_all("SELECT * FROM vehicles WHERE vehicle_id=%s", (vehicle_id,))
    if not rows:
        flash("Vehicle not found.", "error")
        return redirect(url_for("vehicles"))
    vehicle = rows[0]
    if request.method == "POST":
        try:
            execute("""UPDATE vehicles SET registration_no=%s, vehicle_type=%s, driver_id=%s
                       WHERE vehicle_id=%s""",
                    (request.form["registration_no"].strip().upper(),
                     request.form["vehicle_type"].strip(),
                     request.form.get("driver_id") or None, vehicle_id))
            flash("Vehicle updated successfully.", "success")
            return redirect(url_for("vehicles"))
        except Error as e:
            flash(f"Could not update vehicle: {e}", "error")
    return render_template("edit_vehicle.html", vehicle=vehicle,
                           drivers=query_all("SELECT driver_id, name, license_no FROM drivers ORDER BY name"))

@app.route("/vehicles/<int:vehicle_id>/delete", methods=["POST"])
def delete_vehicle(vehicle_id):
    try:
        execute("DELETE FROM vehicles WHERE vehicle_id=%s", (vehicle_id,))
        flash("Vehicle deleted successfully.", "success")
    except Error:
        flash("Cannot delete this vehicle because it has violation records.", "error")
    return redirect(url_for("vehicles"))

@app.route("/violations", methods=["GET", "POST"])
def violations():
    if request.method == "POST":
        vehicle_id = request.form.get("vehicle_id")
        violation_type_id = request.form.get("violation_type_id")
        violation_date = request.form.get("violation_date") or date.today().isoformat()
        location = request.form.get("location", "").strip()
        fine_amount = request.form.get("fine_amount", "0")
        status = request.form.get("status", "Unpaid")
        try:
            amount = float(fine_amount)
            if amount < 0:
                raise ValueError("Fine amount cannot be negative")
            execute("""INSERT INTO violation_records
                       (vehicle_id, violation_type_id, violation_date, location, fine_amount, status)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (vehicle_id, violation_type_id, violation_date, location or None, amount, status))
            flash("Violation record added successfully.", "success")
            return redirect(url_for("violations"))
        except (Error, ValueError) as e:
            flash(f"Could not add violation: {e}", "error")
    return render_template("violations.html",
        records=query_all("""SELECT vr.*, v.registration_no, vi.violation_type
                             FROM violation_records vr
                             JOIN vehicles v ON v.vehicle_id=vr.vehicle_id
                             JOIN violation_types vi ON vi.violation_type_id=vr.violation_type_id
                             ORDER BY vr.record_id DESC"""),
        vehicles=query_all("SELECT vehicle_id, registration_no FROM vehicles ORDER BY registration_no"),
        types=query_all("SELECT * FROM violation_types ORDER BY violation_type"))

@app.route("/violations/<int:record_id>/edit", methods=["GET", "POST"])
def edit_violation(record_id):
    rows = query_all("SELECT * FROM violation_records WHERE record_id=%s", (record_id,))
    if not rows:
        flash("Violation record not found.", "error")
        return redirect(url_for("violations"))
    record = rows[0]
    if request.method == "POST":
        try:
            amount = float(request.form["fine_amount"])
            if amount < 0:
                raise ValueError("Fine amount cannot be negative")
            execute("""UPDATE violation_records SET vehicle_id=%s, violation_type_id=%s,
                       violation_date=%s, location=%s, fine_amount=%s, status=%s
                       WHERE record_id=%s""",
                    (request.form["vehicle_id"], request.form["violation_type_id"],
                     request.form["violation_date"], request.form.get("location", "").strip() or None,
                     amount, request.form["status"], record_id))
            flash("Violation record updated successfully.", "success")
            return redirect(url_for("violations"))
        except (Error, ValueError) as e:
            flash(f"Could not update violation: {e}", "error")
    return render_template("edit_violation.html", record=record,
        vehicles=query_all("SELECT vehicle_id, registration_no FROM vehicles ORDER BY registration_no"),
        types=query_all("SELECT * FROM violation_types ORDER BY violation_type"))

@app.route("/violations/<int:record_id>/delete", methods=["POST"])
def delete_violation(record_id):
    execute("DELETE FROM violation_records WHERE record_id=%s", (record_id,))
    flash("Violation record deleted successfully.", "success")
    return redirect(url_for("violations"))

if __name__ == "__main__":
    app.run(debug=True)
