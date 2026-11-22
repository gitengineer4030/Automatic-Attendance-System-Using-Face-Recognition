from datetime import datetime, timedelta
import os
import re
import pickle
import tkinter
from tkinter import *
from tkinter import ttk, messagebox
import openpyxl
import mysql.connector
import data_flow_controle
from data_flow_controle import resolve_path
from admin_auth import require_authenticated_parent
from main import create_optional_image_button

class _LegacyExcelHistoryManagement:
    def __init__(self):
        self.present = None
    ############################################################################################################################
    def attendance_file_reader(self):
        with open(resolve_path("pathsfolder", "address.data"), "rb") as myfile:
            address = pickle.load(myfile)
        return openpyxl.load_workbook(address)

    def registration_date_backup(self):
        with open(resolve_path("pathsfolder", "address3.data"), "rb") as txtfile:
            reg_file = pickle.load(txtfile)
        with open(resolve_path("pathsfolder", "address.data"), "rb") as myfile:
            address = pickle.load(myfile)
        return migrate_registration_dates_sheet(address, reg_file)
    ############################################################################################################################

    def reg_file_details(self,id_no):
        with open(resolve_path("pathsfolder", "address3.data"), "rb") as myfile:
            registration_file = pickle.load(myfile)
        workbook = openpyxl.load_workbook(registration_file, data_only=True)
        try:
            sheet = (
                workbook["Registration"]
                if "Registration" in workbook.sheetnames
                else workbook.worksheets[0]
            )
            headers = {
                re.sub(r"[^a-z0-9]", "", str(sheet.cell(1, column).value).lower()): column
                for column in range(1, sheet.max_column + 1)
                if sheet.cell(1, column).value is not None
            }
            id_column = headers.get("idno")
            date_column = headers.get("dateofregistration")
            if id_column is None or date_column is None:
                return None
            requested_id = str(id_no).strip()
            for row in range(2, sheet.max_row + 1):
                teacher_id = sheet.cell(row, id_column).value
                if isinstance(teacher_id, float) and teacher_id.is_integer():
                    teacher_id = int(teacher_id)
                if str(teacher_id).strip() == requested_id:
                    return sheet.cell(row, date_column).value
            return None
        finally:
            workbook.close()

    def month_no_to_month_name(self,month):
        month_by_name = {
            "01":"Jan",
            "02":"Feb",
            "03":"Mar",
            "04":"Apr",
            "05":"May",
            "06":"June",
            "07":"Jul",
            "08":"Aug",
            "09": "Sep",
            "10":"Oct",
            "11":"Nov",
            "12":"Dec"
        }
        return month_by_name[month]


    def file_reader(self,id_num):
        date_of_reg = self.reg_file_details(id_num)
        if date_of_reg is None:
            return
        # Handle datetime objects (Excel date format)
        if isinstance(date_of_reg, datetime):
            day_of_reg = date_of_reg.day
            month_of_reg = str(date_of_reg.month).zfill(2)
        else:
            date_str = str(date_of_reg).strip()
            # Try DD/MM/YYYY or DD/MM format (day first, then month - common in Pakistan)
            parts = date_str.split("/")
            if len(parts) >= 3:
                try:
                    day_of_reg = int(parts[0])      # First part is day
                    month_of_reg = parts[1].zfill(2) # Second part is month
                except ValueError:
                    return
            elif len(parts) == 2:
                try:
                    day_of_reg = int(parts[0])      # First part is day
                    month_of_reg = parts[1].zfill(2) # Second part is month
                except ValueError:
                    return
            else:
                return
        reg_month_name=self.month_no_to_month_name(month_of_reg)
        print(reg_month_name)
        present_list = []
        percentage = 0
        start_date = None
        self.month1_present=self.month2_present=self.month3_present=self.month4_present = self.month5_present = self.month6_present =None
        self.month7_present = self.month8_present=self.month9_present=self.month10_present=self.month11_present=self.month12_present=None
        ######################################################################################################
        self.month1_absence = self.month2_absence = self.month3_absence =self.month4_absence = self.month5_absence = self.month6_absence =None
        self.month7_absence = self.month8_absence = self.month9_absence = self.month10_absence =self.month11_absence =self.month12_absence =None
        ###########################################################################################################
        self.month1_percentage = self.month2_percentage = self.month3_percentage = self.month4_percentage = self.month5_percentage = self.month6_percentage = None
        self.month7_percentage = self.month8_percentage = self.month9_percentage = self.month10_percentage = self.month11_percentage = self.month12_percentage=None
        ########################################################################################################################
        with open(resolve_path("pathsfolder", "address.data"), "rb") as myfile:
            address = pickle.load(myfile)
        workbook = openpyxl.load_workbook(address)
        months= ["Jan","Feb","Mar","Apr","May","June","Jul","Aug","Sep","Oct","Nov","Dec"]
        for month in months:
            if month in workbook.sheetnames:
                sheet = workbook[month]
                row = sheet.max_row
                colums = sheet.max_column
                for r in range(2, row + 1):
                    for c in range(1, colums + 1):
                        if c == 2:
                            if sheet.cell(r, c).value == id_num:
                                present_list.append(sheet.cell(r,c).value)

                present = present_list.count(id_num)
                present_list.clear()
                start_date = 1
                if month == "Jan":
                    if month == reg_month_name:
                        start_date = day_of_reg
                    day = int(datetime.today().strftime("%d"))
                    if start_date<=day:
                        days = day - start_date
                    else:
                        day = 31
                        days = day-start_date
                    self.month1_present = present
                    if days > 0:
                        self.month1_absence = days - present + 1
                    else:
                        self.month1_absence = 0
                    if self.month1_present >= 1:
                        self.month1_percentage = round(self.month1_present / 31 * 100,2)
                elif month == "Feb":
                    if month == reg_month_name:
                        start_date = day_of_reg
                    year = int(datetime.today().strftime("%Y"))
                    day = int(datetime.today().strftime("%d"))
                    if year % 400 == 0 or year % 4 == 0 and year % 100 != 0:
                        if start_date <=day:
                            days = day - start_date
                        else:
                            day = 29
                            days = day - start_date
                    else:
                        if start_date <=day:
                            days = day - start_date
                        else:
                            day = 28
                            days = day - start_date
                    self.month2_present = present
                    if days > 0:
                        self.month2_absence = days - present + 1
                    else:
                        self.month2_absence = 0
                    if self.month2_present >= 1:
                        self.month2_percentage = round(self.month2_present / 31 * 100,2)
                elif month == "Mar":
                    if month == reg_month_name:
                        start_date = day_of_reg
                    day = int(datetime.today().strftime("%d"))
                    if start_date<=day:
                        days = day - start_date
                    else:
                        day = 31
                        days = day-start_date
                    self.month3_present = present
                    if days > 0:
                        self.month3_absence = days - present + 1
                    else:
                        self.month3_absence = 0
                    if self.month3_present >= 1:
                        self.month3_percentage = round(self.month3_present / 31 * 100,2)
                elif month == "Apr":
                    if month == reg_month_name:
                        start_date = day_of_reg
                    day = int(datetime.today().strftime("%d"))
                    if start_date<=day:
                        days = day - start_date
                    else:
                        day = 30
                        days = day - start_date
                    self.month4_present = present
                    if days > 0:
                        self.month4_absence = days - present + 1
                    else:
                        self.month4_absence = 0
                    if self.month4_present >= 1:
                        self.month4_percentage = round(self.month4_present / 31 * 100,2)
                elif month == "May":
                    if month == reg_month_name:
                        start_date = day_of_reg
                    day = int(datetime.today().strftime("%d"))
                    if start_date<=day:
                        days = day - start_date
                    else:
                        day = 31
                        days = day - start_date
                    self.month5_present = present
                    if days > 0:
                        self.month5_absence = days - present + 1
                    else:
                        self.month5_absence = 0
                    if self.month5_present >= 1:
                        self.month5_percentage = round(self.month5_present / 31 * 100,2)
                elif month == "June":
                    if month == reg_month_name:
                        start_date = day_of_reg
                    day = int(datetime.today().strftime("%d"))
                    if start_date<=day:
                        days = day - start_date
                    else:
                        day = 30
                        days = day - start_date
                    self.month6_present = present
                    if days > 0:
                        self.month6_absence = days - present + 1
                    else:
                        self.month6_absence = 0
                    if self.month6_present >= 1:
                        self.month6_percentage = round(self.month6_present / 31 * 100,2)
                elif month == "Jul":
                    if month == reg_month_name:
                        start_date = day_of_reg
                    day = int(datetime.today().strftime("%d"))
                    if start_date<=day:
                        days = day - start_date
                    else:
                        day = 31
                        days = day - start_date
                    self.month7_present = present
                    if days > 0:
                        self.month7_absence = days - present + 1
                    else:
                        self.month7_absence = 0
                    if self.month7_present >= 1:
                        self.month7_percentage = round(self.month7_present / 31 * 100,2)
                elif month == "Aug":
                    if month == reg_month_name:
                        start_date = day_of_reg
                    day = int(datetime.today().strftime("%d"))
                    if start_date <= day:
                        days = day - start_date
                    else:
                        day = 31
                        days = day - start_date
                    self.month8_present = present
                    if days > 0:
                        self.month8_absence = days - present + 1
                    else:
                        self.month8_absence = 0
                    if self.month8_present >= 1:
                        self.month8_percentage = round(self.month8_present / 31 * 100,2)
                elif month == "Sep":
                    if month == reg_month_name:
                        start_date = day_of_reg
                    day = int(datetime.today().strftime("%d"))
                    if start_date <= day:
                        days = day - start_date
                    else:
                        day = 30
                        days = day - start_date
                    self.month9_present = present
                    if days > 0:
                        self.month9_absence = days - present + 1
                    else:
                        self.month9_absence = 0
                    if self.month9_present >=1:
                        self.month9_percentage = round(self.month9_present / 31 * 100,2)
                elif month == "Oct":
                    if month == reg_month_name:
                        start_date = day_of_reg
                    day = int(datetime.today().strftime("%d"))
                    if start_date <= day:
                        days = day - start_date
                    else:
                        day = 31
                        days = day - start_date
                    self.month10_present = present
                    if days > 0:
                        self.month10_absence = days - present + 1
                    else:
                        self.month10_absence = 0
                    if self.month10_present >=1:
                        self.month10_percentage = round(self.month10_present / 31 * 100,2)
                elif month == "Nov":
                    if month == reg_month_name:
                        start_date = day_of_reg
                    day = int(datetime.today().strftime("%d"))
                    if start_date <= day:
                        days = day - start_date
                    else:
                        day = 30
                        days = day - start_date
                    self.month11_present = present
                    if days > 0:
                        self.month11_absence = days - present + 1
                    else:
                        self.month11_absence = 0
                    if self.month11_present >=1:
                        self.month11_percentage = round(self.month11_present / 31 * 100,2)
                elif month == "Dec":
                    if month == reg_month_name:
                        start_date = day_of_reg
                    day = int(datetime.today().strftime("%d"))
                    if start_date <= day:
                        days = day - start_date
                    else:
                        day = 31
                        days = day - start_date
                    self.month12_present = present
                    if days > 0:
                        self.month12_absence = days - present + 1
                    else:
                        self.month12_absence = 0
                    if self.month12_present >=1:
                        self.month12_percentage = round(self.month12_present / 31 * 100,2)
