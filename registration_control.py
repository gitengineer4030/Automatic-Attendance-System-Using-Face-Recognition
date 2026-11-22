from tkinter import *
import cv2
from PIL import Image,ImageTk
import os
import data_flow_controle
from data_flow_controle import resolve_path
import tkinter as tk
from tkinter import messagebox
import mysql.connector
from admin_auth import require_authenticated_parent
from main import (
    CAMERA_DISPLAY_SIZE,
    LatestFrameCapture,
    create_optional_image_button,
    fit_camera_frame,
)
###############################################################################################################
#The camera class provide Camera interface To store The photo of Registed person
##############################################################################################################
class Reg_Camera(Toplevel):
    def __init__(self,parent, teacher_data):
        require_authenticated_parent(parent)
        super().__init__(parent)
        self.auth_session = parent.auth_session
        self.teacher_data = teacher_data
        self.image = None
        self.photo_path = None
        self.registration_completed = False
        self.photo_created = False
        self.reuse_existing_photo = False
        self.encoding_created = False
        self.minsize(width=720, height=540)
        self.configure(bg="#2e7e99")
        self.title("Camera")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.frame = None
        self.label = None
        self.take_frame = None
        self.cancel = None
        self.register = None
        self.capture_reader = None
        self._camera_running = False
        self._last_frame_sequence = -1
        self._latest_frame = None
        self._camera_error_reported = False

    def _remove_created_files(self, *paths):
        failures = []
        for path in paths:
            if not path or not os.path.exists(path):
                continue
            try:
                os.remove(path)
            except OSError as exc:
                failures.append(f"{path}: {exc}")
        if failures:
            messagebox.showwarning(
                "Cleanup warning",
                "Registration failed, and these temporary files could not be "
                "removed:\n\n" + "\n".join(failures),
                parent=self,
            )

    def resolve_camera_source(self, source):
        """Resolve a saved camera configuration to a cv2.VideoCapture argument.
        Numeric strings become camera indexes (int); anything else is treated
        as a network URL string (RTSP/HTTP/etc.)."""
        if source is None or str(source).strip() == "":
            return 0
        try:
            return int(str(source).strip())
        except ValueError:
            return str(source).strip()

    def camera_frame(self):
        came_frame = LabelFrame(self, bg="black", width=CAMERA_DISPLAY_SIZE[0],
                                height=CAMERA_DISPLAY_SIZE[1])
        came_frame.pack(padx=8, pady=8)
        came_frame.pack_propagate(False)
        self.label_came = Label(came_frame, bg="black", text="Connecting to camera...",
                                fg="white")
        self.label_came.pack(fill=BOTH, expand=True)
        _, saved_registration = data_flow_controle.load_camera_config()
        source = self.resolve_camera_source(saved_registration)
        self.capture_reader = LatestFrameCapture(source)


    def camera_controle(self):
        """Start the camera preview loop using Tkinter after() (non-blocking)."""
        if self._camera_running:
            return
        self._camera_running = True
        self._camera_error_reported = False
        self._last_frame_sequence = -1
        self.capture_reader.start()
        self._update_camera_frame()

    def _update_camera_frame(self):
        """Read one frame, update the label, and schedule the next update."""
        if not self._camera_running:
            return
        reader = self.capture_reader
        if reader is None:
            return
        if reader.error and not self._camera_error_reported:
            self._camera_error_reported = True
            self.stop_camera()
            messagebox.showerror(
                "Camera unavailable", reader.error, parent=self
            )
            return
        sequence, frame = reader.read_latest()
        if frame is not None and sequence != self._last_frame_sequence:
            self._last_frame_sequence = sequence
            self._latest_frame = frame
            display_frame = fit_camera_frame(frame)
            display_frame = cv2.flip(display_frame, 1)
            display_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            photo = ImageTk.PhotoImage(Image.fromarray(display_frame))
            self.frame = photo
            self.label_came.configure(image=photo, text="")
            self.label_came.image = photo
        if self._camera_running:
            self.after(33, self._update_camera_frame)

    def stop_camera(self):
        """Stop the camera preview loop and release the capture device."""
        self._camera_running = False
        reader = self.capture_reader
        self.capture_reader = None
        if reader is not None:
            reader.stop()


    def capture_photo(self):
        require_authenticated_parent(self)
        if self._latest_frame is None:
            messagebox.showerror("Photo unavailable", "Wait for the camera preview before taking a photo.", parent=self)
            return
        photo_frame = cv2.flip(self._latest_frame, 1)
        photo_frame = cv2.cvtColor(photo_frame, cv2.COLOR_BGR2RGB)
        self.image = Image.fromarray(photo_frame)
        self.label_came.configure(image=self.frame)
        self.name = (
            f'{self.teacher_data["name"].upper()} '
            f'{self.teacher_data["teacher_id"]}.jpg'
        )
        self.photo_path = resolve_path("Images", self.name)
        if os.path.exists(self.photo_path):
            reuse = messagebox.askyesno(
                "Reuse existing photo?",
                "A photo with this teacher ID already exists. Reuse it without "
                "overwriting the existing photo?",
                parent=self,
            )
            if not reuse:
                self.photo_path = None
                return
            self.reuse_existing_photo = True
        else:
            try:
                os.makedirs(os.path.dirname(self.photo_path), exist_ok=True)
                self.image.save(self.photo_path)
            except OSError as exc:
                self.photo_path = None
                messagebox.showerror(
                    "Photo could not be saved",
                    f"The Images folder is unavailable or not writable:\n{exc}",
                    parent=self,
                )
                return
            self.photo_created = True
        self.cancel['state'] = NORMAL
        self.register['state'] = NORMAL
        self.take_frame['state'] = DISABLED

    def cancel_photo(self):
        self.take_frame['state'] = NORMAL
        self.cancel['state'] = DISABLED
        self.register['state'] = DISABLED
        self.stop_camera()
        _, saved_registration = data_flow_controle.load_camera_config()
        self.capture_reader = LatestFrameCapture(
            self.resolve_camera_source(saved_registration)
        )
        if self.photo_created:
            self._remove_created_files(self.photo_path)
        self.photo_path = None
        self.photo_created = False
        self.reuse_existing_photo = False
        self._latest_frame = None
        self.camera_controle()

    def save_photo(self):
        self.camera_controle()

    def store_registration(self):
        require_authenticated_parent(self)
        self.stop_camera()
        if not self.photo_path or not os.path.isfile(self.photo_path):
            messagebox.showerror("Registration failed", "Take a photo before registering.", parent=self)
            return
        encoding_path = resolve_path(
            "Encodes", os.path.splitext(os.path.basename(self.photo_path))[0] + ".npy"
        )
        if os.path.exists(encoding_path) and not self.reuse_existing_photo:
            messagebox.showerror(
                "Encoding already exists",
                "A face encoding with this teacher ID already exists. It was not overwritten.",
                parent=self,
            )
            return
        try:
            import numpy

            os.makedirs(os.path.dirname(encoding_path), exist_ok=True)
            if not os.path.exists(encoding_path):
                import face_recognition

                image = face_recognition.load_image_file(self.photo_path)
                encodings = face_recognition.face_encodings(image)
                if not encodings:
                    raise ValueError("No face was detected in the captured photo.")
                numpy.save(encoding_path, encodings[0], allow_pickle=False)
                self.encoding_created = True
            else:
                encoding = numpy.load(encoding_path, allow_pickle=False)
                if encoding.shape != (128,):
                    raise ValueError("The saved face encoding has an invalid shape.")
            data_flow_controle.register_teacher(
                self.teacher_data, self.photo_path, encoding_path
            )
        except data_flow_controle.DuplicateTeacherError as exc:
            messagebox.showerror("Duplicate teacher", str(exc), parent=self)
            self._cleanup_registration_files(encoding_path)
            self.master.camera_on = False
            self.master.deiconify()
            self.destroy()
            return
        except (
            ImportError,
            OSError,
            ValueError,
            RuntimeError,
            mysql.connector.Error,
        ) as exc:
            messagebox.showerror(
                "Registration failed",
                f"The teacher could not be registered:\n{exc}",
                parent=self,
            )
            self._cleanup_registration_files(encoding_path)
            self._resume_capture()
            return
        messagebox.showinfo("Registration complete", "Teacher registered successfully.", parent=self)
        self.registration_completed = True
        self.master.camera_on = False
        self.master.deiconify()
        self.destroy()

    def _cleanup_registration_files(self, encoding_path):
        cleanup_paths = []
        if self.encoding_created:
            cleanup_paths.append(encoding_path)
        if self.photo_created:
            cleanup_paths.append(self.photo_path)
        self._remove_created_files(*cleanup_paths)
        self.encoding_created = False
        self.photo_created = False
        self.photo_path = None
        self.reuse_existing_photo = False

    def _resume_capture(self):
        self.take_frame.configure(state=NORMAL)
        self.cancel.configure(state=DISABLED)
        self.register.configure(state=DISABLED)
        _, saved_registration = data_flow_controle.load_camera_config()
        self.capture_reader = LatestFrameCapture(
            self.resolve_camera_source(saved_registration)
        )
        self._latest_frame = None
        self.camera_controle()

    def build_buttons(self):
        btn_img = self.button_style()
        fram_buttons = Frame(self, bg="#2e7e99")
        fram_buttons.pack(pady=10)
        self.take_frame = create_optional_image_button(
            fram_buttons, "Take Photo", self.capture_photo, btn_img,
            bg="#2e7e99",
        )
        self.take_frame.pack(side=LEFT, padx=10)
        self.cancel = create_optional_image_button(
            fram_buttons, "Cancel", self.cancel_photo, btn_img,
            state=DISABLED, bg="#2e7e99",
        )
        self.cancel.pack(side=LEFT, padx=10)
        self.register = create_optional_image_button(
            fram_buttons, "Register", self.store_registration, btn_img,
            state=DISABLED, bg="#2e7e99",
        )
        self.register.pack(side=LEFT, padx=10)

    def button_style(self):
        return resolve_path("Buttons", "Search button.png")

    def on_close(self):
        self.stop_camera()
        if not self.registration_completed:
            self._cleanup_registration_files(
                resolve_path(
                    "Encodes",
                    os.path.splitext(os.path.basename(self.photo_path or ""))[0] + ".npy",
                )
            )
        self.master.camera_on = False
        self.master.deiconify()
        self.destroy()
