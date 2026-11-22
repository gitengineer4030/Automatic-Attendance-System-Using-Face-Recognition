import base64
import ctypes
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import tempfile
import tkinter as tk
from datetime import datetime, timedelta
from ctypes import wintypes
from pathlib import Path
from tkinter import messagebox

import mysql.connector
from mysql.connector import IntegrityError

import data_flow_controle


_USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{3,64}$")
_SCRYPT_N = 1 << 15
_SCRYPT_R = 8
_SCRYPT_P = 1
_SCRYPT_MAXMEM = 64 * 1024 * 1024
_MAX_FAILED_ATTEMPTS = 5
_BASE_LOCKOUT_SECONDS = 30
_MAX_LOCKOUT_SECONDS = 15 * 60
_SESSION_TOKEN = object()


class AuthenticationError(ValueError):
    """Raised when authentication or administrator setup is rejected."""


class DatabaseCredentialsStorageError(RuntimeError):
    """Raised when saved MySQL connection details cannot be protected or read."""


_DATABASE_CREDENTIALS_DIRECTORY = "Automatic Attendance System"
_DATABASE_CREDENTIALS_FILE = "database-credentials.bin"


class _DataBlob(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_ubyte)),
    ]


def _dpapi_transform(data, protect):
    if os.name != "nt":
        raise DatabaseCredentialsStorageError(
            "Persistent database credentials are supported only on Windows."
        )

    try:
        crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    except OSError as exc:
        raise DatabaseCredentialsStorageError(
            f"Windows credential protection is unavailable: {exc}"
        ) from exc
    transform = (
        crypt32.CryptProtectData if protect else crypt32.CryptUnprotectData
    )
    transform.argtypes = [
        ctypes.POINTER(_DataBlob),
        wintypes.LPCWSTR if protect else ctypes.POINTER(wintypes.LPWSTR),
        ctypes.POINTER(_DataBlob),
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(_DataBlob),
    ]
    transform.restype = wintypes.BOOL
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p

    input_buffer = ctypes.create_string_buffer(data)
    input_blob = _DataBlob(
        len(data), ctypes.cast(input_buffer, ctypes.POINTER(ctypes.c_ubyte))
    )
    output_blob = _DataBlob()
    description = wintypes.LPWSTR()
    description_pointer = (
        "Attendance database credentials"
        if protect
        else ctypes.byref(description)
    )
    if not transform(
        ctypes.byref(input_blob),
        description_pointer,
        None,
        None,
        None,
        0x1 if protect else 0,
        ctypes.byref(output_blob),
    ):
        raise DatabaseCredentialsStorageError(
            f"Windows could not {'protect' if protect else 'read'} the saved "
            f"database credentials: {ctypes.WinError(ctypes.get_last_error())}"
        )
    try:
        return ctypes.string_at(output_blob.pbData, output_blob.cbData)
    finally:
        kernel32.LocalFree(ctypes.cast(output_blob.pbData, ctypes.c_void_p))
        if description:
            kernel32.LocalFree(ctypes.cast(description, ctypes.c_void_p))


def _database_credentials_path():
    local_app_data = os.environ.get("LOCALAPPDATA", "").strip()
    if not local_app_data:
        raise DatabaseCredentialsStorageError(
            "Windows did not provide a Local AppData folder for saved "
            "database credentials."
        )
    return (
        Path(local_app_data)
        / _DATABASE_CREDENTIALS_DIRECTORY
        / _DATABASE_CREDENTIALS_FILE
    )


def _save_database_credentials(credentials):
    path = _database_credentials_path()
    contents = json.dumps(credentials, separators=(",", ":")).encode("utf-8")
    protected_contents = _dpapi_transform(contents, protect=True)
    temporary_path = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            dir=path.parent, prefix=f"{path.name}.", suffix=".tmp", delete=False
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(protected_contents)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, path)
    except OSError as exc:
        cleanup_error = None
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError as cleanup_exc:
                cleanup_error = cleanup_exc
        message = f"Could not save encrypted database credentials: {exc}"
        if cleanup_error is not None:
            message += f" Temporary file cleanup also failed: {cleanup_error}"
        raise DatabaseCredentialsStorageError(message) from exc


