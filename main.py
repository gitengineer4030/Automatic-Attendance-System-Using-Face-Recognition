import pickle
import cv2
import os
import threading
import face_recognition
from datetime import datetime
import time
import logging
import numpy
import data_flow_controle
from data_flow_controle import resolve_path
from admin_auth import AdminSession
import tkinter as tk
from tkinter import messagebox
import mysql.connector
###########################################################################################


CAMERA_DISPLAY_SIZE = (800, 450)
_NETWORK_OPEN_TIMEOUT_MS = 5000
_NETWORK_READ_TIMEOUT_MS = 1000


def create_optional_image_button(
    parent, text, command, image_path, width=155, height=50, **options
):
    """Create a consistently sized button whether or not its image is available."""
    image = None
    try:
        image = tk.PhotoImage(master=parent, file=image_path)
    except (OSError, tk.TclError):
        pass

    button_options = {
        "text": text,
        "command": command,
        "font": ("Arial Black", 10),
        "bg": "#1f5d7e",
        "fg": "white",
        "activebackground": "#2e7e99",
        "activeforeground": "#00ffff",
        "cursor": "hand2",
    }
    button_options.update(options)
    if image is not None:
        try:
            button_background = options.get("bg", parent.cget("background"))
        except tk.TclError:
            button_background = button_options["bg"]
        button_options.update(
            image=image,
            compound=tk.CENTER,
            width=max(width, image.width()),
            height=max(height, image.height()),
            bg=button_background,
            activebackground=button_background,
            borderwidth=0,
            relief=tk.FLAT,
            highlightthickness=0,
            padx=0,
            pady=0,
        )
    else:
        button_options.update(
            width=max(12, min(22, len(text) + 4)),
            height=2,
            padx=8,
            pady=6,
            borderwidth=1,
            relief=tk.RAISED,
            highlightthickness=0,
        )

    button = tk.Button(parent, **button_options)
    button.image = image
    return button


def is_network_camera_source(source):
    if not isinstance(source, str):
        return False
    return source.strip().lower().startswith(("rtsp://", "http://", "https://"))


def fit_camera_frame(frame, max_size=CAMERA_DISPLAY_SIZE):
    height, width = frame.shape[:2]
    max_width, max_height = max_size
    scale = min(max_width / width, max_height / height, 1.0)
    if scale == 1.0:
        return frame

    size = (max(1, round(width * scale)), max(1, round(height * scale)))
    return cv2.resize(frame, size, interpolation=cv2.INTER_AREA)


def open_camera_capture(source):
    if is_network_camera_source(source):
        parameters = []
        if hasattr(cv2, "CAP_PROP_OPEN_TIMEOUT_MSEC"):
            parameters.extend(
                (cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, _NETWORK_OPEN_TIMEOUT_MS)
            )
        if hasattr(cv2, "CAP_PROP_READ_TIMEOUT_MSEC"):
            parameters.extend(
                (cv2.CAP_PROP_READ_TIMEOUT_MSEC, _NETWORK_READ_TIMEOUT_MS)
            )
        if parameters:
            try:
                capture = cv2.VideoCapture(
                    source, cv2.CAP_FFMPEG, parameters
                )
            except cv2.error:
                capture = cv2.VideoCapture(source)
        else:
            capture = cv2.VideoCapture(source)
    else:
        capture = cv2.VideoCapture(source)

    if not capture.isOpened():
        capture.release()
        raise RuntimeError("Could not open the selected camera source.")

    capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return capture


