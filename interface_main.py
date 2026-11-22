import threading
import cv2
import queue
from tkinter import *
import registration_control
import unregister_control
from multiprocessing import *
import main
import tkinter
from tkinter import ttk
from datetime import datetime
import history_interface
from tkinter import messagebox
from PIL import Image, ImageTk
import data_flow_controle
from data_flow_controle import resolve_path
import mysql.connector
from main import CAMERA_DISPLAY_SIZE, LatestFrameCapture, fit_camera_frame
from admin_auth import (
    AdminAccountWindow,
    AdminSession,
    AdminAuthenticationWindow,
    require_authenticated_parent,
)
##################################################################################################################################################
##################################################################################################################################################
class Caller_interface(Toplevel):
    def __init__(self, controller, auth_session):
        require_authenticated_parent(controller)
        if not isinstance(auth_session, AdminSession) or not auth_session.is_authenticated():
            raise PermissionError("Administrator authentication is required.")
        super().__init__(controller)
        self.controller = controller
        self.auth_session = auth_session
        self.startup_ok = True
        self.name = None
        self.dateandtime = None
        self.task_running = False
        self.ids_list = []
        self.label = None
        self.registration_window = None
        self.unregister_window = None
        self.history_window = None
        self.year = datetime.today().strftime("%Y")
        self._database_error_reported = False
        self.startup_ok = True
        self.create_options_menu()


    def create_options_menu(self):
        menubar = Menu(self)
        options_menu = Menu(menubar, tearoff=0)
        options_menu.add_command(label="Camera Settings", command=self.open_camera_settings)
        options_menu.add_command(
            label="Admin Account", command=self.open_admin_account
        )
        options_menu.add_separator()
        options_menu.add_command(label="Logout", command=self.logout)
        menubar.add_cascade(label="Options", menu=options_menu)
        self.config(menu=menubar)

    def open_camera_settings(self):
        require_authenticated_parent(self)
        CameraSettingsWindow(self)

    def on_close(self):
        self._stop_attendance_process()
        main.Attendance_taker(self.auth_session).date_time_saver()
        self.controller.close_application()

    def _stop_attendance_process(self):
        if self.task_running and getattr(self, "task1", None) is not None:
            if getattr(self, "attendance_stop_event", None) is not None:
                self.attendance_stop_event.set()
            self.task1.join(timeout=3)
            if self.task1.is_alive():
                self.task1.kill()
                self.task1.join(timeout=2)
            self.task_running = False

    def logout(self):
        require_authenticated_parent(self)
        self._stop_attendance_process()
        main.Attendance_taker(self.auth_session).date_time_saver()
        self.controller.logout(self, self.auth_session)

    def open_admin_account(self):
        require_authenticated_parent(self)
        AdminAccountWindow(self)

    def stop(self):
        require_authenticated_parent(self)
        self.start['state'] = NORMAL
        if getattr(self, "task1", None) is not None and self.task1.is_alive():
            if getattr(self, "attendance_stop_event", None) is not None:
                self.attendance_stop_event.set()
            self.task1.join(timeout=3)
            if self.task1.is_alive():
                self.task1.kill()
                self.task1.join(timeout=2)
        self.task_running = False
        self.stop.configure(state=DISABLED,bg="#2e7e99")
        Attendance_taker = main.Attendance_taker(self.auth_session)
        Attendance_taker.date_time_saver()

    def heading(self):
        head = Label(self,text="Automatic Attendance System",font=("Arial black",30),fg="#FFFFFF",bg="#2e7e99")
        head.pack(pady=30)

    def build_Table(self):
        tree_style = ttk.Style()
        tree_style.configure("Treeview",background="gray17",foreground="white")
        tree_style.configure("Treeview.Heading",font=("Arial black",10),background="gray17")
        tree_frame = Frame(self)
        tree_frame.pack()
        tree_scroll = Scrollbar(tree_frame)
        tree_scroll.pack(side=RIGHT, fill=Y)
        all_columns = ("name","id.no","Attendance",'date','time')
        self.data_tree=ttk.Treeview(tree_frame,show="headings",columns=all_columns,yscrollcommand=tree_scroll.set,height=20)
        tree_scroll.configure(command=self.data_tree.yview)
        self.data_tree.column('name',minwidth=120)
        self.data_tree.column("id.no",minwidth=80)
        self.data_tree.column("Attendance",minwidth=80)
        self.data_tree.column("date",minwidth=100)
        self.data_tree.column("time", minwidth=100)
        #Headings
        self.data_tree.heading('name',text="NAME",anchor=tkinter.W)
        self.data_tree.heading('id.no',text="ID.NO",anchor=tkinter.W)
        self.data_tree.heading("Attendance",text="Attendance",anchor=tkinter.W)
        self.data_tree.heading('date', text="DATE",anchor=tkinter.W)
        self.data_tree.heading('time', text="TIME", anchor=tkinter.W)
        self.data_tree.pack()

    def reg_interfaces(self):
        require_authenticated_parent(self)
        win = self.registration_window
        if win is not None and win.winfo_exists():
            win.deiconify()
            win.lift()
            win.focus_force()
            return
        win = registration_control.registration_interface(self)
        self.registration_window = win
        original_on_close = win.on_close

        def on_close():
            original_on_close()
            self.registration_window = None

        win.on_close = on_close
        win.whole_reg_interface()

    def unreg_interface(self):
        require_authenticated_parent(self)
        win = self.unregister_window
        if win is not None and win.winfo_exists():
            win.deiconify()
            win.lift()
            win.focus_force()
            return
        win = unregister_control.Unregister_interface(self)
        self.unregister_window = win
        win.protocol("WM_DELETE_WINDOW", lambda: self._on_sub_window_closed(win, "unregister_window"))

    def cam(self):
        require_authenticated_parent(self)
        self.start.update()
        self.stop.configure(state=NORMAL,bg='#2e7e99')
        self.start.configure(state=DISABLED,bg='#2e7e99')
        Attendance_taker = main.Attendance_taker(self.auth_session)
        try:
            img_present = Attendance_taker.image_and_person_name_path_provider()
        except (mysql.connector.Error, OSError, ValueError) as exc:
            self.start.configure(state=NORMAL,bg='#2e7e99')
            self.stop.configure(state=DISABLED,bg='#2e7e99')
            messagebox.showerror(
                "Attendance could not start",
                f"Active teacher data could not be loaded:\n{exc}",
                parent=self,
            )
            return
        if img_present is False:
            self.start.configure(state=NORMAL,bg='#2e7e99')
            self.stop.configure(state=DISABLED,bg='#2e7e99')
            return
        self.task_running = True
        self.attendance_error_queue = Queue()
        self.attendance_stop_event = Event()
        self.task1 = Process(
            target=Attendance_taker.came_scanner,
            args=(self.attendance_error_queue, self.attendance_stop_event),
            daemon=True,
        )
        self.task1.start()
        self.after(500, self._poll_attendance_errors)

    def _poll_attendance_errors(self):
        require_authenticated_parent(self)
        if not self.task_running:
            return
        try:
            error = self.attendance_error_queue.get_nowait()
        except queue.Empty:
            error = None
        if error:
            messagebox.showerror("Attendance error", error, parent=self)
        if not self.task1.is_alive():
            self.task_running = False
            self.start.configure(state=NORMAL,bg="#2e7e99")
            self.stop.configure(state=DISABLED,bg="#2e7e99")
            return
        self.after(500, self._poll_attendance_errors)

    def data_reciver(self):
        require_authenticated_parent(self)
        try:
            records = data_flow_controle.get_today_attendance()
            self._database_error_reported = False
        except mysql.connector.Error as exc:
            if not self._database_error_reported:
                messagebox.showerror(
                    "Database connection error",
                    f"Could not refresh today's attendance from MySQL:\n{exc}",
                    parent=self,
                )
                self._database_error_reported = True
            self.data_tree.after(5000, self.data_reciver)
            return
        today = datetime.today().strftime("%m/%d/%Y")
        for record in records:
            row_key = (str(record["teacher_id"]), record["attendance_date"])
            if row_key in self.ids_list:
                continue
            self.ids_list.append(row_key)
            attendance_time = record["attendance_time"]
            self.data_tree.insert(
                "",
                index=END,
                values=(
                    record["name"],
                    record["teacher_id"],
                    str(record["attendance_status"]).title(),
                    today,
                    data_flow_controle.format_attendance_time(attendance_time),
                ),
            )
        self.data_tree.after(1000, self.data_reciver)

    def refresh_attendance_display(self):
        require_authenticated_parent(self)
        if not hasattr(self, "data_tree"):
            return
        self.data_tree.delete(*self.data_tree.get_children())
        self.ids_list.clear()
        self.data_tree.after(0, self.data_reciver)

    def history_calling(self):
        require_authenticated_parent(self)
        win = self.history_window
        if win is not None and win.winfo_exists():
            win.deiconify()
            win.lift()
            win.focus_force()
            return
        win = history_interface.History_table(self)
        self.history_window = win
        win.protocol("WM_DELETE_WINDOW", lambda: self._on_sub_window_closed(win, "history_window"))
        win.run_history()

    def _on_sub_window_closed(self, win, attr_name):
        """Close a single-instance sub-window and clear its stored reference."""
        try:
            win.destroy()
        except Exception:
            pass
        setattr(self, attr_name, None)

    def button_style(self):
        return resolve_path("Buttons", "Search button.png")

    def build_buttons(self):
        btn_img = self.button_style()
        button_frame=Frame(self,bg="#2e7e99")
        button_frame.pack(pady=30)
        self.update()
        main.create_optional_image_button(
            button_frame, "Registration", self.reg_interfaces, btn_img
        ).pack(side=LEFT,padx=10)
        main.create_optional_image_button(
            button_frame, "Teacher Status", self.unreg_interface, btn_img
        ).pack(side=LEFT,padx=10)
        self.start=main.create_optional_image_button(
            button_frame, "Start Attendance", self.cam, btn_img
        )
        self.start.pack(side=LEFT,padx=10)
        self.stop =main.create_optional_image_button(
            button_frame, "Stop Attendance", self.stop, btn_img, state=DISABLED
        )
        self.stop.pack(side=LEFT,padx=10)
        main.create_optional_image_button(
            button_frame, "Teachers History", self.history_calling, btn_img
        ).pack(side=LEFT,padx=10)