def _load_database_credentials():
    path = _database_credentials_path()
    try:
        protected_contents = path.read_bytes()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise DatabaseCredentialsStorageError(
            f"Could not read saved database credentials: {exc}"
        ) from exc

    try:
        credentials = json.loads(
            _dpapi_transform(protected_contents, protect=False).decode("utf-8")
        )
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError) as exc:
        raise DatabaseCredentialsStorageError(
            "Saved database credentials are invalid or cannot be decrypted. "
            "Enter the MySQL connection details again."
        ) from exc
    required = ("host", "port", "user", "password")
    if not isinstance(credentials, dict) or any(
        not isinstance(credentials.get(key), str) or not credentials[key]
        for key in required
    ):
        raise DatabaseCredentialsStorageError(
            "Saved database credentials are incomplete. Enter the MySQL "
            "connection details again."
        )
    return credentials


class AdminSession:
    """In-memory authentication state tied to one active administrator."""

    def __init__(self, admin_id, username, token=None):
        if token is not _SESSION_TOKEN:
            raise PermissionError("Administrator sessions can only be created by login.")
        self.admin_id = admin_id
        self.username = username
        self._active = True

    def is_authenticated(self):
        return self._active

    def invalidate(self):
        self._active = False


def require_authenticated_parent(parent):
    session = getattr(parent, "auth_session", None)
    if not isinstance(session, AdminSession) or not session.is_authenticated():
        raise PermissionError("Administrator authentication is required.")


def _normalize_username(username):
    username = str(username or "").strip()
    if not _USERNAME_PATTERN.fullmatch(username):
        raise AuthenticationError(
            "Username must be 3–64 characters using letters, numbers, '.', '_' or '-'."
        )
    return username.lower()


def _validate_password(password):
    if not isinstance(password, str) or len(password) < 12:
        raise AuthenticationError("Password must contain at least 12 characters.")
    if len(password) > 128:
        raise AuthenticationError("Password cannot exceed 128 characters.")


def _hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=32,
        maxmem=_SCRYPT_MAXMEM,
    )
    return "scrypt${}${}${}${}${}".format(
        _SCRYPT_N,
        _SCRYPT_R,
        _SCRYPT_P,
        base64.urlsafe_b64encode(salt).decode("ascii"),
        base64.urlsafe_b64encode(digest).decode("ascii"),
    )


def _verify_password(password, encoded_hash):
    try:
        algorithm, n, r, p, salt_text, digest_text = encoded_hash.split("$")
        if algorithm != "scrypt":
            return False
        n, r, p = int(n), int(r), int(p)
        if (n, r, p) != (_SCRYPT_N, _SCRYPT_R, _SCRYPT_P):
            return False
        salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_text.encode("ascii"))
        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=n,
            r=r,
            p=p,
            dklen=len(expected),
            maxmem=_SCRYPT_MAXMEM,
        )
        return hmac.compare_digest(actual, expected)
    except (AttributeError, TypeError, ValueError, UnicodeError):
        return False


_DUMMY_PASSWORD_HASH = _hash_password(secrets.token_urlsafe(24))