class LatestFrameCapture:
    """Read camera frames in the background while retaining only the newest."""

    def __init__(self, source):
        self.source = source
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._thread = None
        self._capture = None
        self._ready = False
        self._error = None
        self._latest_frame = None
        self._sequence = 0

    @property
    def ready(self):
        with self._lock:
            return self._ready

    @property
    def error(self):
        with self._lock:
            return self._error

    def start(self):
        if self._thread is not None:
            raise RuntimeError("Camera frame capture has already been started.")
        self._thread = threading.Thread(target=self._read_frames, daemon=True)
        self._thread.start()

    def read_latest(self):
        with self._lock:
            return self._sequence, self._latest_frame

    def stop(self):
        self._stop_event.set()
        if self._thread is not None and self._thread is not threading.current_thread():
            self._thread.join(timeout=0.25)

    def _read_frames(self):
        capture = None
        try:
            capture = open_camera_capture(self.source)
            with self._lock:
                self._capture = capture
                self._ready = True

            while not self._stop_event.is_set():
                success, frame = capture.read()
                if not success or frame is None:
                    if not self._stop_event.is_set():
                        raise RuntimeError(
                            "The camera stopped delivering video frames."
                        )
                    break
                with self._lock:
                    self._latest_frame = frame
                    self._sequence += 1
        except Exception as exc:
            with self._lock:
                self._error = str(exc)
        finally:
            if capture is not None:
                capture.release()
            with self._lock:
                self._capture = None
                self._ready = False


class Attendance_taker():
    def __init__(self, auth_session=None):
        self.auth_session = auth_session
        self.images = []
        self.person_name = []
        self.encoding_List= []
        self.encoding_list= []
        self.name = None
        self.dateandtime = None
        self.cap = None
        self.name_list = []
        self.teacher_ids = []
        self._active_signature = None
        self._last_active_refresh = 0

    def _require_authentication(self):
        if (
            not isinstance(self.auth_session, AdminSession)
            or not self.auth_session.is_authenticated()
        ):
            raise PermissionError("Administrator authentication is required.")
        data_flow_controle.set_authenticated_session(self.auth_session)