class CameraSettingsWindow(Toplevel):
    def __init__(self, parent):
        require_authenticated_parent(parent)
        super().__init__(parent)
        self.parent = parent
        self.auth_session = parent.auth_session
        self.title("Camera Settings")
        self.configure(bg="#2e7e99")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

        self.saved_attendance, self.saved_registration = data_flow_controle.load_camera_config()
        self.detecting = False
        self.preview_running = False
        self.preview_reader = None
        self.preview_sequence = -1
        self.attendance_vars = None
        self.registration_vars = None

        self.build_ui()
        self.load_settings_into_ui()
        self.bind("<Destroy>", self._on_destroy, add="+")

    def build_ui(self):
        Label(self, text="Camera Settings", font=("Arial Black", 16),
              bg="#2e7e99", fg="#FFFFFF").pack(pady=(12, 8))

        container = Frame(self, bg="#2e7e99")
        container.pack(padx=15, pady=5)

        self.attendance_vars = self.build_camera_section(
            container, "Attendance Camera", "attendance", row=0)
        self.registration_vars = self.build_camera_section(
            container, "Registration Camera", "registration", row=1)

        btn_frame = Frame(self, bg="#2e7e99")
        btn_frame.pack(pady=14)
        btn_img = resolve_path("Buttons", "Search button.png")
        main.create_optional_image_button(
            btn_frame, "Save Settings", self.save_settings, btn_img,
            height=60, bg="#2e7e99", fg="#FFFFFF",
        ).pack(side=LEFT, padx=10)
        main.create_optional_image_button(
            btn_frame, "Cancel", self.on_cancel, btn_img,
            height=60, bg="#2e7e99", fg="#FFFFFF",
        ).pack(side=LEFT, padx=10)

    def build_camera_section(self, parent, title, key, row):
        section = LabelFrame(parent, text=title, bg="#2e7e99", fg="#FFFFFF",
                             font=("Arial Black", 12), bd=2)
        section.grid(row=row, column=0, padx=8, pady=8, sticky="ew")

        vars_ = {
            "key": key,
            "source_type": StringVar(value="local"),
            "index": StringVar(value="0"),
            "url": StringVar(value=""),
            "status": StringVar(value=""),
        }

        type_frame = Frame(section, bg="#2e7e99")
        type_frame.pack(anchor="w", padx=8, pady=(6, 2))
        Radiobutton(type_frame, text="Local Camera Index", variable=vars_["source_type"],
                    value="local", bg="#2e7e99", fg="#FFFFFF",
                    selectcolor="#2e7e99", activebackground="#2e7e99",
                    activeforeground="#00ffff", font=("Arial Black", 10),
                    command=lambda: self.on_source_type_change(vars_)).pack(side=LEFT)
        Radiobutton(type_frame, text="Network URL (RTSP/HTTP)", variable=vars_["source_type"],
                    value="network", bg="#2e7e99", fg="#FFFFFF",
                    selectcolor="#2e7e99", activebackground="#2e7e99",
                    activeforeground="#00ffff", font=("Arial Black", 10),
                    command=lambda: self.on_source_type_change(vars_)).pack(side=LEFT, padx=(18, 0))

        index_row = Frame(section, bg="#2e7e99")
        index_row.pack(anchor="w", padx=8, pady=2)
        Label(index_row, text="Camera Index (0, 1, 2 ...):", bg="#2e7e99",
              fg="#FFFFFF", font=("Arial Black", 10)).pack(side=LEFT)
        index_entry = Entry(index_row, textvariable=vars_["index"], width=10,
                            font=("Arial Black", 10), bg="#D8FCC9")
        index_entry.pack(side=LEFT, padx=(6, 6))
        vars_["index_entry"] = index_entry
        Button(index_row, text="Detect Cameras", font=("Arial Black", 9),
               bg="#2e7e99", fg="white", border=0, borderwidth=0,
               activebackground="#2e7e99", activeforeground="#00ffff",
               command=lambda: self.detect_cameras(vars_)).pack(side=LEFT)

        url_row = Frame(section, bg="#2e7e99")
        url_row.pack(anchor="w", padx=8, pady=2)
        Label(url_row, text="Camera URL:", bg="#2e7e99", fg="#FFFFFF",
              font=("Arial Black", 10)).pack(side=LEFT)
        url_entry = Entry(url_row, textvariable=vars_["url"], width=38,
                          font=("Arial Black", 10), bg="white")
        url_entry.pack(side=LEFT, padx=(6, 0))
        vars_["url_entry"] = url_entry

        test_row = Frame(section, bg="#2e7e99")
        test_row.pack(anchor="w", padx=8, pady=(6, 8))
        Button(test_row, text="Test Camera", font=("Arial Black", 10),
               bg="#2e7e99", fg="white", border=0, borderwidth=0,
               activebackground="#2e7e99", activeforeground="#00ffff",
               command=lambda: self.test_camera(vars_)).pack(side=LEFT)
        status_label = Label(test_row, textvariable=vars_["status"], bg="#2e7e99",
                             fg="#00ffff", font=("Arial Black", 10))
        status_label.pack(side=LEFT, padx=(12, 0))
        vars_["status_label"] = status_label

        self.on_source_type_change(vars_)
        return vars_

    def on_source_type_change(self, vars_):
        if vars_["source_type"].get() == "local":
            vars_["index_entry"].configure(state=NORMAL)
            vars_["url_entry"].configure(state=DISABLED)
        else:
            vars_["index_entry"].configure(state=DISABLED)
            vars_["url_entry"].configure(state=NORMAL)

    def load_settings_into_ui(self):
        att = self.saved_attendance
        if self.is_network_url(att):
            self.attendance_vars["source_type"].set("network")
            self.attendance_vars["url"].set(att)
        else:
            self.attendance_vars["source_type"].set("local")
            self.attendance_vars["index"].set(att)
        self.on_source_type_change(self.attendance_vars)

        reg = self.saved_registration
        if self.is_network_url(reg):
            self.registration_vars["source_type"].set("network")
            self.registration_vars["url"].set(reg)
        else:
            self.registration_vars["source_type"].set("local")
            self.registration_vars["index"].set(reg)
        self.on_source_type_change(self.registration_vars)

    @staticmethod
    def is_network_url(value):
        if not value:
            return False
        v = str(value).strip()
        try:
            int(v)
            return False
        except ValueError:
            return True

    def get_section_value(self, vars_):
        if vars_["source_type"].get() == "network":
            return vars_["url"].get().strip()
        return vars_["index"].get().strip() or "0"

    def save_settings(self):
        require_authenticated_parent(self)
        attendance_value = self.get_section_value(self.attendance_vars)
        registration_value = self.get_section_value(self.registration_vars)
        if data_flow_controle.save_camera_config(attendance_value, registration_value):
            self.saved_attendance = attendance_value
            self.saved_registration = registration_value
            messagebox.showinfo("Saved", "Camera settings saved successfully.")
            self.destroy()
        else:
            messagebox.showerror("Error", "Failed to save camera settings.")

    def on_cancel(self):
        self.preview_running = False
        self.detecting = False
        self._stop_preview_reader()
        self.destroy()

    def _on_destroy(self, event):
        if event.widget is self:
            self.preview_running = False
            self.detecting = False
            self._stop_preview_reader()

    def detect_cameras(self, vars_):
        require_authenticated_parent(self)
        if self.detecting:
            return
        self.detecting = True
        vars_["status"].set("Detecting cameras...")
        thread = threading.Thread(target=self._detect_cameras_thread, args=(vars_,), daemon=True)
        thread.start()

    def _detect_cameras_thread(self, vars_):
        working = []
        for index in range(0, 10):
            if not self.auth_session.is_authenticated():
                return
            cap = None
            try:
                cap = cv2.VideoCapture(index)
                if cap is not None and cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        working.append(str(index))
            except Exception:
                pass
            finally:
                if cap is not None:
                    try:
                        cap.release()
                    except Exception:
                        pass
        if self.auth_session.is_authenticated():
            self.after(0, lambda: self._detection_finished(vars_, working))

    def _detection_finished(self, vars_, working):
        require_authenticated_parent(self)
        self.detecting = False
        if working:
            vars_["status"].set(f"Detected: {', '.join(working)}")
            vars_["index"].set(working[0])
        else:
            vars_["status"].set("No local cameras detected")

    def test_camera(self, vars_):
        require_authenticated_parent(self)
        source = self.get_section_value(vars_)
        if not source:
            messagebox.showwarning("Warning", "Please enter a camera index or URL.")
            return
        if self.preview_running:
            return
        self.preview_running = True
        self.preview_sequence = -1
        vars_["status"].set("Testing...")
        self.preview_reader = LatestFrameCapture(self.resolve_source(source))
        self.preview_reader.start()
        self.after(50, lambda: self._poll_camera_test(vars_, source))

    def resolve_source(self, source):
        try:
            return int(str(source).strip())
        except ValueError:
            return str(source).strip()

    def _poll_camera_test(self, vars_, source):
        if not self.preview_running or not self.auth_session.is_authenticated():
            return
        reader = self.preview_reader
        if reader is None:
            return
        if reader.error:
            error = reader.error
            self.preview_running = False
            self._stop_preview_reader()
            self._test_finished(vars_, False, error)
            return
        sequence, frame = reader.read_latest()
        if frame is None:
            self.after(50, lambda: self._poll_camera_test(vars_, source))
            return
        self.preview_sequence = sequence
        self._test_finished(vars_, True, "Camera is working.")
        self.show_live_preview(source)

    def show_live_preview(self, source):
        require_authenticated_parent(self)
        preview = Toplevel(self)
        preview.title(f"Live Preview - {source}")
        preview.configure(bg="#2e7e99")
        preview.resizable(False, False)
        preview_frame = Frame(
            preview, bg="black", width=CAMERA_DISPLAY_SIZE[0],
            height=CAMERA_DISPLAY_SIZE[1],
        )
        preview_frame.pack(padx=8, pady=8)
        preview_frame.pack_propagate(False)
        label = Label(preview_frame, bg="black")
        label.pack(fill=BOTH, expand=True)
        Button(preview, text="Close Preview", bg="#2e7e99", fg="white",
               border=0, borderwidth=0, activebackground="#2e7e99",
               activeforeground="#00ffff", font=("Arial Black", 10),
               command=lambda: self.stop_preview(preview)).pack(pady=(0, 8))

        def update_frame():
            if not self.preview_running:
                if preview.winfo_exists():
                    preview.destroy()
                return
            reader = self.preview_reader
            if reader is None:
                self.stop_preview(preview)
                return
            if reader.error:
                error = reader.error
                self.stop_preview(preview)
                messagebox.showerror("Camera preview stopped", error, parent=self)
                return
            sequence, frame = reader.read_latest()
            if frame is not None and sequence != self.preview_sequence:
                self.preview_sequence = sequence
                frame = cv2.flip(fit_camera_frame(frame), 1)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = ImageTk.PhotoImage(Image.fromarray(frame))
                label.configure(image=img)
                label.image = img
            preview.after(33, update_frame)

        preview.after(0, update_frame)
        preview.protocol("WM_DELETE_WINDOW", lambda: self.stop_preview(preview))

    def _stop_preview_reader(self):
        reader = self.preview_reader
        self.preview_reader = None
        if reader is not None:
            reader.stop()

    def stop_preview(self, preview=None):
        self.preview_running = False
        self._stop_preview_reader()
        if preview is not None:
            if preview.winfo_exists():
                preview.destroy()

    def _test_finished(self, vars_, success, message):
        if success:
            vars_["status"].set("Test passed")
            vars_["status_label"].configure(fg="#00ff00")
            messagebox.showinfo("Camera Test", message)
        else:
            vars_["status"].set("Test failed")
            vars_["status_label"].configure(fg="#ff0000")
            messagebox.showerror("Camera Test Failed", message)


####################################################################################################################################################
####################################################################################################################################################
if __name__ == '__main__':
    authentication_window = AdminAuthenticationWindow()
    if authentication_window.winfo_exists():
        authentication_window.mainloop()
