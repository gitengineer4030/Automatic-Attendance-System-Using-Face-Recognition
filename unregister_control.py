from tkinter import *
from tkinter import messagebox, ttk
import mysql.connector
import data_flow_controle
from data_flow_controle import resolve_path
from admin_auth import require_authenticated_parent
from main import create_optional_image_button


class Unregister_interface(Toplevel):
    def __init__(self, parent):
        require_authenticated_parent(parent)
        super().__init__(parent)
        self.auth_session = parent.auth_session
        self.geometry("760x620")
        self.minsize(width=700, height=540)
        self.title("Teacher Status Management")
        self.configure(bg="#2e7e99")
        self.reg_list = []
        self.visible_teachers = []
        self.status_filter_var = StringVar(value="All Teachers")
        self.message_var = StringVar(value="Select a teacher to edit information or manage status.")
        self.heading()
        self.sub_frames()
        self.search_bar()
        self.record_name_list()
        self.take_registration()
        self.binding_key_list()

    def heading(self):
        self.heading_of_registration = Label(self, text="Teacher Status Management",
                                             font=("Arial Black", 25), bg="#2e7e99", fg="#F9F9F9")
        self.heading_of_registration.pack()

    def sub_frames(self):
        self.main_sub_frame = Frame(self, bg="#2e7e99", padx=24, pady=14)
        self.main_sub_frame.pack(fill=BOTH, expand=True)

    def search_bar(self):
        search_bar_frame = Frame(self.main_sub_frame, bg="#2e7e99")
        search_bar_frame.pack(fill=X, pady=(0, 10))
        Label(search_bar_frame, bg="#2e7e99", text="Search by name or ID",
              font=("Arial Black", 10), fg="white").pack(anchor="w")
        self.id_no = Entry(search_bar_frame, width=35, font=("Arial Black", 11),
                           bg="white", relief="solid", bd=1)
        self.id_no.pack(fill=X, ipady=6, pady=(4, 10))

        filter_row = Frame(search_bar_frame, bg="#2e7e99")
        filter_row.pack(fill=X)
        Label(filter_row, bg="#2e7e99", text="Show:",
              font=("Arial Black", 10), fg="white").pack(side=LEFT, padx=(0, 8))
        self.status_filter = ttk.Combobox(
            filter_row, textvariable=self.status_filter_var,
            values=("All Teachers", "Active Teachers", "Deactivated Teachers"),
            state="readonly", width=24,
        )
        self.status_filter.pack(side=LEFT)
        self.status_filter.bind("<<ComboboxSelected>>", self._refresh_teacher_list)
        btn_img = resolve_path("Buttons", "Search button.png")
        self.edit_button = create_optional_image_button(
            filter_row, "Edit Information", self.open_edit_teacher, btn_img,
            width=190, height=48, state=DISABLED,
        )
        self.edit_button.pack(side=RIGHT, padx=(0, 8))
        self.toggle_button = create_optional_image_button(
            filter_row, "Select a teacher", self.remove_registration_data,
            btn_img, width=190, height=48, state=DISABLED,
        )
        self.toggle_button.pack(side=RIGHT)

    def remove_registration_data(self):
        require_authenticated_parent(self)
        selected_id = self.id_no.get().strip()
        if not selected_id:
            messagebox.showinfo("Select a teacher", "Select a teacher from the list or enter their ID.", parent=self)
            return
        try:
            teacher = data_flow_controle.get_teacher_by_id(selected_id)
        except mysql.connector.Error as exc:
            messagebox.showerror("Database error", f"Could not load teacher details:\n{exc}", parent=self)
            return
        if teacher is None:
            messagebox.showinfo("Teacher not found", f"No registered teacher was found with ID {selected_id}.", parent=self)
            return
        current_status = teacher["status"]
        if current_status == "Active":
            confirm_msg = "Are you sure you want to deactivate this teacher? Their registration information, photograph, face encoding, and complete attendance history will be preserved."
            action_text = "Deactivate"
            new_status = "Inactive"
        else:
            confirm_msg = "Are you sure you want to activate this teacher?"
            action_text = "Activate"
            new_status = "Active"

        check = messagebox.askyesno(f"{action_text} teacher?", confirm_msg, parent=self)
        if not check:
            return

        try:
            data_flow_controle.update_teacher_status(selected_id, new_status)
            self.take_registration(selected_id=selected_id)
        except (mysql.connector.Error, data_flow_controle.TeacherNotFoundError) as exc:
            messagebox.showerror(
                "Status update failed",
                f"The teacher status was not changed:\n{exc}",
                parent=self,
            )
            return
        self.message_var.set(
            f'{teacher["name"]} is now {new_status.lower()}. '
            "This window will remain open; the list has been updated."
        )
        self._notify_history_status_changed()

    def record_name_list(self):
        Label(self.main_sub_frame, text="Teachers", bg="#2e7e99", fg="white",
              font=("Arial Black", 11)).pack(anchor="w", pady=(12, 4))
        list_frame = Frame(self.main_sub_frame, bg="#2e7e99")
        list_frame.pack(fill=BOTH, expand=True)
        self.name_list_box = Listbox(
            list_frame, font=("Segoe UI", 11), height=12,
            activestyle="dotbox", selectbackground="#087cff",
            selectforeground="white", exportselection=False,
        )
        scroll = Scrollbar(list_frame, orient=VERTICAL, command=self.name_list_box.yview)
        self.name_list_box.configure(yscrollcommand=scroll.set)
        self.name_list_box.pack(side=LEFT, fill=BOTH, expand=True)
        scroll.pack(side=RIGHT, fill=Y)
        Label(self.main_sub_frame, textvariable=self.message_var, bg="#2e7e99",
              fg="#e7f7ff", font=("Segoe UI", 10), anchor="w").pack(fill=X, pady=(10, 0))

    def get_update(self, data):
        self.name_list_box.delete(0, END)
        for nameid in data:
            self.name_list_box.insert(END, nameid)

    def fill_entry(self, _event=None):
        selection = self.name_list_box.curselection()
        if not selection:
            return
        self.id_no.delete(0, END)
        text = self.name_list_box.get(selection[0])
        teacher_id = text.split(" | ", 1)[0]
        self.id_no.insert(0, teacher_id)
        teacher = next(
            (item for item in self.visible_teachers if str(item["id"]) == teacher_id),
            None,
        )
        if teacher:
            action = "Deactivate" if teacher["status"] == "Active" else "Activate"
            self.toggle_button.configure(text=f"{action} Teacher", state=NORMAL)
            self.edit_button.configure(state=NORMAL)
            self.message_var.set(f'{teacher["name"]} (ID {teacher["id"]}) is {teacher["status"]}.')

    def open_edit_teacher(self):
        require_authenticated_parent(self)
        selected_id = self.id_no.get().strip()
        if not selected_id:
            messagebox.showinfo(
                "Select a teacher",
                "Select a teacher from the list before editing.",
                parent=self,
            )
            return
        teacher = next(
            (item for item in self.visible_teachers if item["id"] == selected_id),
            None,
        )
        if teacher is None:
            messagebox.showinfo(
                "Teacher not found",
                "Select a registered teacher from the list.",
                parent=self,
            )
            return
        EditTeacherWindow(self, teacher["teacher_pk"])

    def _on_teacher_updated(self, teacher):
        self.id_no.delete(0, END)
        self._refresh_teacher_list()
        refreshed = self.take_registration(selected_id=teacher["teacher_id"])
        refresh_attendance = getattr(self.master, "refresh_attendance_display", None)
        if refresh_attendance:
            refresh_attendance()
        history_window = getattr(self.master, "history_window", None)
        if history_window is not None and history_window.winfo_exists():
            refresh = getattr(history_window, "refresh_teacher_information", None)
            if refresh:
                refresh(teacher)
        if refreshed:
            self.message_var.set(
                f'{teacher["name"]} (ID {teacher["teacher_id"]}) was updated successfully.'
            )

    def take_registration(self, selected_id=None):
        self.reg_list = []
        teachers = []
        try:
            rows = data_flow_controle.get_teachers()
        except mysql.connector.Error as exc:
            self.message_var.set(f"Could not load teachers from MySQL: {exc}")
            self.name_list_box.delete(0, END)
            self.visible_teachers = []
            return False
        for row in rows:
            teacher = {
                "teacher_pk": row["teacher_pk"],
                "id": str(row["teacher_id"]).strip(),
                "name": str(row["name"] or "Unknown").strip(),
                "status": row["status"],
            }
            teachers.append(teacher)
            display = (
                f'{teacher["id"]} | {teacher["name"]} | '
                f'{self._status_label(teacher["status"])}'
            )
            self.reg_list.append(display)
        self.visible_teachers = teachers
        self._refresh_teacher_list(selected_id=selected_id)
        return True

    @staticmethod
    def _status_label(status):
        return "Active" if status == "Active" else "Deactivated"

    def _refresh_teacher_list(self, _event=None, selected_id=None):
        query = self.id_no.get().strip().lower()
        filter_value = self.status_filter_var.get()
        teachers = [
            teacher for teacher in self.visible_teachers
            if (not query or query in teacher["name"].lower() or query in teacher["id"].lower())
            and (
                filter_value == "All Teachers"
                or (filter_value == "Active Teachers" and teacher["status"] == "Active")
                or (filter_value == "Deactivated Teachers" and teacher["status"] == "Inactive")
            )
        ]
        self.name_list_box.delete(0, END)
        for teacher in teachers:
            self.name_list_box.insert(
                END,
                f'{teacher["id"]} | {teacher["name"]} | {self._status_label(teacher["status"])}',
            )
        if selected_id is not None:
            for index, teacher in enumerate(teachers):
                if teacher["id"] == str(selected_id):
                    self.name_list_box.selection_set(index)
                    self.name_list_box.see(index)
                    self.fill_entry(None)
                    return
        self.toggle_button.configure(text="Select a teacher", state=DISABLED)
        self.edit_button.configure(state=DISABLED)

    def binding_key_list(self):
        self.name_list_box.bind("<<ListboxSelect>>", self.fill_entry)
        self.id_no.bind("<KeyRelease>", self._refresh_teacher_list)

    def _notify_history_status_changed(self):
        history_window = getattr(self.master, "history_window", None)
        if history_window is not None and history_window.winfo_exists():
            refresh = getattr(history_window, "refresh_teacher_status", None)
            if refresh:
                refresh()