################################################################################
    def image_and_person_name_path_provider(self):
        self._require_authentication()
        self.refresh_active_teachers(force=True)
        if not self.teacher_ids:
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo(
                "No active teachers",
                "Register or activate a teacher before starting attendance.",
            )
            root.destroy()
            return False
        return True

    def refresh_active_teachers(self, force=False):
        self._require_authentication()
        if not force and time.monotonic() - self._last_active_refresh < 3:
            return
        teachers = data_flow_controle.get_active_teachers()
        signature = tuple(
            (
                str(teacher["teacher_id"]),
                teacher["encoding_path"],
                str(teacher["name"]).strip(),
            )
            for teacher in teachers
        )
        self._last_active_refresh = time.monotonic()
        if not force and signature == self._active_signature:
            return

        encodings = []
        teacher_ids = []
        names = []
        for teacher in teachers:
            encoding_path = teacher["encoding_path"]
            if not encoding_path or not os.path.isfile(encoding_path):
                raise FileNotFoundError(
                    f"Face encoding is missing for teacher ID {teacher['teacher_id']}."
                )
            encodings.append(numpy.load(encoding_path, allow_pickle=False))
            teacher_ids.append(str(teacher["teacher_id"]))
            names.append(str(teacher["name"]).strip())
        self._active_signature = signature
        self.teacher_ids = teacher_ids
        self.person_name = names
        self.encoding_list = encodings

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

    def myface_recognition(self, error_queue=None, stop_event=None):
        self._require_authentication()
        saved_attendance, _ = data_flow_controle.load_camera_config()
        camera_source = self.resolve_camera_source(saved_attendance)
        capture_reader = LatestFrameCapture(camera_source)
        capture_reader.start()
        network_source = is_network_camera_source(camera_source)
        last_frame_sequence = -1
        last_network_processing = 0
        marked_ids = set()
        try:
            while stop_event is None or not stop_event.is_set():
                if capture_reader.error:
                    if error_queue is not None:
                        error_queue.put(
                            f"Attendance camera stopped: {capture_reader.error}"
                        )
                    break
                frame_sequence, captured_frame = capture_reader.read_latest()
                if captured_frame is None or frame_sequence == last_frame_sequence:
                    time.sleep(0.01)
                    continue
                last_frame_sequence = frame_sequence
                if network_source:
                    now_monotonic = time.monotonic()
                    if now_monotonic - last_network_processing < 0.1:
                        continue
                    last_network_processing = now_monotonic

                try:
                    self.refresh_active_teachers()
                except (mysql.connector.Error, OSError, ValueError) as exc:
                    logging.exception("Could not refresh active face-recognition teachers.")
                    if error_queue is not None:
                        error_queue.put(
                            f"Attendance stopped because teacher data could not be refreshed: {exc}"
                        )
                    break

                frame = cv2.flip(captured_frame, 1)
                edit_frame = cv2.resize(frame, (0, 0), None, 0.25, 0.25)
                edit_frame = cv2.cvtColor(edit_frame, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(edit_frame)
                face_encodings = face_recognition.face_encodings(
                    edit_frame, face_locations
                )
                for face_encoding, face_location in zip(face_encodings, face_locations):
                    if not self.encoding_list:
                        break
                    matches = face_recognition.compare_faces(
                        self.encoding_list, face_encoding
                    )
                    distances = face_recognition.face_distance(
                        self.encoding_list, face_encoding
                    ).round(1)
                    match_index = int(numpy.argmin(distances))
                    is_recognized = (
                        matches[match_index] and distances[match_index] <= 0.3
                    )
                    if is_recognized:
                        teacher_id = self.teacher_ids[match_index]
                        name = self.person_name[match_index]
                        if teacher_id not in marked_ids:
                            try:
                                attendance = data_flow_controle.Data_Manager()
                                attendance.present_idnumber = teacher_id
                                attendance.present_name = name
                                now = datetime.now()
                                attendance.date = now.date()
                                attendance.time = now.time().replace(second=0, microsecond=0)
                                attendance.attendance_data()
                                marked_ids.add(teacher_id)
                            except data_flow_controle.DuplicateAttendanceError:
                                marked_ids.add(teacher_id)
                            except data_flow_controle.InactiveTeacherError:
                                self.refresh_active_teachers(force=True)
                                continue
                            except (mysql.connector.Error, ValueError) as exc:
                                logging.exception("Could not record attendance.")
                                if error_queue is not None:
                                    error_queue.put(f"Attendance could not be saved: {exc}")
                                return
                        color = (0, 255, 0)
                    else:
                        name = "Unknown"
                        color = (0, 0, 255)
                    y1, x2, y2, x1 = face_location
                    y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(
                        frame, name, (x1 + 25, y2 + 25),
                        cv2.FONT_HERSHEY_COMPLEX, 1, color, 1,
                    )

                display_frame = fit_camera_frame(frame)
                cv2.imshow("camera", display_frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
        finally:
            capture_reader.stop()
            cv2.destroyAllWindows()

    def date_time_saver(self):
        self._require_authentication()
        date = datetime.today().strftime('%m/%d/%Y')
        time = datetime.today().strftime('%I:%M')
        file = open(resolve_path("pathsfolder", "date.data"),"wb")
        pickle.dump(date,file)

    def came_scanner(self, error_queue=None, stop_event=None):
        self._require_authentication()
        try:
            self.refresh_active_teachers(force=True)
            if not self.teacher_ids:
                if error_queue is not None:
                    error_queue.put(
                        "Attendance stopped because there are no active teachers."
                    )
                return
            self.myface_recognition(error_queue, stop_event)
        except (mysql.connector.Error, OSError, ValueError) as exc:
            logging.exception("Attendance could not start.")
            if error_queue is not None:
                error_queue.put(f"Attendance could not start: {exc}")
            else:
                raise
###########################################################################################################
##########################################################################################################
if __name__ == '__main__':
    raise SystemExit(
        "Launch interface_main.py to authenticate before using attendance features."
    )