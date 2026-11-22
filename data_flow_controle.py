import os
import pickle
import threading
from contextlib import contextmanager
from datetime import date, datetime, time, timedelta
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

import mysql.connector
from mysql.connector import IntegrityError
from mysql.connector.pooling import MySQLConnectionPool


_PROJECT_ROOT = Path(__file__).resolve().parent
DATABASE_NAME = "attendance_system"
_connection_pool = None
_connection_pool_pid = None
_pool_lock = threading.Lock()
_authenticated_session = None


class DatabaseStartupError(RuntimeError):
    """Raised when MySQL configuration or schema initialization fails."""


class DuplicateTeacherError(ValueError):
    """Raised when a teacher ID already exists."""


class TeacherValidationError(ValueError):
    """Raised when edited teacher information is invalid."""


class TeacherNotFoundError(LookupError):
    """Raised when an operation references an unknown teacher."""


class InactiveTeacherError(ValueError):
    """Raised when an inactive teacher is used for new attendance."""


class DuplicateAttendanceError(ValueError):
    """Raised when attendance already exists for a teacher and date."""


def get_project_root():
    return _PROJECT_ROOT


def resolve_path(*parts):
    return str(_PROJECT_ROOT.joinpath(*parts))


def set_authenticated_session(session):
    global _authenticated_session
    if session is None:
        _authenticated_session = None
        return
    from admin_auth import AdminSession

    if not isinstance(session, AdminSession) or not session.is_authenticated():
        raise PermissionError("Administrator authentication is required.")
    _authenticated_session = session


def require_authenticated_session():
    from admin_auth import AdminSession

    if (
        not isinstance(_authenticated_session, AdminSession)
        or not _authenticated_session.is_authenticated()
    ):
        raise PermissionError("Administrator authentication is required.")


def normalize_teacher_status(value):
    text = str(value or "Active").strip().lower()
    if text in {
        "inactive", "in-active", "deactivated", "deactivate",
        "inactive teacher", "disabled",
    }:
        return "Inactive"
    return "Active"


def format_attendance_time(value):
    if value is None:
        return ""
    if isinstance(value, timedelta):
        total_seconds = int(value.total_seconds()) % (24 * 60 * 60)
        value = time(
            total_seconds // 3600,
            (total_seconds % 3600) // 60,
            total_seconds % 60,
        )
    return value.strftime("%I:%M %p")


def _mysql_config(include_database=True):
    user = os.environ.get("ATTENDANCE_DB_USER", "").strip()
    password = os.environ.get("ATTENDANCE_DB_PASSWORD", "")
    if not user or not password:
        raise DatabaseStartupError(
            "Set ATTENDANCE_DB_USER and ATTENDANCE_DB_PASSWORD before starting "
            "the attendance application."
        )
    try:
        port = int(os.environ.get("ATTENDANCE_DB_PORT", "3306"))
    except ValueError as exc:
        raise DatabaseStartupError(
            "ATTENDANCE_DB_PORT must be a valid TCP port."
        ) from exc
    config = {
        "host": os.environ.get("ATTENDANCE_DB_HOST", "127.0.0.1").strip(),
        "port": port,
        "user": user,
        "password": password,
        "connection_timeout": 5,
    }
    if include_database:
        config["database"] = DATABASE_NAME
    return config


def _get_connection_pool():
    global _connection_pool, _connection_pool_pid
    process_id = os.getpid()
    with _pool_lock:
        if _connection_pool is None or _connection_pool_pid != process_id:
            _connection_pool = MySQLConnectionPool(
                pool_name=f"attendance_pool_{process_id}",
                pool_size=5,
                pool_reset_session=True,
                **_mysql_config(),
            )
            _connection_pool_pid = process_id
    return _connection_pool


