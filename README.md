# Automatic Attendance System Using Face Recognition

<p align="center">
  <strong>An Intelligent Face Recognition-Based Attendance Management System for Teachers and Educational Institutions</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.x-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/MySQL-Database-4479A1?logo=mysql&logoColor=white" alt="MySQL">
  <img src="https://img.shields.io/badge/OpenCV-Computer%20Vision-green?logo=opencv" alt="OpenCV">
  <img src="https://img.shields.io/badge/Tkinter-Desktop%20GUI-orange" alt="Tkinter">
  <img src="https://img.shields.io/badge/Platform-Windows-blue?logo=windows" alt="Windows">
</p>

<p align="center">
  <a href="https://github.com/gitengineer4030/Automatic-Attendance-System-Using-Face-Recognition">Repository</a> •
  <a href="#features">Features</a> •
  <a href="#installation-and-setup">Installation</a> •
  <a href="#database-architecture">Database</a> •
  <a href="#usage-guide">Usage</a>
</p>

---

## 1. Project Overview

**Automatic Attendance System Using Face Recognition** is a Python-based desktop application designed to automate teacher attendance management in schools, colleges, and other educational institutions.

The system uses computer vision and facial recognition technology to identify registered teachers through a live camera feed and automatically record their attendance in a MySQL database.

Instead of relying on traditional manual attendance registers, the application provides an integrated solution for teacher registration, facial recognition, attendance monitoring, teacher account management, and historical attendance reporting.

The application also includes a secure administrator authentication system to ensure that only authorized users can access attendance records and management functionality.

The system is designed as a Windows desktop application with a graphical user interface built using Python Tkinter.

## 2. Objectives

The primary objectives of this project are:

- Automate the daily attendance process using facial recognition.
- Reduce manual attendance-taking efforts.
- Minimize duplicate attendance entries.
- Maintain organized teacher information.
- Store attendance records in a centralized MySQL database.
- Provide historical attendance tracking and reporting.
- Improve the security of attendance management through administrator authentication.
- Support different camera sources for attendance and registration.
- Provide a user-friendly desktop interface for administrators.

## 3. Features

### 3.1. Face Recognition-Based Attendance

- Detect faces through a live camera feed.
- Recognize registered teachers using facial encodings.
- Compare detected faces against registered face data.
- Identify unknown individuals.
- Automatically record recognized teachers' attendance.
- Record attendance dates and times.
- Prevent duplicate attendance entries for the same teacher on the same date.
- Display the current day's attendance records in the application.

### 3.2. Teacher Registration

The application provides a dedicated teacher registration module.

Administrators can register teachers using the following information:

- Teacher Name
- Father's Name
- Teacher ID
- Subject
- Phone Number
- Registration Date

Registration workflow:

1. Enter the teacher's information.
2. Validate the entered information.
3. Check for duplicate teacher IDs.
4. Open the registration camera.
5. Capture the teacher's photograph.
6. Generate facial encoding data.
7. Save teacher information and associated file paths in MySQL.
8. Make the registered teacher available for face recognition.

### 3.3. Teacher Status Management

The application provides teacher account management through its Teacher Status Management interface.

Features include:

- View registered teachers.
- Search teachers by name or ID.
- Filter all teachers.
- Filter active teachers.
- Filter deactivated teachers.
- View teacher information.
- Edit existing teacher information.
- Activate and deactivate teacher accounts.

Deactivation is designed to preserve historical attendance records instead of permanently deleting teacher information.

Inactive teachers are excluded from new attendance recognition.

### 3.4. Administrator Authentication and Security

The application includes a dedicated administrator authentication system.

Security features include:

- First-time administrator account setup.
- Administrator login.
- Username validation.
- Secure password hashing using the `scrypt` algorithm.
- Password confirmation during account creation.
- Minimum password length of 12 characters.
- Failed login attempt tracking.
- Temporary account lockout after repeated unsuccessful login attempts.
- Administrator account management.
- Username and password updates.
- Protected application windows.
- Session-based authentication.
- Secure logout functionality.