class EditTeacherWindow(Toplevel):
    """Edit a teacher's database-backed information without changing identity links."""

    FIELD_LABELS = (
        ("name", "Teacher Name"),
        ("father_name", "Father Name"),
        ("teacher_id", "ID Number"),
        ("subject", "Subject"),
        ("phone_number", "Phone Number"),
    )

    def __init__(self, parent, teacher_pk):
        require_authenticated_parent(parent)
        super().__init__(parent)
        self.parent = parent
        self.teacher_pk = teacher_pk
        self.configure(bg="#2e7e99")
        self.title("Edit Teacher Information")
        self.geometry("620x520")
        self.resizable(False, False)
        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        try:
            teacher = data_flow_controle.get_teacher_by_pk(teacher_pk)
        except mysql.connector.Error as exc:
            messagebox.showerror(
                "Database error",
                f"Could not load teacher information:\n{exc}",
                parent=self,
            )
            self.destroy()
            return
        if teacher is None:
            messagebox.showerror(
                "Teacher not found",
                "This teacher record no longer exists.",
                parent=self,
            )
            self.destroy()
            return

        self.fields = {}
        self._build_form(teacher)
        self.grab_set()

    def _build_form(self, teacher):
        Label(
            self, text="Edit Teacher Information",
            font=("Arial Black", 20), bg="#2e7e99", fg="#F9F9F9",
        ).pack(pady=(18, 8))
        Label(
            self,
            text="Registration date and account status are read-only.",
            font=("Segoe UI", 10), bg="#2e7e99", fg="#e7f7ff",
        ).pack(pady=(0, 12))

        form = Frame(self, bg="#2e7e99")
        form.pack(padx=26, pady=4)
        for row, (field, label) in enumerate(self.FIELD_LABELS):
            Label(
                form, text=label, width=17, anchor="w",
                font=("Arial Black", 10), bg="#2e7e99", fg="white",
            ).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=7)
            entry = Entry(form, width=34, font=("Segoe UI", 11), bg="white")
            entry.grid(row=row, column=1, pady=7)
            entry.insert(0, str(teacher[field] or ""))
            self.fields[field] = entry

        registration_date = teacher["registration_date"]
        registration_text = (
            registration_date.strftime("%m/%d/%Y")
            if registration_date is not None else "Not available"
        )
        readonly_rows = (
            ("Registration Date", registration_text),
            ("Teacher Status", str(teacher["status"])),
        )
        for offset, (label, value) in enumerate(readonly_rows, start=len(self.FIELD_LABELS)):
            Label(
                form, text=label, width=17, anchor="w",
                font=("Arial Black", 10), bg="#2e7e99", fg="#d4eaf5",
            ).grid(row=offset, column=0, sticky="w", padx=(0, 12), pady=7)
            Label(
                form, text=value, width=34, anchor="w",
                font=("Segoe UI", 11), bg="#1f5d7e", fg="#d4eaf5",
                padx=6, pady=4,
            ).grid(row=offset, column=1, sticky="ew", pady=7)

        buttons = Frame(self, bg="#2e7e99")
        buttons.pack(pady=18)
        self.save_button = Button(
            buttons, text="Save Changes", width=16, command=self.save_changes,
            font=("Arial Black", 10), bg="#2e7e99", fg="white",
            activebackground="#2e7e99", activeforeground="#00ffff",
        )
        self.save_button.pack(side=LEFT, padx=10)
        Button(
            buttons, text="Cancel", width=16, command=self.destroy,
            font=("Arial Black", 10), bg="#2e7e99", fg="white",
            activebackground="#2e7e99", activeforeground="#00ffff",
        ).pack(side=LEFT, padx=10)

    def save_changes(self):
        require_authenticated_parent(self)
        teacher_data = {
            field: entry.get().strip()
            for field, entry in self.fields.items()
        }
        try:
            data_flow_controle.validate_teacher_information(teacher_data)
        except data_flow_controle.TeacherValidationError as exc:
            messagebox.showerror("Invalid teacher information", str(exc), parent=self)
            return

        if not messagebox.askyesno(
            "Confirm teacher update",
            "Save these changes to the selected teacher's record?\n\n"
            "The teacher's status, registration date, photo, face encoding, "
            "and attendance history will remain unchanged.",
            parent=self,
        ):
            return

        try:
            teacher = data_flow_controle.update_teacher_information(
                self.teacher_pk, teacher_data
            )
        except data_flow_controle.DuplicateTeacherError as exc:
            messagebox.showerror("Duplicate teacher ID", str(exc), parent=self)
            return
        except data_flow_controle.TeacherNotFoundError as exc:
            messagebox.showerror("Teacher not found", str(exc), parent=self)
            return
        except mysql.connector.Error as exc:
            messagebox.showerror(
                "Update failed",
                f"Teacher information was not updated:\n{exc}",
                parent=self,
            )
            return

        if teacher is None:
            messagebox.showerror("Update failed", "The updated teacher could not be reloaded.", parent=self)
            return
        messagebox.showinfo(
            "Teacher updated",
            f'{teacher["name"]} (ID {teacher["teacher_id"]}) was updated successfully.',
            parent=self,
        )
        self.parent._on_teacher_updated(teacher)
        self.destroy()