################################################################################################################################################
#This is the registration entres interface for geting information of Teachers
################################################################################################################################################
class registration_interface(Toplevel):
    def __init__(self,parent):
        require_authenticated_parent(parent)
        super().__init__(parent)
        self.auth_session = parent.auth_session
        self.name = None
        self.lastname = None
        self.father_name = None
        self.id_number = None
        self.subject = None
        self.phone_number = None
    ####################################################
    def whole_reg_interface(self):
        self.minsize(width=720, height=540)
        self.configure(background="#2e7e99")
        self.title("Teacher Registration")
        self.protocol('WM_DELETE_WINDOW', self.on_close)
        self.camera_on = False
        # self.resizable(False, False)
        self.headings()
        self.sub_frames()
        self.set_entry_name()
        self.create_entry()
        self.creat_buttons()
        self.label = None
        # self.default_file()
    #########################################################
    def headings(self):
        self.heading_of_registration =Label(self,text="Teacher Registration",font=("Arial Black",30),bg="#2e7e99",fg="#F9F9F9")
        self.heading_of_registration.pack()

    def sub_frames(self):
        """self.entres_frame = Frame(self, bg="#34568B")
        self.entres_frame.pack()"""
        self.frame_of_labels_and_entres = Frame(self, bg="#2e7e99")
        self.frame_of_labels_and_entres.pack(pady=40)
        self.button_frame = Frame(self, bg='#2e7e99', padx=40)
        self.button_frame.pack()

    def create_entry(self):
        name = Entry(self.frame_of_labels_and_entres, width=25, font=("Arial Black", 10),bg="white")
        name.grid(row=1, column=2, pady=10)
        self.name = name
        name.focus()
        father_name = Entry(self.frame_of_labels_and_entres, width=25, font=("Arial Black", 10),bg="white")
        father_name.grid(row=2, column=2, pady=10)
        self.father_name = father_name
        id_number = Entry(self.frame_of_labels_and_entres, width=25, font=("Arial Black", 10),bg="white")
        id_number.grid(row=3, column=2, pady=10)
        self.id_number = id_number
        subject = Entry(self.frame_of_labels_and_entres, width=25, font=("Arial Black", 10),bg="white")
        subject.grid(row=4, column=2, pady=10)
        self.subject = subject
        phone_number = Entry(self.frame_of_labels_and_entres, width=25, font=("Arial Black", 10),bg="white")
        phone_number.grid(row=5, column=2, pady=10)
        self.phone_number = phone_number


    def set_entry_name(self):
        Label(self.frame_of_labels_and_entres, text="NAME", width=15, fg="#FFFFFF", bg="#2e7e99", font=("Arial Black", 12)).grid(row=1,
                                                                                                             column=1)
        Label(self.frame_of_labels_and_entres, text="FATHER NAME", width=15, fg="#FFFFFF", bg="#2e7e99", font=("Arial Black", 12)).grid(
            row=2, column=1)
        Label(self.frame_of_labels_and_entres, text="ID NO", width=15, fg="#FFFFFF", bg="#2e7e99", font=("Arial Black", 12)).grid(row=3,
                                                                                                             column=1)
        Label(self.frame_of_labels_and_entres, text="SUBJECT", width=15, fg="#FFFFFF", bg="#2e7e99", font=("Arial Black", 12)).grid(row=4,
                                                                                                               column=1)
        Label(self.frame_of_labels_and_entres, text="PHONE", width=15, fg="#FFFFFF", bg="#2e7e99", font=("Arial Black", 12)).grid(row=5,
                                                                                                             column=1)
    def get_entres(self):
        return {
            "name": self.name.get().strip(),
            "father_name": self.father_name.get().strip(),
            "teacher_id": self.id_number.get().strip(),
            "subject": self.subject.get().strip(),
            "phone_number": self.phone_number.get().strip(),
        }

    def web_came(self):
        require_authenticated_parent(self)
        teacher_data = self.get_entres()
        if any(not value for value in teacher_data.values()):
            messagebox.showinfo("info","Please fill remaining field first!")
            return
        try:
            if data_flow_controle.get_teacher_by_id(teacher_data["teacher_id"]):
                messagebox.showinfo("info","The IDNO is already register!")
                return
        except mysql.connector.Error as exc:
            messagebox.showerror(
                "Database error",
                f"Could not check whether the teacher ID is already registered:\n{exc}",
                parent=self,
            )
            return
        if not teacher_data["teacher_id"].isdigit():
            messagebox.showinfo("info", "ID number must contain digits only!")
            return
        if not teacher_data["phone_number"].isdigit():
            messagebox.showinfo("info", "Phone number must contain digits only!")
            return
        self.grab_release()
        self.withdraw()
        self.camera_on = True
        self.Reg_Camera = Reg_Camera(self, teacher_data)
        self.Reg_Camera.camera_frame()
        self.Reg_Camera.build_buttons()
        self.Reg_Camera.camera_controle()
        self.Reg_Camera.mainloop()

    def clear_entres(self):
        self.name.delete(0, END)
        self.father_name.delete(0,END)
        self.subject.delete(0,END)
        self.id_number.delete(0,END)
        self.phone_number.delete(0,END)
        self.name.focus()

    def creat_buttons(self):
        btn_img = self.button_style()
        create_optional_image_button(
            self.button_frame, "Cancel", self.clear_entres, btn_img,
            bg="#2e7e99", fg="#FFFFFF", pady=3,
        ).grid(row=6, column=2, padx=60)
        create_optional_image_button(
            self.button_frame, "Next", self.web_came, btn_img,
            bg="#2e7e99", fg="#FFFFFF", pady=3,
        ).grid(row=6, column=4, padx=12)

    def button_style(self):
        return resolve_path("Buttons", "Search button.png")

    def on_close(self):
        camera = getattr(self, "Reg_Camera", None)
        if self.camera_on and camera is not None and camera.winfo_exists():
            camera.stop_camera()
            camera._remove_created_files(camera.photo_path)
            camera.destroy()
        self.destroy()

    ###################################################################################################################
    ###################################################################################################################
