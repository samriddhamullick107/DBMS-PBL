# Smart Traffic Violation & Road Safety Management System

A basic DBMS PBL web application using Flask (Python), HTML/CSS/JavaScript, and MySQL.

## Features
- Dashboard summary
- Driver CRUD: create, read, update, delete
- Vehicle CRUD: create, read, update, delete
- Violation record CRUD: create, read, update, delete
- MySQL primary keys, foreign keys, unique constraints, and joins

## Requirements
- Python 3.10+
- MySQL Server (or XAMPP MySQL/MariaDB)
- VS Code (recommended)

## Setup

### 1. Create the database
1. Start MySQL Server.
2. Open MySQL Workbench, phpMyAdmin, or a MySQL terminal.
3. Run the full contents of `database/schema.sql`.
   - In Workbench: open the file, connect to your server, then click the lightning-bolt execute button.
   - In phpMyAdmin: select the Import tab and import `database/schema.sql`.

### 2. Configure the connection
The defaults are:
- host: `localhost`
- port: `3306`
- user: `root`
- password: empty
- database: `smart_traffic_db`

If your MySQL password is not empty, set environment variables before running the app.

**Windows Command Prompt:**
```bat
set DB_HOST=localhost
set DB_PORT=3306
set DB_USER=root
set DB_PASSWORD=your_mysql_password
set DB_NAME=smart_traffic_db
```

**PowerShell:**
```powershell
$env:DB_HOST="localhost"
$env:DB_PORT="3306"
$env:DB_USER="root"
$env:DB_PASSWORD="your_mysql_password"
$env:DB_NAME="smart_traffic_db"
```

### 3. Install dependencies
Open a terminal in this project folder:
```bash
python -m venv venv
```

Windows:
```bat
venv\Scripts\activate
```

macOS/Linux:
```bash
source venv/bin/activate
```

Then:
```bash
python -m pip install -r requirements.txt
```

### 4. Run the website
```bash
python app.py
```
Open http://127.0.0.1:5000 in your browser.

## Suggested demo order
1. Open Dashboard.
2. Add a driver in Drivers.
3. Add a vehicle and link it to that driver.
4. Add a violation record for the vehicle.
5. Edit a record, then delete a test record.
6. Show the dashboard counts and explain primary/foreign keys.

## Important notes
- This is an academic demonstration project, not an official traffic enforcement service.
- There is no real camera detection or online payment gateway in this basic version.
- Do not use real driver personal data in a public demo.
- Before deployment, disable Flask debug mode, use a strong secret key, add authentication/authorization and CSRF protection, and use a dedicated database account rather than MySQL root.