@contextmanager
def database_connection():
    connection = _get_connection_pool().get_connection()
    try:
        yield connection
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database():
    """Initialize the MySQL schema without importing or altering Excel files."""
    config = _mysql_config(include_database=False)
    connection = None
    try:
        try:
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()
            try:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{DATABASE_NAME}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            finally:
                cursor.close()
        except mysql.connector.Error:
            if connection is not None:
                connection.close()
                connection = None
            # Dedicated application users can use an existing database without
            # having the global CREATE DATABASE privilege.
            connection = mysql.connector.connect(**_mysql_config())
        finally:
            if connection is not None:
                connection.close()

        schema = (
            """
            CREATE TABLE IF NOT EXISTS teachers (
                teacher_pk BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
                name VARCHAR(150) NOT NULL,
                father_name VARCHAR(150) NOT NULL,
                teacher_id VARCHAR(64) NOT NULL,
                subject VARCHAR(150) NOT NULL,
                phone_number VARCHAR(40) NOT NULL,
                registration_date DATE NOT NULL,
                status ENUM('Active', 'Inactive') NOT NULL DEFAULT 'Active',
                photo_path VARCHAR(500) NOT NULL,
                encoding_path VARCHAR(500) NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (teacher_pk),
                UNIQUE KEY uq_teachers_teacher_id (teacher_id),
                KEY idx_teachers_status (status)
            ) ENGINE=InnoDB
            """,
            """
            CREATE TABLE IF NOT EXISTS attendance (
                attendance_pk BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
                teacher_pk BIGINT UNSIGNED NOT NULL,
                attendance_status VARCHAR(24) NOT NULL DEFAULT 'present',
                attendance_date DATE NOT NULL,
                attendance_time TIME NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (attendance_pk),
                UNIQUE KEY uq_attendance_teacher_date (teacher_pk, attendance_date),
                KEY idx_attendance_date (attendance_date),
                CONSTRAINT fk_attendance_teacher
                    FOREIGN KEY (teacher_pk) REFERENCES teachers (teacher_pk)
                    ON UPDATE CASCADE ON DELETE RESTRICT
            ) ENGINE=InnoDB
            """,
        )
        with database_connection() as pooled_connection:
            cursor = pooled_connection.cursor()
            try:
                for statement in schema:
                    cursor.execute(statement)
                cursor.execute(
                    "SELECT TABLE_NAME FROM information_schema.TABLES "
                    "WHERE TABLE_SCHEMA = %s AND TABLE_NAME IN (%s, %s)",
                    (DATABASE_NAME, "teachers", "attendance"),
                )
                tables = {row[0] for row in cursor.fetchall()}
                if tables != {"teachers", "attendance"}:
                    raise DatabaseStartupError(
                        "MySQL schema verification failed for the attendance database."
                    )

                required_columns = {
                    "teachers": {
                        "teacher_pk", "name", "father_name", "teacher_id", "subject",
                        "phone_number", "registration_date", "status", "photo_path",
                        "encoding_path",
                    },
                    "attendance": {
                        "attendance_pk", "teacher_pk", "attendance_status",
                        "attendance_date", "attendance_time",
                    },
                }
                for table, expected in required_columns.items():
                    cursor.execute(
                        "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
                        "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s",
                        (DATABASE_NAME, table),
                    )
                    columns = {row[0] for row in cursor.fetchall()}
                    if not expected.issubset(columns):
                        raise DatabaseStartupError(
                            f"MySQL schema verification failed for table {table}."
                        )
                pooled_connection.commit()
            finally:
                cursor.close()
    except DatabaseStartupError:
        raise
    except mysql.connector.Error as exc:
        raise DatabaseStartupError(
            "Could not initialize the local MySQL database. Confirm that the "
            "MySQL service is running, the credentials are correct, and the "
            "configured account has the required database privileges.\n"
            f"MySQL error: {exc}"
        ) from exc
    finally:
        if connection is not None:
            connection.close()


def get_teacher_by_id(teacher_id):
    require_authenticated_session()
    with database_connection() as connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT * FROM teachers WHERE teacher_id = %s",
                (str(teacher_id).strip(),),
            )
            return cursor.fetchone()
        finally:
            cursor.close()


def get_teacher_by_pk(teacher_pk):
    require_authenticated_session()
    with database_connection() as connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT * FROM teachers WHERE teacher_pk = %s",
                (teacher_pk,),
            )
            return cursor.fetchone()
        finally:
            cursor.close()


def get_teachers(status=None):
    require_authenticated_session()
    query = "SELECT * FROM teachers"
    parameters = ()
    if status is not None:
        query += " WHERE status = %s"
        parameters = (normalize_teacher_status(status),)
    query += " ORDER BY name, teacher_id"
    with database_connection() as connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(query, parameters)
            return cursor.fetchall()
        finally:
            cursor.close()


def get_active_teachers():
    return get_teachers("Active")