#########################################################################################################################
#  History interface
#########################################################################################################################

class History_management:
    """Compatibility access to historical records backed by MySQL."""

    def reg_file_details(self, teacher_id):
        return data_flow_controle.get_registration_date(teacher_id)

    def file_reader(self, teacher_id, year=None):
        year = year or datetime.today().year
        return data_flow_controle.get_attendance_records(
            teacher_id,
            datetime(year, 1, 1).date(),
            datetime(year, 12, 31).date(),
        )


class History_table(Toplevel):
    """Modern teacher attendance history window, compatible with the existing Tkinter app."""

    MONTHS = [
        ("Jan", 1), ("Feb", 2), ("Mar", 3), ("Apr", 4),
        ("May", 5), ("June", 6), ("Jul", 7), ("Aug", 8),
        ("Sep", 9), ("Oct", 10), ("Nov", 11), ("Dec", 12),
    ]
    BG = "#2e7e99"
    PANEL = "#1f5d7e"
    PANEL_LIGHT = "#2a6f97"
    BLUE = "#087cff"
    TEXT = "#f4f8ff"
    MUTED = "#cfe8f6"
    GREEN = "#16bd87"
    RED = "#ff4963"

    def __init__(self, parent):
        require_authenticated_parent(parent)
        super().__init__(parent)
        self.parent = parent
        self.auth_session = parent.auth_session
        self.title("Teacher Attendance Record")
        self.geometry("1500x850")
        self.minsize(1120, 680)
        self.configure(bg=self.BG)

        self.reg_list = []
        self.teachers = []
        self.attendance_records = []
        self.filtered_records = []
        self.selected_teacher = None
        self.registration_date = None
        self.table = None
        self.month_table = None
        self.teacher_load_error = None
        self.name_var = StringVar()
        self.academic_year_start = self._detect_academic_year()
        self.academic_year = str(self.academic_year_start)
        self.record_type_var = StringVar(value="All Records")
        # Default: Sunday is excluded. All other weekdays are included.
        # The user can change any checkbox at any time.
        self.excluded_days = {6}
        self._load_excluded_days()
        self.from_var = StringVar(value=f"01/01/{datetime.today().year}")
        self.to_var = StringVar(value=datetime.today().strftime("%m/%d/%Y"))
        self.status_var = StringVar(value="Select a teacher to load attendance history.")
        self._load_teachers()
        self._configure_styles()
        self._build_ui()
        self._populate_teacher_list()
        self._refresh_history()

    # ---------- Data access ----------
    @staticmethod
    def _read_pickle(path):
        with open(path, "rb") as handle:
            return pickle.load(handle)

    def _detect_academic_year(self):
        """Use the current calendar year as the default attendance period."""
        return datetime.today().year

    # ---------- Excluded days persistence ----------
    EXCLUDED_DAYS_FILE = resolve_path("pathsfolder", "excluded_days.data")

    @staticmethod
    def _load_excluded_days_static():
        """Load excluded weekdays from disk. Returns a set of weekday ints (0=Mon .. 6=Sun)."""
        try:
            if not os.path.exists(History_table.EXCLUDED_DAYS_FILE):
                return set()
            with open(History_table.EXCLUDED_DAYS_FILE, "rb") as handle:
                data = pickle.load(handle)
            if isinstance(data, (list, tuple, set)):
                return {int(d) for d in data}
        except Exception:
            pass
        return set()

    @staticmethod
    def _save_excluded_days_static(days):
        """Persist excluded weekdays to disk."""
        try:
            os.makedirs(os.path.dirname(History_table.EXCLUDED_DAYS_FILE), exist_ok=True)
            with open(History_table.EXCLUDED_DAYS_FILE, "wb") as handle:
                pickle.dump(sorted(int(d) for d in days), handle)
        except Exception:
            pass

    def _load_excluded_days(self):
        self.excluded_days = self._load_excluded_days_static()

    def _save_excluded_days(self):
        self._save_excluded_days_static(self.excluded_days)

    def _is_excluded_day(self, weekday_int):
        return weekday_int in self.excluded_days

    def _on_excluded_day_toggled(self):
        """Handle excluded-days checkbox toggles: rebuild selection, persist, and refresh."""
        self.excluded_days = {
            weekday_int
            for weekday_int, var in self.excluded_day_vars.items()
            if var.get()
        }
        self._save_excluded_days()
        # Refresh the display so calculations reflect the new exclusion set
        self._refresh_history()

    @staticmethod
    def _parse_date(value):
        if value is None or value == "":
            return None
        if isinstance(value, datetime):
            return value.date()
        if hasattr(value, "year") and hasattr(value, "month") and hasattr(value, "day"):
            try:
                return value
            except Exception:
                pass
        raw = str(value).strip()
        for fmt in (
            "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d",
            "%d-%m-%Y", "%m-%d-%Y", "%d/%m/%y",
        ):
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                continue
        return None

    @staticmethod
    def _parse_registration_date(value):
        if value is None or value == "":
            return None
        if isinstance(value, datetime):
            return value.date()
        if hasattr(value, "year") and hasattr(value, "month") and hasattr(value, "day"):
            return value
        raw = str(value).strip()
        for date_format in (
            "%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d",
            "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y",
        ):
            try:
                return datetime.strptime(raw, date_format).date()
            except ValueError:
                continue
        return None

    # ---------- Strict date validation for user input ----------
    _DATE_RE = re.compile(r"^\d{2}/\d{2}/\d{4}$")

    @staticmethod
    def _validate_date_string(date_str):
        """Strictly validate a date string in MM/DD/YYYY format.

        Returns a datetime.date object if valid, otherwise None.
        Shows a warning message via messagebox if invalid.
        """
        if not date_str or not date_str.strip():
            return None
        raw = date_str.strip()
        # Enforce exact MM/DD/YYYY pattern (rejects DD/MM/YYYY, YYYY-MM-DD, etc.)
        if not History_table._DATE_RE.match(raw):
            messagebox.showerror(
                "Invalid date format",
                f"'{raw}' is not a valid date.\n"
                f"Please enter the date in MM/DD/YYYY format (e.g., 01/15/2026).",
            )
            return None
        try:
            return datetime.strptime(raw, "%m/%d/%Y").date()
        except ValueError:
            messagebox.showerror(
                "Invalid date",
                f"'{raw}' is not a valid calendar date.\n"
                f"Please enter a real date in MM/DD/YYYY format (e.g., 01/15/2026).",
            )
            return None

    # ---------- Calendar icon ----------
    def _create_calendar_icon(self, size=20):
        """Draw a clean, modern calendar icon on a transparent canvas and return PhotoImage."""
        import tkinter as tk
        canvas = tk.Canvas(self, width=size, height=size,
                           highlightthickness=0, bd=0)
        # Make canvas background transparent
        canvas.configure(bg='white')
        pad = 2
        page_w = size - pad * 2
        page_h = size - pad * 2
        # Outer calendar page
        canvas.create_rectangle(pad, pad, pad + page_w, pad + page_h,
                                fill="white", outline="#1a4e6b", width=1.5)
        # Header bar with rounded top corners
        header_h = 6
        canvas.create_rectangle(pad + 1, pad + 1, pad + page_w - 1, pad + 1 + header_h,
                                fill="#1a4e6b", outline="#1a4e6b")
        # Spiral binding circle
        cx = pad + page_w // 2
        cy = pad + 1 + header_h // 2
        canvas.create_oval(cx - 2, cy - 2, cx + 2, cy + 2,
                           fill="white", outline="#1a4e6b")
        # Date grid cells
        cell = 2
        gap = 1.5
        start_x = pad + 4
        start_y = pad + 1 + header_h + 3
        for r in range(2):
            for c in range(3):
                x0 = start_x + c * (cell + gap)
                y0 = start_y + r * (cell + gap)
                canvas.create_rectangle(x0, y0, x0 + cell, y0 + cell,
                                        fill="#1a4e6b", outline="")
        canvas.update()
        img = tk.PhotoImage(width=size, height=size)
        img.blank()
        for i in range(size):
            img.put("white", to=(0, i))
        # Border
        for i in range(size):
            img.put("#1a4e6b", to=(pad, pad + i))
            img.put("#1a4e6b", to=(pad + i, pad))
            img.put("#1a4e6b", to=(size - pad - 1, pad + i))
            img.put("#1a4e6b", to=(pad + i, size - pad - 1))
        # Header bar
        for x in range(pad + 1, size - pad - 1):
            for y in range(pad + 1, pad + 1 + header_h):
                img.put("#1a4e6b", to=(x, y))
        # Spiral circle
        cx = size // 2
        cy = pad + 1 + header_h // 2
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if dx * dx + dy * dy <= 4:
                    img.put("#1a4e6b", to=(cx + dx, cy + dy))
        # Date grid cells
        cell = 2
        gap = 1.5
        start_x = pad + 4
        start_y = pad + 1 + header_h + 3
        for r in range(2):
            for c in range(3):
                x0 = start_x + c * (cell + gap)
                y0 = start_y + r * (cell + gap)
                for xx in range(cell):
                    for yy in range(cell):
                        img.put("#1a4e6b", to=(int(x0 + xx), int(y0 + yy)))
        canvas.destroy()
        return img

    # ---------- Calendar date picker ----------
    def _open_calendar(self, target_var):
        """Open a popup calendar to pick a date in MM/DD/YYYY format."""
        cal = Toplevel(self)
        cal.title("Select Date")
        cal.configure(bg=self.BG)
        cal.resizable(False, False)
        cal.transient(self)
        cal.grab_set()

        # Center on parent
        cal.update_idletasks()
        px = self.winfo_rootx() + 50
        py = self.winfo_rooty() + 50
        cal.geometry(f"+{px}+{py}")

        now = datetime.today()
        year_var = IntVar(value=now.year)
        month_var = IntVar(value=now.month)

        # Header: month/year navigation
        hdr = Frame(cal, bg=self.BG)
        hdr.pack(pady=(10, 5), padx=10, fill=X)

        def prev_month():
            m = month_var.get() - 1
            y = year_var.get()
            if m < 1:
                m = 12
                y -= 1
            month_var.set(m)
            year_var.set(y)
            _build_grid()

        def next_month():
            m = month_var.get() + 1
            y = year_var.get()
            if m > 12:
                m = 1
                y += 1
            month_var.set(m)
            year_var.set(y)
            _build_grid()

        btn_prev = Button(hdr, text="<", command=prev_month,
                          bg=self.PANEL, fg="white", font=("Segoe UI", 10, "bold"),
                          width=3, relief=FLAT, cursor="hand2")
        btn_prev.pack(side=LEFT)

        lbl_my = Label(hdr, text="", bg=self.BG, fg=self.TEXT,
                       font=("Segoe UI", 11, "bold"), width=12)
        lbl_my.pack(side=LEFT, expand=True)

        btn_next = Button(hdr, text=">", command=next_month,
                          bg=self.PANEL, fg="white", font=("Segoe UI", 10, "bold"),
                          width=3, relief=FLAT, cursor="hand2")
        btn_next.pack(side=RIGHT)

        # Weekday headers
        week_hdr = Frame(cal, bg=self.PANEL)
        week_hdr.pack(padx=10, pady=(0, 2), fill=X)
        for wd in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            Label(week_hdr, text=wd, bg=self.PANEL, fg=self.TEXT,
                  font=("Segoe UI", 9, "bold"), width=4).pack(side=LEFT, expand=True, padx=1)

        # Day grid
        grid_frame = Frame(cal, bg=self.BG)
        grid_frame.pack(padx=10, pady=(0, 10))

        day_buttons = []

        def _build_grid():
            for btn in day_buttons:
                btn.destroy()
            day_buttons.clear()

            y = year_var.get()
            m = month_var.get()
            lbl_my.configure(text=datetime(y, m, 1).strftime("%B %Y"))

            first_weekday, num_days = calendar.monthrange(y, m)
            # calendar.monthrange returns (weekday_of_first_day, days_in_month)
            # Monday=0 ... Sunday=6

            row = 0
            col = first_weekday
            for day in range(1, num_days + 1):
                btn = Button(grid_frame, text=str(day), width=4,
                             bg=self.PANEL_LIGHT, fg=self.TEXT,
                             font=("Segoe UI", 9),
                             relief=FLAT, cursor="hand2",
                             command=lambda d=day: _select_date(d))
                btn.grid(row=row, column=col, padx=1, pady=1)
                day_buttons.append(btn)
                col += 1
                if col > 6:
                    col = 0
                    row += 1

        def _select_date(day):
            y = year_var.get()
            m = month_var.get()
            chosen = datetime(y, m, day).date()
            target_var.set(chosen.strftime("%m/%d/%Y"))
            cal.grab_release()
            cal.destroy()

        # Today button
        btn_today = Button(cal, text="Today", command=lambda: _select_date(now.day),
                           bg=self.BLUE, fg="white", font=("Segoe UI", 9),
                           relief=FLAT, cursor="hand2")
        btn_today.pack(pady=(0, 10))

        # Need calendar module for monthrange
        import calendar
        _build_grid()
        cal.wait_window()

    @staticmethod
    def _safe_int(value):
        try:
            teacher_id = str(value).strip()
            return teacher_id if teacher_id.isdigit() else None
        except (TypeError, ValueError):
            return None

    def _load_teachers(self):
        self.teacher_load_error = None
        try:
            rows = data_flow_controle.get_teachers()
            self.teachers = [
                {
                    "teacher_pk": row["teacher_pk"],
                    "name": str(row["name"] or "").strip(),
                    "father_name": str(row["father_name"] or "").strip(),
                    "id": str(row["teacher_id"]).strip(),
                    "subject": str(row["subject"] or "").strip(),
                    "phone": str(row["phone_number"] or "").strip(),
                    "registration_date": row["registration_date"],
                    "account_status": row["status"],
                }
                for row in rows
            ]
        except mysql.connector.Error as exc:
            self.teachers = []
            self.teacher_load_error = str(exc)

    def _read_attendance(self, teacher_id, year):
        """Read actual attendance events, including records for inactive teachers."""
        start = datetime(year, 1, 1).date()
        end = datetime(year, 12, 31).date()
        rows = data_flow_controle.get_attendance_records(teacher_id, start, end)
        return [
            {
                "name": str(row["name"] or "").strip(),
                "id": str(row["teacher_id"]).strip(),
                "status": str(row["attendance_status"] or "present").title(),
                "date": row["attendance_date"],
                "time": data_flow_controle.format_attendance_time(
                    row["attendance_time"]
                ),
                "source": "recorded",
            }
            for row in rows
        ]

    def reg_file_details(self, id_no):
        for teacher in self.teachers:
            if teacher["id"] == str(id_no).strip():
                return teacher["registration_date"]
        return None

    # ---------- Styling and layout ----------
    def _configure_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(
            "History.Treeview",
            background=self.PANEL, foreground=self.TEXT, fieldbackground=self.PANEL,
            rowheight=27, borderwidth=0, font=("Segoe UI", 10),
        )
        style.configure(
            "History.Treeview.Heading",
            background="#1a4e6b", foreground="white",
            font=("Segoe UI", 10, "bold"), padding=(8, 9), relief="flat",
        )
        style.map("History.Treeview", background=[("selected", self.BLUE)], foreground=[("selected", "white")])
        style.configure(
            "History.TCombobox", padding=6, font=("Segoe UI", 10),
            fieldbackground="white", background=self.PANEL_LIGHT,
        )
        style.map("History.TCombobox", fieldbackground=[("readonly", "white")])
        style.configure(
            "History.TCheckbutton",
            background=self.BG,
            foreground=self.TEXT,
            font=("Segoe UI", 9),
        )
        style.map(
            "History.TCheckbutton",
            background=[("active", self.PANEL_LIGHT)],
            foreground=[("active", self.TEXT)],
        )

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=0)
        self.rowconfigure(3, weight=1)
        self.rowconfigure(4, weight=0)

        Label(
            self, text="Teacher Attendance Record", font=("Arial Black", 28),
            bg=self.BG, fg="#F9F9F9",
        ).grid(row=0, column=0, pady=(22, 8))

        actions = Frame(self, bg=self.BG)
        actions.grid(row=1, column=0, pady=(0, 12))
        self._action_button(actions, "Print Report", self._print_report).pack(side=LEFT, padx=6)
        self._action_button(actions, "Export CSV", self._export_csv).pack(side=LEFT, padx=6)
        self._action_button(actions, "Export Excel", self._export_excel).pack(side=LEFT, padx=6)
        self._action_button(actions, "Print Full Report", self._print_full_report).pack(side=LEFT, padx=6)

        filter_panel = Frame(self, bg=self.BG, padx=12, pady=10, highlightthickness=1,
                             highlightbackground="#1a4e6b")
        filter_panel.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))
        filter_panel.columnconfigure(0, weight=1)
        filter_panel.columnconfigure(1, weight=1)
        filter_panel.columnconfigure(2, weight=1)
        filter_panel.columnconfigure(3, weight=1)

        left = Frame(filter_panel, bg=self.BG)
        left.grid(row=0, column=0, sticky="nsew", padx="0 12")
        Label(left, text="Search Teacher by Name or ID", bg=self.BG, fg="#F9F9F9",
              font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.id_no = Entry(left, textvariable=self.name_var, font=("Segoe UI", 10),
                           relief="solid", bd=1)
        self.id_no.pack(fill=X, ipady=7, pady="4 5")
        self.id_no.bind("<KeyRelease>", self._on_search)
        list_frame = Frame(left, bg=self.BG)
        list_frame.pack(fill=X)
        self.name_list_box = Listbox(list_frame, height=6, font=("Segoe UI", 9), bd=0,
                                     activestyle="dotbox", selectbackground=self.BLUE,
                                     selectforeground="white", exportselection=False)
        name_scroll = Scrollbar(list_frame, orient=VERTICAL, command=self.name_list_box.yview)
        self.name_list_box.configure(yscrollcommand=name_scroll.set)
        self.name_list_box.pack(side=LEFT, fill=X, expand=True)
        name_scroll.pack(side=RIGHT, fill=Y)
        self.name_list_box.bind("<<ListboxSelect>>", self._select_teacher)

        # Excluded days of week (below the teacher list box)
        excl_frame = Frame(left, bg=self.BG)
        excl_frame.pack(fill=X, pady=(10, 0))
        self._filter_label(excl_frame, "Exclude Days of Week:", 0, 0)
        self.excluded_day_vars = {}
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, dname in enumerate(day_names):
            var = BooleanVar(value=False)
            self.excluded_day_vars[i] = var
            cb = ttk.Checkbutton(
                excl_frame,
                text=dname,
                variable=var,
                style="History.TCheckbutton",
                command=self._on_excluded_day_toggled,
            )
            cb.grid(row=0, column=i + 1, sticky="w", padx=(6, 6), pady=2)

        # Restore saved excluded days into checkbox states
        for weekday_int, var in self.excluded_day_vars.items():
            var.set(weekday_int in self.excluded_days)

        profile = Frame(filter_panel, bg=self.PANEL, padx=12, pady=10, highlightthickness=1,
                        highlightbackground="#1a4e6b")
        profile.grid(row=0, column=1, sticky="nsew", padx="0 12")
        self.profile_name = Label(profile, text="No teacher selected", bg=self.PANEL, fg="#F9F9F9",
                                  font=("Segoe UI", 15, "bold"), anchor="w")
        self.profile_name.pack(fill=X, pady="2 5")
        self.profile_status = Label(
            profile, text="●  Select a teacher", bg=self.PANEL, fg=self.MUTED,
            font=("Segoe UI", 10, "bold"), anchor="w",
        )
        self.profile_status.pack(fill=X, pady=(0, 5))
        self.profile_details = Label(profile, text="Choose a teacher from the search list.",
                                     bg=self.PANEL, fg=self.MUTED, font=("Segoe UI", 10), anchor="w",
                                     justify=LEFT)
        self.profile_details.pack(fill=X)

        filters = Frame(filter_panel, bg=self.BG)
        filters.grid(row=0, column=2, sticky="nsew")
        filters.columnconfigure((0, 1), weight=1)
        # Row configuration for filters
        filters.rowconfigure(0, weight=0)
        filters.rowconfigure(1, weight=0)
        filters.rowconfigure(2, weight=0)
        filters.rowconfigure(3, weight=1)
        filters.rowconfigure(4, weight=0)
        self._filter_label(filters, "Academic Year", 0, 0)
        self.academic_year_title = Label(filters, text=f"Academic Year: {self.academic_year}",
                                         bg=self.BG, fg="#F9F9F9", font=("Segoe UI", 10, "bold"))
        self.academic_year_title.grid(row=1, column=0, sticky="ew", padx="0 8", pady="3 8")
        self._filter_label(filters, "Record type", 0, 1)
        self.type_combo = ttk.Combobox(filters, textvariable=self.record_type_var,
                                       values=["All Records", "Present", "Absent", "Estimated Absence"],
                                       state="readonly", style="History.TCombobox")
        self.type_combo.grid(row=1, column=1, sticky="ew", pady="3 8")
        self.type_combo.bind("<<ComboboxSelected>>", lambda _e: self._refresh_tables())
        # From Date field
        self._filter_label(filters, "From Date (MM/DD/YYYY)", 2, 0)
        self.from_field = Frame(filters)
        self.from_field.grid(row=3, column=0, sticky="nsew", padx="0 8", pady="3 8")
        self.from_var_entry = Entry(self.from_field, textvariable=self.from_var,
                                     font=("Segoe UI", 10), bd=1, relief="solid")
        self.from_var_entry.pack(side="left", fill="x", expand=True, padx=(0, 6), pady=5)
        self.cal_icon_from = self._create_calendar_icon()
        Button(self.from_field, image=self.cal_icon_from, command=lambda: self._open_calendar(self.from_var),
               bg="white", relief=FLAT, cursor="hand2").pack(side="right", padx=(0, 0), pady=5)
        # To Date field
        self._filter_label(filters, "To Date (MM/DD/YYYY)", 2, 1)
        self.to_field = Frame(filters)
        self.to_field.grid(row=3, column=1, sticky="nsew", pady=8)
        self.to_var_entry = Entry(self.to_field, textvariable=self.to_var,
                                   font=("Segoe UI", 10), bd=1, relief="solid")
        self.to_var_entry.pack(side="left", fill="x", expand=True, padx=(0, 6), pady=5)
        self.cal_icon_to = self._create_calendar_icon()
        Button(self.to_field, image=self.cal_icon_to, command=lambda: self._open_calendar(self.to_var),
               bg="white", relief=FLAT, cursor="hand2").pack(side="right", padx=(0, 0), pady=5)
        # Refresh button at row 4 spanning both columns
        self._action_button(filters, "↻ Refresh", self._refresh_history).grid(
            row=4, column=0, columnspan=2, sticky="ew", padx=8, pady=(10, 0))

        body = Frame(self, bg=self.BG, padx=14, pady=10)
        body.grid(row=3, column=0, sticky="nsew")
        body.columnconfigure(0, weight=11, uniform="panels")
        body.columnconfigure(1, weight=10, uniform="panels")
        body.rowconfigure(1, weight=1)

        cards = Frame(body, bg=self.BG)
        cards.grid(row=0, column=0, columnspan=2, sticky="ew", pady="0 12")
        for i in range(3):
            cards.columnconfigure(i, weight=1)
        self.present_card = self._metric_card(cards, 0, "Total Present Days", "0", self.GREEN)
        self.absent_card = self._metric_card(cards, 1, "Total Absent Days", "0", self.RED)
        self.days_card = self._metric_card(cards, 2, "Total Days From Joining", "0", self.BLUE)

        daily_panel = self._panel(body, "Daily Attendance Details")
        daily_panel.grid(row=1, column=0, sticky="nsew", padx="0 8")
        daily_panel.rowconfigure(1, weight=1)
        daily_panel.columnconfigure(0, weight=1)
        columns = ("no", "date", "day", "status", "time")
        self.table = ttk.Treeview(daily_panel, columns=columns, show="headings",
                                  style="History.Treeview", height=16)
        for key, label, width in [
            ("no", "No.", 48), ("date", "Date", 110), ("day", "Day", 105),
            ("status", "Status", 125), ("time", "Time", 90),
        ]:
            self.table.heading(key, text=label)
            self.table.column(key, width=width, minwidth=45, anchor="center" if key != "status" else "w")
        daily_scroll = ttk.Scrollbar(daily_panel, orient=VERTICAL, command=self.table.yview)
        self.table.configure(yscrollcommand=daily_scroll.set)
        self.table.grid(row=1, column=0, sticky="nsew", padx="10 0", pady="0 8")
        daily_scroll.grid(row=1, column=1, sticky="ns", padx="0 10", pady="0 8")
        self.table.tag_configure("present", foreground="#46e3b0")
        self.table.tag_configure("absent", foreground="#ff7183")
        self.table.tag_configure("estimated", foreground="#ffcf70")
        self.table.tag_configure("excluded", foreground="#9aa5b1")
        self.daily_footer = Label(daily_panel, text="Showing 0 records", bg=self.PANEL,
                                  fg=self.MUTED, font=("Segoe UI", 9), anchor="w")
        self.daily_footer.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady="0 9")

        summary_panel = self._panel(body, "Monthly Wise Summary")
        summary_panel.grid(row=1, column=1, sticky="nsew", padx="8 0")
        summary_panel.rowconfigure(1, weight=1)
        summary_panel.columnconfigure(0, weight=1)
        mcols = ("month", "present", "absent", "rate")
        self.month_table = ttk.Treeview(summary_panel, columns=mcols, show="headings",
                                         style="History.Treeview", height=12)
        for key, label, width in [
            ("month", "Month", 90), ("present", "Present Days", 105),
            ("absent", "Absent Days*", 105), ("rate", "Attendance Rate", 120),
        ]:
            self.month_table.heading(key, text=label)
            self.month_table.column(key, width=width, anchor="center")
        month_scroll = ttk.Scrollbar(summary_panel, orient=VERTICAL, command=self.month_table.yview)
        self.month_table.configure(yscrollcommand=month_scroll.set)
        self.month_table.grid(row=1, column=0, sticky="nsew", padx=10, pady="0 8")
        month_scroll.grid(row=1, column=1, sticky="ns", padx="0 10", pady="0 8")
        totals = Frame(summary_panel, bg=self.PANEL, padx=10, pady=10)
        totals.grid(row=2, column=0, sticky="ew", padx=10, pady="0 10")
        for i in range(4):
            totals.columnconfigure(i, weight=1)
        self.total_labels = []
        for i, (label, value) in enumerate([
            ("Months", "0"), ("Present", "0"), ("Absent*", "0"), ("Attendance Rate", "0%"),
        ]):
            cell = Frame(totals, bg=self.PANEL)
            cell.grid(row=0, column=i, sticky="ew", padx=3)
            Label(cell, text=label, bg=self.PANEL, fg=self.MUTED,
                  font=("Segoe UI", 8)).pack()
            val = Label(cell, text=value, bg=self.PANEL, fg="white",
                        font=("Segoe UI", 13, "bold"))
            val.pack(pady="4 0")
            self.total_labels.append(val)

        Label(self, textvariable=self.status_var, bg=self.PANEL, fg=self.MUTED,
              font=("Segoe UI", 9), anchor="w", padx=14, pady=5).grid(row=4, column=0, sticky="ew")

    def _action_button(self, parent, text, command):
        btn_img = resolve_path("Buttons", "Search button.png")
        btn = create_optional_image_button(
            parent, text, command, btn_img, bg=self.BG,
        )
        return btn

    def _filter_label(self, parent, text, row, col):
        Label(parent, text=text, bg=self.BG, fg="#F9F9F9",
              font=("Segoe UI", 9, "bold")).grid(row=row, column=col, sticky="w")

    def _metric_card(self, parent, column, title, value, color):
        frame = Frame(parent, bg=self.PANEL, highlightthickness=1, highlightbackground="#1a4e6b",
                      padx=16, pady=12)
        frame.grid(row=0, column=column, sticky="ew", padx=("0 6" if column == 0 else "6 6"))
        Label(frame, text=title, bg=self.PANEL, fg=self.TEXT,
              font=("Segoe UI", 10, "bold")).pack(anchor="w")
        label = Label(frame, text=value, bg=self.PANEL, fg=color,
                      font=("Segoe UI", 21, "bold"))
        label.pack(anchor="w", pady="4 0")
        return label

    def _panel(self, parent, title):
        panel = Frame(parent, bg=self.PANEL, highlightthickness=1, highlightbackground="#1a4e6b")
        Label(panel, text="▦  " + title, bg=self.PANEL, fg="white",
              font=("Segoe UI", 12, "bold"), anchor="w", padx=12, pady=10).grid(
                  row=0, column=0, columnspan=2, sticky="ew")
        return panel

    # ---------- Search and selection ----------
    def _populate_teacher_list(self, filtered=None):
        self.name_list_box.delete(0, END)
        candidates = self.teachers if filtered is None else filtered
        for teacher in candidates:
            status = "Active" if teacher["account_status"] == "Active" else "Deactivated"
            self.name_list_box.insert(END, f'{teacher["id"]} - {teacher["name"]} [{status}]')

    def _on_search(self, _event=None):
        query = self.name_var.get().strip().lower()
        filtered = [
            teacher for teacher in self.teachers
            if query in teacher["name"].lower() or query in str(teacher["id"])
        ] if query else self.teachers
        self._populate_teacher_list(filtered)

    def _select_teacher(self, _event=None):
        require_authenticated_parent(self)
        selection = self.name_list_box.curselection()
        if not selection:
            return
        display = self.name_list_box.get(selection[0])
        teacher_id = self._safe_int(display.split(" - ", 1)[0])
        teacher = next((item for item in self.teachers if item["id"] == teacher_id), None)
        if not teacher:
            return
        self.selected_teacher = teacher
        self.name_var.set(f'{teacher["id"]} - {teacher["name"]}')
        self._update_teacher_profile()
        self._refresh_history()

    def _update_teacher_profile(self):
        if not self.selected_teacher:
            return
        teacher = self.selected_teacher
        reg = teacher["registration_date"].strftime("%d/%m/%Y") if teacher["registration_date"] else "Not available"
        details = f'ID no: {teacher["id"]}     Registration: {reg}'
        if teacher["subject"]:
            details += f'\nSubject: {teacher["subject"]}'
        self.profile_name.configure(text=teacher["name"])
        self.profile_details.configure(text=details)
        if teacher["account_status"] == "Active":
            self.profile_status.configure(text="●  ACTIVE — eligible for attendance", fg="#46e3b0")
        else:
            self.profile_status.configure(text="●  DEACTIVATED — historical records remain available", fg="#ff9aa8")

    def refresh_teacher_status(self):
        """Reload account status after it changes in the management window."""
        selected_id = self.selected_teacher["id"] if self.selected_teacher else None
        self._load_teachers()
        self._on_search()
        if selected_id is None:
            return
        teacher = next((item for item in self.teachers if item["id"] == selected_id), None)
        if teacher is None:
            return
        self.selected_teacher = teacher
        self._update_teacher_profile()
        self._refresh_history()

    def refresh_teacher_information(self, updated_teacher):
        selected_pk = (
            self.selected_teacher.get("teacher_pk")
            if self.selected_teacher is not None else None
        )
        self._load_teachers()
        if selected_pk != updated_teacher["teacher_pk"]:
            self._populate_teacher_list()
            return
        teacher = next(
            (item for item in self.teachers if item["teacher_pk"] == selected_pk),
            None,
        )
        if teacher is None:
            self.selected_teacher = None
            self._populate_teacher_list()
            self._refresh_history()
            return
        self.selected_teacher = teacher
        self.name_var.set(f'{teacher["id"]} - {teacher["name"]}')
        self._populate_teacher_list()
        self._update_teacher_profile()
        self._refresh_history()

    def fill_entry(self, event=None):
        self._select_teacher(event)

    def check(self, event=None):
        self._on_search(event)

    def get_update(self, data):
        self._populate_teacher_list()

    def take_registration(self):
        self._load_teachers()
        self._populate_teacher_list()

    def binding_key_list(self):
        self.name_list_box.bind("<<ListboxSelect>>", self._select_teacher)
        self.id_no.bind("<KeyRelease>", self._on_search)

    # ---------- Calculations and refresh ----------
    def _date_filter(self):
        """Validate From/To dates strictly in MM/DD/YYYY format.

        Returns (start, end) as date objects, or (None, None) if either
        field has an invalid user-entered value.
        Empty fields are allowed (None) and default to year boundaries.
        """
        from_val = self.from_var.get().strip()
        to_val = self.to_var.get().strip()

        start = None
        end = None

        if from_val:
            start = self._validate_date_string(from_val)
            if start is None:
                return None, None  # Invalid user input
        if to_val:
            end = self._validate_date_string(to_val)
            if end is None:
                return None, None  # Invalid user input

        return start, end

    def _make_display_records(self):
        if not self.selected_teacher:
            return []
        year = self.academic_year_start
        recorded = self._read_attendance(self.selected_teacher["id"], year)
        self.attendance_records = recorded
        start, end = self._date_filter()
        # Block if user entered invalid dates (validation already showed warning)
        if (self.from_var.get().strip() or self.to_var.get().strip()) and start is None and end is None:
            return []
        if start is None:
            start = datetime(year, 1, 1).date()
        if end is None:
            end = datetime(year, 12, 31).date()
        # End date logic:
        # Default = current system date (always cap at current date to avoid future dates)
        # If user set a To Date, use it instead (but still capped at current date)
        # The last attendance date is NOT used as a cap anymore - we calculate through the
        # current date so missing recent dates are evaluated as Absent, not skipped.
        current_date = datetime.now().date()
        registration = self.selected_teacher.get("registration_date")
        start = max(start, registration) if registration else start
        end = min(end, datetime(year, 12, 31).date(), current_date)
        if start > end:
            return []

        by_date = {}
        for record in recorded:
            by_date.setdefault(record["date"], record)

        # Every calendar date within the reporting period must appear in the table.
        # Excluded weekdays are shown as "Excluded" (not Absent).
        # Non-excluded weekdays without a recorded attendance are shown as "Estimated Absence".
        # Saturday and Sunday are treated exactly like other weekdays:
        # they are eligible unless explicitly excluded by the user via checkboxes.
        result = []
        day = start
        from datetime import timedelta
        while day <= end:
            weekday_int = day.weekday()
            record = by_date.get(day)
            if record:
                result.append(record)
            elif self._is_excluded_day(weekday_int):
                result.append({
                    "name": self.selected_teacher["name"],
                    "id": self.selected_teacher["id"],
                    "status": "Excluded",
                    "date": day,
                    "time": "",
                    "source": "excluded",
                })
            else:
                result.append({
                    "name": self.selected_teacher["name"],
                    "id": self.selected_teacher["id"],
                    "status": "Estimated Absence",
                    "date": day,
                    "time": "",
                    "source": "estimated",
                })
            day += timedelta(days=1)
        kind = self.record_type_var.get()
        if kind == "Present":
            result = [r for r in result if r["status"].lower() == "present"]
        elif kind == "Absent":
            # "Absent" includes both explicitly recorded absences and estimated weekday absences.
            result = [
                r for r in result
                if r["status"].lower() == "absent" or r["status"] == "Estimated Absence"
            ]
        elif kind == "Estimated Absence":
            result = [r for r in result if r["status"] == "Estimated Absence"]
        return result

    def _refresh_history(self):
        if not self.selected_teacher:
            if self.teacher_load_error:
                self.status_var.set(
                    f"Could not load teachers from MySQL: {self.teacher_load_error}"
                )
            elif self.teachers:
                self.status_var.set("Select a teacher from the search list to load their history.")
            else:
                self.status_var.set("No registered teachers were found in MySQL.")
            self._clear_tables()
            return
        try:
            self.filtered_records = self._make_display_records()
        except mysql.connector.Error as exc:
            self.attendance_records = []
            self.filtered_records = []
            self._clear_tables()
            self.status_var.set(f"Could not load attendance history from MySQL: {exc}")
            return
        self._refresh_tables()

    def _refresh_tables(self):
        if not self.selected_teacher:
            return
        if not self.attendance_records:
            self.attendance_records = self._read_attendance(
                self.selected_teacher["id"], self.academic_year_start
            )
        self.filtered_records = self._make_display_records()
        if self.table is not None:
            self.table.delete(*self.table.get_children())
        for index, record in enumerate(self.filtered_records, 1):
            date = record["date"]
            status = record["status"]
            if status.lower() == "present":
                tag = "present"
            elif status == "Estimated Absence":
                tag = "estimated"
            elif status == "Excluded":
                tag = "excluded"
            else:
                tag = "absent"
            self.table.insert("", END, values=(
                index, date.strftime("%d-%m-%Y"), date.strftime("%A"), status, record.get("time", "")
            ), tags=(tag,))
        self.daily_footer.configure(text=f"Showing {len(self.filtered_records)} records")
        self._update_summary()
        excluded_note = ""
        if self.excluded_days:
            day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            excluded = ", ".join(day_names[d] for d in sorted(self.excluded_days))
            excluded_note = f" Excluded weekdays: {excluded}."
        self.status_var.set(
            "Green = recorded present. Amber = estimated weekday absence."
            + excluded_note
            + " Excluded weekdays are not counted as working days or absences."
            " All non-excluded weekdays (including Sat/Sun) are eligible for attendance."
            " School holidays/closures are not available in the source files."
        )

    def _clear_tables(self):
        if self.table:
            self.table.delete(*self.table.get_children())
        if self.month_table:
            self.month_table.delete(*self.month_table.get_children())
        self.present_card.configure(text="0")
        self.absent_card.configure(text="0")
        self.days_card.configure(text="0")
        self.daily_footer.configure(text="Showing 0 records")
        for label in getattr(self, "total_labels", []):
            label.configure(text="0")

    def _update_summary(self):
        year = self.academic_year_start
        start, end = self._date_filter()
        # Block if user entered invalid dates (validation already showed warning)
        if (self.from_var.get().strip() or self.to_var.get().strip()) and start is None and end is None:
            return []
        if start is None:
            start = datetime(year, 1, 1).date()
        if end is None:
            end = datetime(year, 12, 31).date()
        registration = self.selected_teacher.get("registration_date") if self.selected_teacher else None
        if registration:
            start = max(start, registration)
        # Find the last attendance date for this teacher
        source_records = self.attendance_records
        # The end date is capped at the current date only - NOT at the last attendance date
        # We calculate through the current date so missing recent dates are evaluated
        end = min(end, datetime(year, 12, 31).date(), datetime.now().date())
        recorded_present = {r["date"] for r in source_records if r["status"].lower() == "present"}
        total_present = 0
        total_estimated = 0
        active_months = 0
        self.month_table.delete(*self.month_table.get_children())
        from datetime import timedelta
        for month_name, month_num in self.MONTHS:
            month_start = datetime(year, month_num, 1).date()
            if month_num == 12:
                month_end = datetime(year, 12, 31).date()
            else:
                month_end = datetime(year, month_num + 1, 1).date() - timedelta(days=1)
            period_start = max(month_start, start)
            period_end = min(month_end, end)
            if period_start > period_end:
                self.month_table.insert("", END, values=(month_name, "—", "—", "—"))
                continue
            # Eligible working days = all non-excluded weekdays (Mon-Sun).
            # Excluded weekdays (set via checkboxes) are not counted.
            weekdays = 0
            day = period_start
            while day <= period_end:
                if not self._is_excluded_day(day.weekday()):
                    weekdays += 1
                day += timedelta(days=1)
            present = sum(
                1
                for d in recorded_present
                if period_start <= d <= period_end
                and not self._is_excluded_day(d.weekday())
            )
            estimated_absent = max(0, weekdays - present)
            rate = round((present / weekdays) * 100, 1) if weekdays else 0
            total_present += present
            total_estimated += estimated_absent
            active_months += 1
            self.month_table.insert("", END, values=(
                month_name, present, estimated_absent, f"{rate:.1f}%"
            ))
        # Total Days From Joining = ALL calendar days from registration through the
        # applicable final attendance date (inclusive). Weekends and excluded weekdays
        # are NOT removed from this calendar-day total.
        period_days = 0
        day = start
        while day <= end:
            period_days += 1
            day += timedelta(days=1)
        rate = round(total_present / (total_present + total_estimated) * 100, 1) if total_present + total_estimated else 0
        self.present_card.configure(text=str(total_present))
        self.absent_card.configure(text=str(total_estimated))
        self.days_card.configure(text=str(period_days))
        values = [str(active_months), str(total_present), str(total_estimated), f"{rate:.1f}%"]
        for label, value in zip(self.total_labels, values):
            label.configure(text=value)

    # ---------- Export / print ----------
    def _export_rows(self, full=False):
        if not self.selected_teacher:
            from tkinter import messagebox
            messagebox.showwarning("Select teacher", "Please select a teacher first.", parent=self)
            return []
        if full:
            current_type = self.record_type_var.get()
            self.record_type_var.set("All Records")
            rows = self._make_display_records()
            self.record_type_var.set(current_type)
            return rows
        return list(self.filtered_records)

    def _export_csv(self):
        from tkinter import filedialog, messagebox
        import csv
        rows = self._export_rows()
        if not rows:
            messagebox.showinfo("No records", "There are no rows to export.", parent=self)
            return
        filename = filedialog.asksaveasfilename(
            parent=self, title="Export attendance CSV", defaultextension=".csv",
            filetypes=[("CSV file", "*.csv")],
            initialfile=f"attendance_{self.selected_teacher['id']}_{self.academic_year_start}.csv",
        )
        if not filename:
            return
        try:
            with open(filename, "w", newline="", encoding="utf-8-sig") as handle:
                writer = csv.writer(handle)
                writer.writerow(["Teacher", self.selected_teacher["name"], "ID", self.selected_teacher["id"]])
                writer.writerow(["No.", "Date", "Day", "Status", "Time"])
                for i, row in enumerate(rows, 1):
                    writer.writerow([i, row["date"].strftime("%d-%m-%Y"),
                                     row["date"].strftime("%A"), row["status"], row.get("time", "")])
            messagebox.showinfo("Export complete", f"CSV saved to:\n{filename}", parent=self)
        except Exception as exc:
            messagebox.showerror("Export failed", str(exc), parent=self)

    def _export_excel(self):
        from tkinter import filedialog, messagebox
        rows = self._export_rows()
        if not rows:
            messagebox.showinfo("No records", "There are no rows to export.", parent=self)
            return
        filename = filedialog.asksaveasfilename(
            parent=self, title="Export attendance Excel", defaultextension=".xlsx",
            filetypes=[("Excel workbook", "*.xlsx")],
            initialfile=f"attendance_{self.selected_teacher['id']}_{self.academic_year_start}.xlsx",
        )
        if not filename:
            return
        try:
            workbook = openpyxl.Workbook()
            sheet = workbook.active
            sheet.title = "Daily Attendance"
            sheet.append(["Teacher", self.selected_teacher["name"]])
            sheet.append(["Teacher ID", self.selected_teacher["id"]])
            sheet.append(["Academic Year", self.academic_year])
            sheet.append([])
            sheet.append(["No.", "Date", "Day", "Status", "Time"])
            for i, row in enumerate(rows, 1):
                sheet.append([i, row["date"].strftime("%d-%m-%Y"), row["date"].strftime("%A"),
                              row["status"], row.get("time", "")])
            summary = workbook.create_sheet("Monthly Summary")
            summary.append(["Month", "Present Days", "Estimated Absence*", "Attendance Rate"])
            for item in self.month_table.get_children():
                summary.append(list(self.month_table.item(item, "values")))
            for ws in workbook.worksheets:
                ws.freeze_panes = "A5"
                for col in ws.columns:
                    letter = col[0].column_letter
                    width = max((len(str(cell.value or "")) for cell in col), default=10)
                    ws.column_dimensions[letter].width = min(max(width + 2, 12), 34)
            workbook.save(filename)
            workbook.close()
            messagebox.showinfo("Export complete", f"Excel report saved to:\n{filename}", parent=self)
        except Exception as exc:
            messagebox.showerror("Export failed", str(exc), parent=self)

    def _build_print_html(self, rows, full=False):
        import html
        teacher = self.selected_teacher
        summary_rows = []
        for item in self.month_table.get_children():
            vals = self.month_table.item(item, "values")
            summary_rows.append("<tr>" + "".join(f"<td>{html.escape(str(v))}</td>" for v in vals) + "</tr>")
        daily_rows = []
        for i, row in enumerate(rows, 1):
            daily_rows.append(
                "<tr>" + "".join(f"<td>{html.escape(str(v))}</td>" for v in (
                    i, row["date"].strftime("%d-%m-%Y"), row["date"].strftime("%A"),
                    row["status"], row.get("time", "")
                )) + "</tr>"
            )
        title = "Full Teacher Attendance Report" if full else "Teacher Attendance Report"
        return f"""<!doctype html><html><head><meta charset="utf-8"><title>{title}</title>
        <style>body{{font-family:Arial,sans-serif;color:#14263b;margin:28px}}h1{{color:#0758b5}}
        .meta{{padding:12px;background:#edf5ff;margin-bottom:18px}}table{{border-collapse:collapse;width:100%;margin:10px 0 22px}}
        th{{background:#123f70;color:white}}th,td{{border:1px solid #b9c9da;padding:7px;text-align:left;font-size:12px}}
        .note{{font-size:11px;color:#555}}@media print{{button{{display:none}}}}</style></head><body>
        <h1>{title}</h1><div class="meta"><b>Teacher:</b> {html.escape(teacher["name"])}
        &nbsp; <b>ID:</b> {teacher["id"]} &nbsp; <b>Academic year:</b> {self.academic_year}</div>
        <h2>Daily Attendance Details</h2><table><thead><tr><th>No.</th><th>Date</th><th>Day</th><th>Status</th><th>Time</th></tr></thead>
        <tbody>{''.join(daily_rows)}</tbody></table>
        <h2>Monthly Summary</h2><table><thead><tr><th>Month</th><th>Present Days</th><th>Estimated Absence*</th><th>Attendance Rate</th></tr></thead>
        <tbody>{''.join(summary_rows)}</tbody></table>
        <p class="note">* Absence is estimated from weekdays without a recorded attendance event. Excluded weekdays are not counted as working days or absences. The source project does not contain a school holiday calendar or explicit absent records, so estimated absences must be verified before official use.</p>
        <button onclick="window.print()">Print</button></body></html>"""

    def _print_report(self):
        self._print(full=False)

    def _print_full_report(self):
        self._print(full=True)

    def _print(self, full=False):
        from tkinter import messagebox
        import os
        import tempfile
        rows = self._export_rows(full=full)
        if not rows:
            messagebox.showinfo("No records", "There are no rows to print.", parent=self)
            return
        try:
            html_report = self._build_print_html(rows, full=full)
            fd, filename = tempfile.mkstemp(prefix="teacher_attendance_", suffix=".html")
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(html_report)
            # Opening the report lets the user print from the browser; don't silently send
            # anything to a printer or depend on a PDF library.
            os.startfile(filename)
            messagebox.showinfo(
                "Print report",
                "The report has opened in your default browser. Use Ctrl+P to print it.",
                parent=self,
            )
        except Exception as exc:
            messagebox.showerror("Print failed", str(exc), parent=self)

    # Backwards-compatible method names used by the original application.
    def check_result(self):
        self._refresh_history()

    def data_table(self):
        pass

    def search_bar(self):
        pass

    def record_name_list(self):
        pass

    def run_history(self):
        # The complete interface is built in __init__ to keep the original caller working.
        self._populate_teacher_list()
        self._refresh_history()