def ensure_admin_schema():
    with data_flow_controle.database_connection() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS admin_users (
                    admin_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
                    username VARCHAR(64) NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    status ENUM('Active', 'Inactive') NOT NULL DEFAULT 'Active',
                    failed_attempts INT UNSIGNED NOT NULL DEFAULT 0,
                    lockout_until DATETIME NULL,
                    PRIMARY KEY (admin_id),
                    UNIQUE KEY uq_admin_users_username (username)
                ) ENGINE=InnoDB
                """
            )
            connection.commit()
        finally:
            cursor.close()


def admin_exists():
    with data_flow_controle.database_connection() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT 1 FROM admin_users LIMIT 1")
            return cursor.fetchone() is not None
        finally:
            cursor.close()


def create_first_admin(username, password, confirmation):
    normalized_username = _normalize_username(username)
    _validate_password(password)
    if password != confirmation:
        raise AuthenticationError("The password and confirmation do not match.")
    password_hash = _hash_password(password)

    with data_flow_controle.database_connection() as connection:
        cursor = connection.cursor()
        lock_acquired = False
        try:
            cursor.execute("SELECT GET_LOCK(%s, 5)", ("attendance_admin_setup",))
            lock_acquired = cursor.fetchone()[0] == 1
            if not lock_acquired:
                raise AuthenticationError(
                    "Administrator setup is busy. Please try again."
                )
            cursor.execute("SELECT 1 FROM admin_users LIMIT 1")
            if cursor.fetchone() is not None:
                raise AuthenticationError(
                    "An administrator account already exists."
                )
            cursor.execute(
                "INSERT INTO admin_users (username, password_hash, status) "
                "VALUES (%s, %s, 'Active')",
                (normalized_username, password_hash),
            )
            connection.commit()
        except IntegrityError as exc:
            connection.rollback()
            if exc.errno == 1062:
                raise AuthenticationError(
                    "An administrator account already exists."
                ) from exc
            raise
        finally:
            if lock_acquired:
                cursor.execute("SELECT RELEASE_LOCK(%s)", ("attendance_admin_setup",))
                cursor.fetchone()
            cursor.close()


def authenticate_admin(username, password):
    normalized = str(username or "").strip().lower()
    if not normalized or not password:
        raise AuthenticationError("Enter both username and password.")
    if len(normalized) > 64 or len(password) > 128:
        _verify_password("invalid credentials", _DUMMY_PASSWORD_HASH)
        raise AuthenticationError(
            "Login unsuccessful. Check your credentials or wait before trying again."
        )

    with data_flow_controle.database_connection() as connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT admin_id, username, password_hash, status, "
                "failed_attempts, lockout_until FROM admin_users "
                "WHERE username = %s FOR UPDATE",
                (normalized,),
            )
            admin = cursor.fetchone()
            if admin is None:
                _verify_password(password, _DUMMY_PASSWORD_HASH)
                connection.commit()
                raise AuthenticationError(
                    "Login unsuccessful. Check your credentials or wait before trying again."
                )

            now = datetime.now()
            if admin["status"] != "Active":
                _verify_password(password, _DUMMY_PASSWORD_HASH)
                failures = int(admin["failed_attempts"]) + 1
                lockout_until = None
                if failures >= _MAX_FAILED_ATTEMPTS:
                    exponent = min(failures - _MAX_FAILED_ATTEMPTS, 5)
                    delay = min(
                        _BASE_LOCKOUT_SECONDS * (2 ** exponent),
                        _MAX_LOCKOUT_SECONDS,
                    )
                    lockout_until = now + timedelta(seconds=delay)
                cursor.execute(
                    "UPDATE admin_users SET failed_attempts = %s, "
                    "lockout_until = %s WHERE admin_id = %s",
                    (failures, lockout_until, admin["admin_id"]),
                )
                connection.commit()
                raise AuthenticationError(
                    "Login unsuccessful. Check your credentials or wait before trying again."
                )
            if admin["lockout_until"] is not None and admin["lockout_until"] > now:
                _verify_password(password, admin["password_hash"])
                connection.commit()
                raise AuthenticationError(
                    "Login unsuccessful. Check your credentials or wait before trying again."
                )

            valid = _verify_password(password, admin["password_hash"])
            if not valid:
                failures = int(admin["failed_attempts"]) + 1
                lockout_until = None
                if failures >= _MAX_FAILED_ATTEMPTS:
                    exponent = min(failures - _MAX_FAILED_ATTEMPTS, 5)
                    delay = min(
                        _BASE_LOCKOUT_SECONDS * (2 ** exponent),
                        _MAX_LOCKOUT_SECONDS,
                    )
                    lockout_until = now + timedelta(seconds=delay)
                cursor.execute(
                    "UPDATE admin_users SET failed_attempts = %s, "
                    "lockout_until = %s WHERE admin_id = %s",
                    (failures, lockout_until, admin["admin_id"]),
                )
                connection.commit()
                raise AuthenticationError(
                    "Login unsuccessful. Check your credentials or wait before trying again."
                )

            cursor.execute(
                "UPDATE admin_users SET failed_attempts = 0, lockout_until = NULL "
                "WHERE admin_id = %s",
                (admin["admin_id"],),
            )
            connection.commit()
            return AdminSession(
                admin["admin_id"], admin["username"], _SESSION_TOKEN
            )
        finally:
            cursor.close()


def get_admin_status(admin_id):
    with data_flow_controle.database_connection() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "SELECT status FROM admin_users WHERE admin_id = %s",
                (admin_id,),
            )
            row = cursor.fetchone()
            if row is None:
                raise AuthenticationError("Administrator account was not found.")
            return row[0]
        finally:
            cursor.close()


def change_admin_credentials(
    admin_id, current_password, new_username, new_password, confirmation
):
    username = _normalize_username(new_username)
    if not current_password or len(current_password) > 128:
        raise AuthenticationError("Current password is incorrect.")
    if bool(new_password) != bool(confirmation):
        raise AuthenticationError("Enter and confirm the new password.")
    if new_password:
        _validate_password(new_password)
        if new_password != confirmation:
            raise AuthenticationError("The new password and confirmation do not match.")

    with data_flow_controle.database_connection() as connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT admin_id, username, password_hash, status "
                "FROM admin_users WHERE admin_id = %s FOR UPDATE",
                (admin_id,),
            )
            admin = cursor.fetchone()
            if (
                admin is None
                or admin["status"] != "Active"
                or not _verify_password(current_password, admin["password_hash"])
            ):
                raise AuthenticationError("Current password is incorrect.")

            password_hash = (
                _hash_password(new_password) if new_password else admin["password_hash"]
            )
            cursor.execute(
                "UPDATE admin_users SET username = %s, password_hash = %s, "
                "failed_attempts = 0, lockout_until = NULL WHERE admin_id = %s",
                (username, password_hash, admin_id),
            )
            connection.commit()
            return username
        except IntegrityError as exc:
            connection.rollback()
            if exc.errno == 1062:
                raise AuthenticationError(
                    "That username is already in use."
                ) from exc
            raise
        finally:
            cursor.close()


class AdminAuthenticationWindow(tk.Tk):
    """First-run setup, login, and authenticated main-window lifecycle."""

    def __init__(self):
        super().__init__()
        self.withdraw()
        self.session = None
        self.main_window = None
        self._submitting = False
        self.configure(bg="#2e7e99")
        self.geometry("510x470")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        if not self._database_credentials_configured():
            try:
                saved_credentials = _load_database_credentials()
            except DatabaseCredentialsStorageError as exc:
                messagebox.showwarning(
                    "Saved database credentials unavailable",
                    f"{exc}\nEnter the MySQL connection details to continue.",
                    parent=self,
                )
                saved_credentials = None
            if saved_credentials is None:
                self._show_database_config()
                self.deiconify()
                return
            self._set_database_environment(saved_credentials)

        try:
            self._initialize_authentication()
        except (data_flow_controle.DatabaseStartupError, OSError, mysql.connector.Error) as exc:
            messagebox.showerror(
                "Database startup error",
                f"The attendance database could not be initialized:\n{exc}\n\n"
                "Check the MySQL service, saved connection details, and "
                "database privileges.",
                parent=self,
            )
            self._show_database_config()
            self.deiconify()
            return
        self.deiconify()

    @staticmethod
    def _database_credentials_configured():
        return bool(
            os.environ.get("ATTENDANCE_DB_USER", "").strip()
            and os.environ.get("ATTENDANCE_DB_PASSWORD", "")
        )

    @staticmethod
    def _set_database_environment(credentials):
        os.environ["ATTENDANCE_DB_HOST"] = credentials["host"]
        os.environ["ATTENDANCE_DB_PORT"] = credentials["port"]
        os.environ["ATTENDANCE_DB_USER"] = credentials["user"]
        os.environ["ATTENDANCE_DB_PASSWORD"] = credentials["password"]

    def _initialize_authentication(self):
        data_flow_controle.initialize_project(show_warnings=False)
        ensure_admin_schema()
        self._show_login() if admin_exists() else self._show_setup()

    def _show_database_config(self):
        self._clear_screen()
        self.title("Database Connection")
        self.geometry("510x540")
        self._build_heading("Connect to the local MySQL database")
        form = tk.Frame(self, bg="#2e7e99")
        form.pack(fill="x", padx=65)
        self.database_host_entry = self._add_field(form, "MySQL Host")
        self.database_host_entry.insert(
            0, os.environ.get("ATTENDANCE_DB_HOST", "127.0.0.1")
        )
        self.database_port_entry = self._add_field(form, "MySQL Port")
        self.database_port_entry.insert(
            0, os.environ.get("ATTENDANCE_DB_PORT", "3306")
        )
        self.database_user_entry = self._add_field(form, "MySQL Username")
        self.database_user_entry.insert(
            0, os.environ.get("ATTENDANCE_DB_USER", "")
        )
        self.database_password_entry = self._add_field(
            form, "MySQL Password", show="*"
        )
        self._add_show_password(form, (self.database_password_entry,))
        tk.Label(
            form,
            text="After connecting, details are encrypted for your Windows account.",
            font=("Segoe UI", 9), bg="#2e7e99", fg="#e7f7ff",
        ).pack(anchor="w", pady=(8, 0))
        tk.Button(
            form, text="Connect", command=self._submit_database_config,
            font=("Arial Black", 10), bg="#1f5d7e", fg="white",
            activebackground="#1f5d7e", activeforeground="#00ffff",
        ).pack(fill="x", pady=(18, 8), ipady=7)
        self.unbind("<Return>")
        self.bind("<Return>", lambda _event: self._submit_database_config())
        self.database_host_entry.focus_set()

    def _submit_database_config(self):
        host = self.database_host_entry.get().strip()
        port = self.database_port_entry.get().strip()
        username = self.database_user_entry.get().strip()
        password = self.database_password_entry.get()
        if not host or not port or not username or not password:
            messagebox.showerror(
                "Database details required",
                "Enter the MySQL host, port, username, and password.",
                parent=self,
            )
            return

        credentials = {
            "host": host,
            "port": port,
            "user": username,
            "password": password,
        }
        self._set_database_environment(credentials)
        try:
            self._initialize_authentication()
        except (data_flow_controle.DatabaseStartupError, OSError, mysql.connector.Error) as exc:
            messagebox.showerror(
                "Database connection failed",
                f"The attendance database could not be initialized:\n{exc}",
                parent=self,
            )
            self.database_password_entry.delete(0, tk.END)
            self.database_password_entry.focus_set()
            return
        try:
            _save_database_credentials(credentials)
        except DatabaseCredentialsStorageError as exc:
            messagebox.showwarning(
                "Database credentials not saved",
                "The database connection succeeded, but the credentials could "
                f"not be saved securely:\n{exc}\n\n"
                "You will need to enter them again the next time you start "
                "the application.",
                parent=self,
            )
        self.deiconify()

    def _clear_screen(self):
        for child in self.winfo_children():
            child.destroy()

    def _build_heading(self, subtitle):
        tk.Label(
            self, text="Automatic Attendance System",
            font=("Arial Black", 18), bg="#2e7e99", fg="white",
        ).pack(pady=(24, 6))
        tk.Label(
            self, text=subtitle, font=("Segoe UI", 11),
            bg="#2e7e99", fg="#e7f7ff",
        ).pack(pady=(0, 16))

    @staticmethod
    def _add_field(parent, label, show=None):
        tk.Label(
            parent, text=label, font=("Arial Black", 10),
            bg="#2e7e99", fg="white", anchor="w",
        ).pack(fill="x", pady=(8, 3))
        entry = tk.Entry(parent, font=("Segoe UI", 12), show=show or "")
        entry.pack(fill="x", ipady=5)
        return entry

    def _show_setup(self):
        self._clear_screen()
        self._submitting = False
        self.title("Create Administrator Account")
        self.geometry("510x570")
        self._build_heading("Create the first administrator account")
        form = tk.Frame(self, bg="#2e7e99")
        form.pack(fill="x", padx=65)
        self.username_entry = self._add_field(form, "Admin Username")
        self.password_entry = self._add_field(form, "Password", show="*")
        self.confirm_entry = self._add_field(form, "Confirm Password", show="*")
        self._add_show_password(form, (self.password_entry, self.confirm_entry))
        tk.Label(
            form, text="Username: 3–64 characters. Password: at least 12 characters.",
            font=("Segoe UI", 9), bg="#2e7e99", fg="#e7f7ff",
        ).pack(anchor="w", pady=(8, 0))
        tk.Button(
            form, text="Create Admin Account", command=self._submit_setup,
            font=("Arial Black", 10), bg="#1f5d7e", fg="white",
            activebackground="#1f5d7e", activeforeground="#00ffff",
        ).pack(fill="x", pady=(18, 8), ipady=7)
        self.unbind("<Return>")
        self.bind("<Return>", lambda _event: self._submit_setup())
        self.username_entry.focus_set()

    def _show_login(self):
        self._clear_screen()
        self._submitting = False
        self.title("Administrator Login")
        self.geometry("510x455")
        self._build_heading("Administrator Login")
        form = tk.Frame(self, bg="#2e7e99")
        form.pack(fill="x", padx=65)
        self.username_entry = self._add_field(form, "Username")
        self.password_entry = self._add_field(form, "Password", show="*")
        self._add_show_password(form, (self.password_entry,))
        self.login_button = tk.Button(
            form, text="Login", command=self._submit_login,
            font=("Arial Black", 10), bg="#1f5d7e", fg="white",
            activebackground="#1f5d7e", activeforeground="#00ffff",
        )
        self.login_button.pack(fill="x", pady=(22, 8), ipady=7)
        self.unbind("<Return>")
        self.bind("<Return>", lambda _event: self._submit_login())
        self.username_entry.focus_set()

    @staticmethod
    def _add_show_password(parent, entries):
        visible = tk.BooleanVar(value=False)

        def toggle():
            mask = "" if visible.get() else "*"
            for entry in entries:
                entry.configure(show=mask)

        tk.Checkbutton(
            parent, text="Show password", variable=visible, command=toggle,
            bg="#2e7e99", fg="white", selectcolor="#1f5d7e",
            activebackground="#2e7e99", activeforeground="white",
        ).pack(anchor="w", pady=(8, 0))

    def _submit_setup(self):
        if self._submitting:
            return
        username = self.username_entry.get()
        password = self.password_entry.get()
        confirmation = self.confirm_entry.get()
        try:
            create_first_admin(username, password, confirmation)
        except AuthenticationError as exc:
            messagebox.showerror("Setup not completed", str(exc), parent=self)
            return
        except mysql.connector.Error as exc:
            messagebox.showerror(
                "Database error",
                f"The administrator account could not be saved:\n{exc}",
                parent=self,
            )
            return
        self._submitting = True
        messagebox.showinfo(
            "Administrator created",
            "The administrator account was created. Sign in to continue.",
            parent=self,
        )
        self._show_login()

    def _submit_login(self):
        if self._submitting:
            return
        username = self.username_entry.get()
        password = self.password_entry.get()
        if not username.strip() or not password:
            messagebox.showerror(
                "Login required", "Enter both username and password.", parent=self
            )
            return
        self._submitting = True
        self.login_button.configure(state=tk.DISABLED)
        try:
            self.session = authenticate_admin(username, password)
        except AuthenticationError as exc:
            self._submitting = False
            self.login_button.configure(state=tk.NORMAL)
            messagebox.showerror("Login unsuccessful", str(exc), parent=self)
            self.password_entry.delete(0, tk.END)
            self.password_entry.focus_set()
            return
        except mysql.connector.Error as exc:
            self._submitting = False
            self.login_button.configure(state=tk.NORMAL)
            self.password_entry.delete(0, tk.END)
            messagebox.showerror(
                "Database error",
                f"Login could not be completed because the database is unavailable:\n{exc}",
                parent=self,
            )
            return
        self._open_application()

    def _open_application(self):
        from interface_main import Caller_interface

        if hasattr(self, "password_entry"):
            self.password_entry.delete(0, tk.END)
        self._clear_screen()
        self.withdraw()
        try:
            self.auth_session = self.session
            data_flow_controle.set_authenticated_session(self.session)
            self.main_window = Caller_interface(self, self.session)
            if not self.main_window.startup_ok:
                self.session.invalidate()
                self.session = None
                self.auth_session = None
                data_flow_controle.set_authenticated_session(None)
                self.deiconify()
                self._show_login()
                return
            self.main_window.configure(bg="#2e7e99")
            try:
                photo = tk.PhotoImage(file=data_flow_controle.resolve_path("Buttons", "Teacher.png"))
            except (OSError, tk.TclError):
                photo = None
            if photo is not None:
                try:
                    self.main_window.iconphoto(False, photo)
                except tk.TclError as exc:
                    logging.warning("Could not set the application icon: %s", exc)
            self.main_window.wm_minsize(width=1080, height=648)
            self.main_window.title("Teacher today Attendance")
            self.main_window.protocol("WM_DELETE_WINDOW", self.main_window.on_close)
            self.main_window.heading()
            self.main_window.build_Table()
            self.main_window.build_buttons()
            self.main_window.after(300, self.main_window.data_reciver)
            self.main_window.deiconify()
        except Exception as exc:
            self.session.invalidate()
            self.session = None
            self.auth_session = None
            data_flow_controle.set_authenticated_session(None)
            self.deiconify()
            self._show_login()
            messagebox.showerror(
                "Application startup error",
                f"The application could not be opened:\n{exc}",
                parent=self,
            )

    def logout(self, main_window, session):
        if session is not self.session or not session.is_authenticated():
            return
        session.invalidate()
        self.session = None
        self.auth_session = None
        data_flow_controle.set_authenticated_session(None)
        self.main_window = None
        main_window.destroy()
        self.deiconify()
        self._show_login()

    def close_application(self):
        if self.session is not None:
            self.session.invalidate()
            self.session = None
        self.auth_session = None
        data_flow_controle.set_authenticated_session(None)
        self.destroy()


class AdminAccountWindow(tk.Toplevel):
    """Current-password-verified administrator username/password management."""

    def __init__(self, parent):
        require_authenticated_parent(parent)
        super().__init__(parent)
        self.parent = parent
        self.session = parent.auth_session
        self.configure(bg="#2e7e99")
        self.title("Administrator Account")
        self.geometry("520x520")
        self.resizable(False, False)
        self.transient(parent)
        self._build()

    def _build(self):
        tk.Label(
            self, text="Administrator Account",
            font=("Arial Black", 18), bg="#2e7e99", fg="white",
        ).pack(pady=(20, 10))
        try:
            status = get_admin_status(self.session.admin_id)
        except (mysql.connector.Error, AuthenticationError) as exc:
            messagebox.showerror(
                "Account unavailable", f"Could not load account status:\n{exc}", parent=self
            )
            self.destroy()
            return
        tk.Label(
            self, text=f"Account status: {status}",
            font=("Segoe UI", 11), bg="#2e7e99", fg="#e7f7ff",
        ).pack(pady=(0, 12))
        form = tk.Frame(self, bg="#2e7e99")
        form.pack(fill="x", padx=55)
        self.current_password = AdminAuthenticationWindow._add_field(
            form, "Current Password", show="*"
        )
        self.username = AdminAuthenticationWindow._add_field(
            form, "New Username", show=None
        )
        self.username.insert(0, self.session.username)
        self.new_password = AdminAuthenticationWindow._add_field(
            form, "New Password (leave blank to keep current)", show="*"
        )
        self.confirm_password = AdminAuthenticationWindow._add_field(
            form, "Confirm New Password", show="*"
        )
        AdminAuthenticationWindow._add_show_password(
            form, (self.current_password, self.new_password, self.confirm_password)
        )
        buttons = tk.Frame(self, bg="#2e7e99")
        buttons.pack(pady=18)
        tk.Button(
            buttons, text="Save Changes", command=self._save,
            font=("Arial Black", 10), bg="#1f5d7e", fg="white",
        ).pack(side=tk.LEFT, padx=8, ipadx=8, ipady=4)
        tk.Button(
            buttons, text="Cancel", command=self.destroy,
            font=("Arial Black", 10), bg="#1f5d7e", fg="white",
        ).pack(side=tk.LEFT, padx=8, ipadx=8, ipady=4)

    def _save(self):
        require_authenticated_parent(self.parent)
        try:
            username = change_admin_credentials(
                self.session.admin_id,
                self.current_password.get(),
                self.username.get(),
                self.new_password.get(),
                self.confirm_password.get(),
            )
        except AuthenticationError as exc:
            messagebox.showerror("Account update failed", str(exc), parent=self)
            return
        except mysql.connector.Error as exc:
            messagebox.showerror(
                "Database error", f"Account changes were not saved:\n{exc}", parent=self
            )
            return
        self.session.username = username
        messagebox.showinfo(
            "Account updated", "Administrator account changes were saved.", parent=self
        )
        self.destroy()