def get_inactive_teachers():
    return get_teachers("Inactive")


def register_teacher(teacher_data, photo_path, encoding_path):
    require_authenticated_session()
    values = (
        str(teacher_data["name"]).strip().upper(),
        str(teacher_data["father_name"]).strip().upper(),
        str(teacher_data["teacher_id"]).strip(),
        str(teacher_data["subject"]).strip().upper(),
        str(teacher_data["phone_number"]).strip(),
        date.today(),
        "Active",
        str(photo_path),
        str(encoding_path),
    )
    with database_connection() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO teachers "
                "(name, father_name, teacher_id, subject, phone_number, "
                "registration_date, status, photo_path, encoding_path) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                values,
            )
            connection.commit()
            return cursor.lastrowid
        except IntegrityError as exc:
            connection.rollback()
            if exc.errno == 1062:
                raise DuplicateTeacherError(
                    f"Teacher ID {values[2]} is already registered."
                ) from exc
            raise
        finally:
            cursor.close()


def update_teacher(teacher_id, **fields):
    require_authenticated_session()
    allowed_fields = {
        "name", "father_name", "subject", "phone_number",
        "photo_path", "encoding_path",
    }
    updates = [(key, value) for key, value in fields.items() if key in allowed_fields]
    if not updates:
        return False
    assignments = ", ".join(f"{key} = %s" for key, _value in updates)
    values = [value for _key, value in updates]
    values.append(str(teacher_id).strip())
    with database_connection() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                f"UPDATE teachers SET {assignments} WHERE teacher_id = %s",
                tuple(values),
            )
            if cursor.rowcount == 0:
                cursor.execute(
                    "SELECT 1 FROM teachers WHERE teacher_id = %s",
                    (str(teacher_id).strip(),),
                )
                if cursor.fetchone() is None:
                    raise TeacherNotFoundError(
                        f"Teacher ID {teacher_id} was not found."
                    )
            connection.commit()
            return True
        finally:
            cursor.close()


def validate_teacher_information(teacher_data):
    allowed_fields = {
        "name", "father_name", "teacher_id", "subject", "phone_number",
    }
    if set(teacher_data) != allowed_fields:
        raise TeacherValidationError("All editable teacher fields are required.")

    values = {key: str(teacher_data[key]).strip() for key in allowed_fields}
    for field, value in values.items():
        if not value:
            raise TeacherValidationError(
                f"{field.replace('_', ' ').title()} cannot be empty."
            )

    if not values["teacher_id"].isdigit():
        raise TeacherValidationError("Teacher ID must contain digits only.")
    if len(values["teacher_id"]) > 64:
        raise TeacherValidationError("Teacher ID cannot exceed 64 characters.")
    if not values["phone_number"].isdigit():
        raise TeacherValidationError("Phone number must contain digits only.")
    if len(values["phone_number"]) > 40:
        raise TeacherValidationError("Phone number cannot exceed 40 characters.")
    for field in ("name", "father_name", "subject"):
        if len(values[field]) > 150:
            raise TeacherValidationError(
                f"{field.replace('_', ' ').title()} cannot exceed 150 characters."
            )

    values["name"] = values["name"].upper()
    values["father_name"] = values["father_name"].upper()
    values["subject"] = values["subject"].upper()
    return values


def update_teacher_information(teacher_pk, teacher_data):
    require_authenticated_session()
    values = validate_teacher_information(teacher_data)
    with database_connection() as connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT teacher_pk FROM teachers "
                "WHERE teacher_pk = %s FOR UPDATE",
                (teacher_pk,),
            )
            if cursor.fetchone() is None:
                raise TeacherNotFoundError(
                    f"Teacher record {teacher_pk} was not found."
                )
            cursor.execute(
                "UPDATE teachers SET name = %s, father_name = %s, "
                "teacher_id = %s, subject = %s, phone_number = %s "
                "WHERE teacher_pk = %s",
                (
                    values["name"], values["father_name"], values["teacher_id"],
                    values["subject"], values["phone_number"], teacher_pk,
                ),
            )
            cursor.execute(
                "SELECT * FROM teachers WHERE teacher_pk = %s",
                (teacher_pk,),
            )
            teacher = cursor.fetchone()
            connection.commit()
            return teacher
        except IntegrityError as exc:
            connection.rollback()
            if exc.errno == 1062:
                raise DuplicateTeacherError(
                    f"Teacher ID {values['teacher_id']} is already registered."
                ) from exc
            raise
        finally:
            cursor.close()