Passwords are stored as cryptographic hashes rather than readable text.

After logout, the authenticated session is invalidated and protected application functionality cannot be accessed through that session.

### 3.5. MySQL Database Management

The application uses MySQL as its primary database instead of Excel workbooks for active teacher and attendance data.

Database features include:

- Automatic database initialization.
- Automatic creation of required database tables.
- MySQL connection pooling.
- Structured teacher records.
- Structured attendance records.
- Unique teacher ID constraints.
- Duplicate attendance prevention.
- Foreign key relationships.
- Database schema verification.
- Database error handling.

The application uses the database named:

`attendance_system`

### 3.6. Camera Configuration

The application supports independent camera configuration for two operations:

**Attendance Camera**
- Select a local camera.
- Configure a camera index.
- Configure a network camera stream URL.
- Detect available local cameras.
- Test the camera connection.
- Preview the camera feed.

**Registration Camera**
- Configure a separate local camera.
- Configure a network camera stream URL.
- Detect available cameras.
- Test the selected camera.
- Preview the camera feed.

Both camera configurations can be saved independently.

### 3.7. Teacher Attendance Record

The application includes a dedicated Teacher Attendance Record interface for examining historical attendance information.

Features include:

- Search teachers by name or ID.
- Select individual teachers.
- View teacher profile information.
- View registration information.
- Select attendance date ranges.
- Select reporting years.
- View daily attendance details.
- View present and absent records.
- Calculate attendance summaries.
- View total presents and absents.
- View monthly-wise attendance summaries.
- Calculate attendance percentages.
- Exclude selected days of the week from attendance calculations.
- View historical attendance information.
- Refresh attendance information.
- Print attendance reports.
- Print full attendance reports.
- Export attendance reports to CSV.
- Export attendance reports to Excel.

The historical attendance interface retrieves recorded attendance events from MySQL and calculates reporting information using the teacher's registration date and selected reporting period.

### 3.8. Application Interface

The application provides a desktop graphical interface with:

- Main attendance dashboard.
- Live camera functionality.
- Today's attendance table.
- Teacher registration interface.
- Teacher status management interface.
- Teacher attendance history interface.
- Administrator account management.
- Camera configuration.
- Login and first-time setup screens.

The interface uses Python Tkinter and Pillow for graphical interface functionality.

---

## 4. Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| OpenCV | Camera handling and computer vision |
| Face Recognition | Facial detection and recognition |
| dlib | Facial recognition engine dependency |
| NumPy | Numerical operations and facial encodings |
| MySQL | Database management |
| MySQL Connector/Python | Python-to-MySQL connectivity |
| Tkinter | Desktop graphical user interface |
| Pillow | Image processing and GUI image rendering |
| OpenPyXL | Excel report generation |
| Git | Version control |
| GitHub | Source code hosting |

## 5. System Architecture

The application follows a modular Python desktop architecture.

### Main Application Components

**1. User Interface Layer**

Responsible for displaying application windows, forms, buttons, tables, camera previews, and administrative controls.

**2. Face Recognition Layer**

Responsible for camera frame processing, face detection, facial encoding comparison, and identification of registered teachers.

**3. Registration Layer**

Responsible for collecting teacher information, capturing photographs, generating facial encodings, and registering teachers.

**4. Database Management Layer**

Responsible for MySQL connectivity, database initialization, teacher records, attendance records, and database operations.

**5. Authentication Layer**

Responsible for administrator setup, login, password security, session management, and access protection.

**6. Attendance History Layer**

Responsible for retrieving historical attendance records, calculating summaries, filtering records, and generating reports.

## 6. Database Architecture

The application automatically initializes its MySQL database and required application tables.

**Database name:**

`attendance_system`

### Main Database Tables

#### 6.1. teachers

Stores registered teacher information.

| Column | Description |
|---|---|
| teacher_pk | Internal primary key |
| name | Teacher name |
| father_name | Father's name |
| teacher_id | Unique teacher ID |
| subject | Teaching subject |
| phone_number | Contact number |
| registration_date | Registration date |
| status | Active or Inactive |
| photo_path | Teacher photograph path |
| encoding_path | Facial encoding path |
| created_at | Record creation timestamp |

#### 6.2. attendance

Stores teacher attendance events.

| Column | Description |
|---|---|
| attendance_pk | Attendance primary key |
| teacher_pk | Related teacher record |
| attendance_status | Attendance status |
| attendance_date | Attendance date |
| attendance_time | Attendance time |
| created_at | Record creation timestamp |

The database enforces a unique constraint on the combination of teacher and attendance date to prevent duplicate daily attendance records.

#### 6.3. admin_users

Stores administrator account information.

The administrator authentication module manages this table.

Its main fields include:

- admin_id
- username
- password_hash
- created_at
- status
- failed_attempts
- lockout_until

### Database Relationships

- Each teacher has a unique internal database identifier.
- Attendance records reference teachers through their internal IDs.
- Teacher deletion is restricted when related attendance records exist.
- Teacher status changes do not require deleting historical attendance information.

### Database Initialization

The application initializes the required MySQL schema during startup.

The application does not automatically import old Excel attendance records into the new MySQL database.

---

## 7. Project Directory Structure

The current repository contains the following project files:

```text
Automatic-Attendance-System-Using-Face-Recognition/
│
├── Buttons/
│   ├── Search button.png
│   └── Teacher.png
│
├── admin_auth.py
│
├── data_flow_controle.py
│
├── history_interface.py
│
├── interface_main.py
│
├── main.py
│
├── registration_control.py
│
├── unregister_control.py
│
├── .gitignore
│
└── README.md
```

### File Descriptions

| File | Responsibility |
|---|---|
| `main.py` | Camera frame capture, face recognition utilities, image processing, and camera-related functionality |
| `interface_main.py` | Main application interface, attendance dashboard, camera settings, and application entry point |
| `data_flow_controle.py` | MySQL database management, data operations, camera configuration, and application data handling |
| `admin_auth.py` | Administrator authentication, first-time setup, password security, and session management |
| `registration_control.py` | Teacher registration, photograph capture, and facial encoding generation |
| `unregister_control.py` | Teacher status management, teacher information editing, activation, and deactivation |
| `history_interface.py` | Historical attendance records, attendance summaries, filtering, and report generation |
| `Buttons/` | Application button image assets |
| `.gitignore` | Excludes unnecessary files from Git version control |

---

## 8. System Requirements

Before installing the application, make sure your computer meets the following requirements.

### Hardware Requirements

- Windows desktop or laptop.
- Webcam or compatible network camera.
- Sufficient RAM to run Python, MySQL, and computer vision operations.
- Available disk space for the application, database, teacher photographs, and facial encodings.

### Software Requirements

- Windows 10 or compatible Windows operating system.
- Python 3 with compatibility for the project's face-recognition dependencies.
- MySQL Server.
- Python package manager (pip).
- Compatible camera drivers.

**Important:** The repository does not currently include a pinned Python version or a `requirements.txt` file. Use a Python version supported by the installed `face-recognition` and `dlib` packages.

---

## 9. Installation and Setup

Follow these instructions to install and run the application on Windows.

### Step 1: Clone the Repository

Open Command Prompt or PowerShell and execute:

```bash
git clone https://github.com/gitengineer4030/Automatic-Attendance-System-Using-Face-Recognition.git
```

### Step 2: Open the Project Directory

```bash
cd Automatic-Attendance-System-Using-Face-Recognition
```

### Step 3: Create a Virtual Environment

```bash
python -m venv .venv
```

### Step 4: Activate the Virtual Environment

```bash
.venv\Scripts\activate
```

### Step 5: Upgrade pip

```bash
python -m pip install --upgrade pip
```

### Step 6: Install Required Python Packages

Install the project's Python dependencies:

```bash
pip install numpy
pip install opencv-python
pip install face-recognition
pip install mysql-connector-python
pip install Pillow
pip install openpyxl
```

**Note about face recognition on Windows:**

The `face-recognition` package depends on `dlib`. Depending on your Python version and Windows environment, installing `dlib` may require compatible prebuilt binaries or a local C++ build environment.

Tkinter is included with standard Windows Python installations that include the Tcl/Tk components.

### Step 7: Install and Configure MySQL Server

Install MySQL Server and make sure its service is running.

The application uses the following default connection settings:

| Setting | Default |
|---|---|
| Host | 127.0.0.1 |
| Port | 3306 |
| Database | attendance_system |

The application requests the MySQL username and password through its database connection screen.

The configured MySQL account must have sufficient privileges to create and manage the application database and tables. Alternatively, an administrator can create the database in advance and grant the application account the necessary privileges.

### Optional: Create the Database Manually

If you want to create the database before launching the application, execute:

```sql
CREATE DATABASE attendance_system
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

If using a dedicated MySQL account, grant it the necessary permissions on this database.

For example:

```sql
CREATE USER 'attendance_app'@'localhost'
IDENTIFIED BY 'ReplaceWithAStrongPassword';

GRANT ALL PRIVILEGES ON attendance_system.*
TO 'attendance_app'@'localhost';
```

Use your own secure database credentials. Do not commit passwords to GitHub.

### Step 8: Run the Application

Execute:

```bash
python interface_main.py
```

The application will open its administrator authentication and initial setup workflow.

---

## 10. First-Time Application Setup

When the application is launched for the first time:

1. The application checks whether MySQL connection details are available.
2. If necessary, it displays the database connection configuration screen.
3. Enter the MySQL host, port, username, and password.
4. Connect to the MySQL database.
5. The application initializes the database and required tables.
6. If no administrator exists, the first-time administrator setup screen appears.
7. Create your administrator username and password.
8. The application stores the password as a secure cryptographic hash.
9. The administrator can subsequently log in using the created credentials.

Database connection details are protected using Windows Data Protection API (DPAPI) when saved by the application.

After the first administrator has been created, the first-time setup workflow is no longer available while that administrator account exists.

---

## 11. Usage Guide

### Step 1: Administrator Login

Launch the application and authenticate using your administrator credentials.

### Step 2: Configure Cameras

Open:

`Options → Camera Settings`

Configure the attendance and registration cameras independently.

You can select local camera indexes or network camera stream URLs.

Test the selected camera before saving the configuration.

### Step 3: Register Teachers

Open the teacher registration interface.

Enter all required teacher information and proceed to the camera interface.

Capture a photograph and complete the registration process.

The application generates facial encoding data and stores the teacher's information in MySQL.

### Step 4: Start Attendance

Return to the main attendance dashboard.

Click:

`Start Attendance`

The system starts processing the configured attendance camera feed.

Recognized active teachers are recorded in the database.

### Step 5: Monitor Attendance

The main dashboard displays today's attendance information.

Click:

`Stop Attendance`

when you want to stop the attendance process.

### Step 6: Manage Teachers

Open the teacher status management interface.

Search for teachers, view their information, edit their details, or change their account status.

### Step 7: View Attendance History

Open:

`Teachers History`

Select a teacher and configure the required reporting period.

Review daily attendance details, attendance summaries, and monthly-wise reports.

You can also print reports or export them to CSV and Excel.

### Step 8: Logout

Use the Logout option from the application menu to end the administrator session.

---

## 12. Attendance Data Management

The system stores actual attendance events in MySQL.

Attendance information includes:

- Teacher identification.
- Attendance status.
- Attendance date.
- Attendance time.

The historical attendance interface uses registration dates and attendance records to generate reporting information.

It also provides controls for excluding selected weekdays from attendance calculations.

Historical attendance data remains associated with the teacher even after the teacher's account is deactivated.

---

## 13. Security Considerations

Security is an important part of the application.

The system implements several security mechanisms:

- Administrator authentication.
- Secure password hashing with `scrypt`.
- Password length validation.
- Login failure tracking and temporary lockout.
- Protected application sessions.
- Logout-based session invalidation.
- MySQL access control.
- Windows DPAPI protection for saved database credentials.
- Database constraints to preserve data integrity.

**Security recommendations:**

- Use a strong MySQL password.
- Use a strong administrator password.
- Restrict access to the computer running the application.
- Protect the MySQL database from unauthorized access.
- Do not upload real teacher photographs, facial encodings, passwords, or private database information to a public repository.

---

## 14. Troubleshooting

### MySQL Connection Failed

Possible causes:

- MySQL Server is not running.
- Incorrect database host or port.
- Incorrect username or password.
- Insufficient database privileges.

**Solution:** Verify the MySQL service and connection settings, and ensure the configured account has the required privileges.

### Camera Not Detected

Possible causes:

- Camera is disconnected.
- Camera drivers are missing.
- Another application is using the camera.
- Incorrect camera index or network URL.

**Solution:** Open Camera Settings, detect available cameras, and test the selected source.

### Face Recognition Dependency Installation Failed

The `face-recognition` package depends on `dlib`, which can be difficult to install on some Windows/Python combinations.

**Solution:** Verify Python compatibility and install the required compatible `dlib` binary or build dependencies.

### Administrator Login Failed

Possible causes:

- Incorrect username.
- Incorrect password.
- Administrator account temporarily locked.

**Solution:** Verify the credentials and wait for any active temporary lockout to expire.

### Database Initialization Failed

Possible causes:

- MySQL service is unavailable.
- The database account lacks the required privileges.
- The database schema could not be initialized.

**Solution:** Verify the MySQL connection and ensure the account has sufficient permissions to create or access `attendance_system` and its tables.

---

## 15. Privacy and Responsible Usage

This application processes facial photographs and facial recognition data.

When deploying the system in an educational institution:

- Obtain appropriate authorization for collecting and processing facial data.
- Inform teachers about the attendance monitoring system.
- Restrict access to registered teacher information.
- Protect facial photographs and encoding files.
- Follow applicable privacy and data protection requirements.
- Use the application only for legitimate attendance management purposes.

---

## 16. Future Enhancements

Potential areas for future development include:

- Advanced attendance analytics.
- Additional reporting capabilities.
- Enhanced camera management.
- Improved deployment and installation automation.
- More comprehensive application testing.
- Additional administrative monitoring features.

These are possible future improvements and are not claims about currently implemented functionality.

---

## 17. Limitations and Deployment Notes

- The application is designed as a Windows desktop application.
- MySQL Server must be available for database operations.
- A compatible camera is required for live face recognition.
- Facial recognition performance depends on camera quality, lighting, face visibility, and environmental conditions.
- The repository does not currently contain a pinned dependency file.
- Existing legacy Excel records are not automatically imported into the new MySQL database.
- Screenshots and demonstration videos are not currently included in the repository.

---

## 18. Repository

**GitHub Repository:**

https://github.com/gitengineer4030/Automatic-Attendance-System-Using-Face-Recognition

**Clone URL:**

```bash
git clone https://github.com/gitengineer4030/Automatic-Attendance-System-Using-Face-Recognition.git
```

---

## 19. Author

**GitHub:** [@gitengineer4030](https://github.com/gitengineer4030)

**Project:** Automatic Attendance System Using Face Recognition

---

## 20. License

No license file is currently included in this repository.

Please contact the repository owner regarding permission for redistribution, modification, or commercial use.

---

<p align="center">
  <strong>Automatic Attendance System Using Face Recognition</strong>
  <br>
  Developed with Python, OpenCV, Face Recognition, and MySQL.
  <br><br>
  <a href="https://github.com/gitengineer4030/Automatic-Attendance-System-Using-Face-Recognition">View Project on GitHub</a>
</p>