def update_teacher_status(teacher_id, status):
    require_authenticated_session()
    with database_connection() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "UPDATE teachers SET status = %s WHERE teacher_id = %s",
                (normalize_teacher_status(status), str(teacher_id).strip()),
            )
            if cursor.rowcount == 0:
                cursor.execute(
                    "SELECT 1 FROM teachers WHERE teacher_id = %s",
                    (str(teacher_id).strip(),),
                )
                if cursor.fetchone() is None:
                    raise TeacherNotFoundError(
                        f"Teacher ID {teacher_id} was not found."
                    )
            connection.commit()
            return True
        finally:
            cursor.close()


def get_teacher_status(teacher_id):
    teacher = get_teacher_by_id(teacher_id)
    return teacher["status"] if teacher else None


def get_registration_date(teacher_id):
    teacher = get_teacher_by_id(teacher_id)
    return teacher["registration_date"] if teacher else None


def get_attendance_records(teacher_id, start_date=None, end_date=None):
    require_authenticated_session()
    query = (
        "SELECT t.name, t.teacher_id, a.attendance_status, "
        "a.attendance_date, a.attendance_time "
        "FROM attendance AS a "
        "JOIN teachers AS t ON t.teacher_pk = a.teacher_pk "
        "WHERE t.teacher_id = %s"
    )
    parameters = [str(teacher_id).strip()]
    if start_date is not None:
        query += " AND a.attendance_date >= %s"
        parameters.append(start_date)
    if end_date is not None:
        query += " AND a.attendance_date <= %s"
        parameters.append(end_date)
    query += " ORDER BY a.attendance_date, a.attendance_time"
    with database_connection() as connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(query, tuple(parameters))
            return cursor.fetchall()
        finally:
            cursor.close()


def get_today_attendance():
    require_authenticated_session()
    with database_connection() as connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT t.name, t.teacher_id, a.attendance_status, "
                "a.attendance_date, a.attendance_time "
                "FROM attendance AS a "
                "JOIN teachers AS t ON t.teacher_pk = a.teacher_pk "
                "WHERE a.attendance_date = %s ORDER BY a.attendance_time",
                (date.today(),),
            )
            return cursor.fetchall()
        finally:
            cursor.close()


def mark_attendance(teacher_id, attendance_date=None, attendance_time=None):
    require_authenticated_session()
    attendance_date = attendance_date or date.today()
    attendance_time = attendance_time or datetime.now().time().replace(microsecond=0)
    if isinstance(attendance_date, str):
        attendance_date = datetime.strptime(attendance_date, "%m/%d/%Y").date()
    if isinstance(attendance_time, str):
        attendance_time = datetime.strptime(attendance_time, "%I:%M").time()
    with database_connection() as connection:
        cursor = connection.cursor()
        require_authenticated_session()
        try:
            cursor.execute(
                "SELECT teacher_pk, status FROM teachers "
                "WHERE teacher_id = %s FOR UPDATE",
                (str(teacher_id).strip(),),
            )
            teacher = cursor.fetchone()
            if teacher is None:
                raise TeacherNotFoundError(f"Teacher ID {teacher_id} was not found.")
            if teacher[1] != "Active":
                raise InactiveTeacherError(
                    f"Inactive teacher ID {teacher_id} cannot be marked present."
                )
            cursor.execute(
                "INSERT INTO attendance "
                "(teacher_pk, attendance_status, attendance_date, attendance_time) "
                "VALUES (%s, %s, %s, %s)",
                (teacher[0], "present", attendance_date, attendance_time),
            )
            connection.commit()
            return True
        except IntegrityError as exc:
            connection.rollback()
            if exc.errno == 1062:
                raise DuplicateAttendanceError(
                    f"Attendance for teacher ID {teacher_id} is already recorded "
                    f"for {attendance_date}."
                ) from exc
            raise
        finally:
            cursor.close()


class Data_Manager:
    """Application-facing registration and attendance operations."""

    def __init__(self):
        self.name = None
        self.father_name = None
        self.id_number = None
        self.subject = None
        self.phone_number = None
        self.present_name = None
        self.present_idnumber = None
        self.date = None
        self.time = None

    def registration_checking(self):
        teacher = get_teacher_by_id(self.present_idnumber)
        if teacher is None or teacher["status"] != "Active":
            return False
        if teacher["name"].strip().upper() != str(self.present_name).strip().upper():
            return False
        return str(teacher["teacher_id"])

    def attendance_data(self):
        return mark_attendance(self.present_idnumber, self.date, self.time)


CAMERA_CONFIG_FILE = resolve_path("pathsfolder", "camera_config.data")
EXCLUDED_DAYS_FILE = resolve_path("pathsfolder", "excluded_days.data")
REQUIRED_DIRECTORIES = ("pathsfolder",)
REQUIRED_BUTTON_IMAGES = (
    "Search button.png", "Search button1.png", "Search button2.png", "Teacher.png",
)


def save_camera_config(attendance_camera, registration_camera):
    require_authenticated_session()
    os.makedirs(os.path.dirname(CAMERA_CONFIG_FILE), exist_ok=True)
    with open(CAMERA_CONFIG_FILE, "wb") as file:
        pickle.dump(
            {
                "attendance_camera": attendance_camera,
                "registration_camera": registration_camera,
            },
            file,
        )
    return True


def load_camera_config():
    require_authenticated_session()
    if not os.path.exists(CAMERA_CONFIG_FILE):
        return "0", "0"
    try:
        with open(CAMERA_CONFIG_FILE, "rb") as file:
            config = pickle.load(file)
        attendance = config.get("attendance_camera", "0")
        registration = config.get("registration_camera", "0")
        return str(attendance or "0"), str(registration or "0")
    except (OSError, EOFError, pickle.UnpicklingError, AttributeError):
        return "0", "0"


def load_excluded_days():
    require_authenticated_session()
    try:
        with open(EXCLUDED_DAYS_FILE, "rb") as file:
            days = pickle.load(file)
        if isinstance(days, (list, tuple, set)):
            return {int(day_value) for day_value in days if 0 <= int(day_value) <= 6}
    except (OSError, EOFError, pickle.UnpicklingError, TypeError, ValueError):
        pass
    return set()


def save_excluded_days(days):
    require_authenticated_session()
    os.makedirs(os.path.dirname(EXCLUDED_DAYS_FILE), exist_ok=True)
    with open(EXCLUDED_DAYS_FILE, "wb") as file:
        pickle.dump(sorted({int(day_value) for day_value in days}), file)


def _initialize_settings():
    os.makedirs(resolve_path("pathsfolder"), exist_ok=True)
    defaults = {
        "camera_config.data": {"attendance_camera": "0", "registration_camera": "0"},
        "excluded_days.data": [],
    }
    errors = []
    for file_name, default in defaults.items():
        file_path = resolve_path("pathsfolder", file_name)
        if os.path.exists(file_path):
            continue
        try:
            with open(file_path, "wb") as file:
                pickle.dump(default, file)
        except OSError as exc:
            errors.append(f"Could not initialize {file_name}: {exc}")
    return errors


def check_button_assets():
    return [
        image for image in REQUIRED_BUTTON_IMAGES
        if not os.path.isfile(resolve_path("Buttons", image))
    ]


def _show_button_warning(missing):
    messagebox.showwarning(
        "Missing Button Assets",
        "The following button images are missing:\n\n"
        + "\n".join(f"  • {name}" for name in missing)
        + "\n\nText-only fallbacks will be used.",
    )


def initialize_project(show_warnings=True):
    """Initialize local folders/settings and require a working MySQL schema."""
    for directory in REQUIRED_DIRECTORIES:
        try:
            os.makedirs(resolve_path(directory), exist_ok=True)
        except OSError as exc:
            raise DatabaseStartupError(
                f"Could not initialize required project directory {directory}: {exc}"
            ) from exc
    initialize_database()
    settings_errors = _initialize_settings()
    if settings_errors:
        raise OSError("\n".join(settings_errors))
    missing = check_button_assets()
    if show_warnings and missing:
        _show_button_warning(missing)
    return {"missing_buttons": missing, "database": DATABASE_NAME}


def safe_pickle_load(file_path, default=None):
    try:
        with open(file_path, "rb") as file:
            return pickle.load(file)
    except (FileNotFoundError, pickle.UnpicklingError, EOFError, OSError):
        return default
