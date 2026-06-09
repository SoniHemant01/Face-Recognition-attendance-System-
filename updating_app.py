import sys
import cv2
from PyQt5.QtWidgets import (
    QApplication, QLabel, QPushButton,
    QVBoxLayout, QWidget, QInputDialog,
    QFileDialog, QStackedWidget, QMessageBox
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import (
    QImage, QPixmap, QFont,
    QPainter, QLinearGradient, QColor
)

from detection import detect_faces
from alignment import align_face
from updating_recognition import recognize_face, register_face
from updating_attendance import mark_attendance
from updating_registration import  register_from_folder
from attendance_analytics import get_attendance_summary
from liveness import check_blink


from attendance_view import (
    get_person_attendance,
    show_attendance_chart
)

# ==============================
# ANIMATED BACKGROUND
# ==============================
class AnimatedBackground(QWidget):
    def __init__(self):
        super().__init__()
        self.shift = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(40)

    def animate(self):
        self.shift += 1
        if self.shift > self.width():
            self.shift = 0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QLinearGradient(self.shift, 0, self.width(), self.height())
        gradient.setColorAt(0.0, QColor(44, 123, 229))
        gradient.setColorAt(0.5, QColor(108, 117, 125))
        gradient.setColorAt(1.0, QColor(44, 123, 229))
        painter.fillRect(self.rect(), gradient)


# ==============================
# MAIN APP
# ==============================
class FaceAttendanceApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Face Recognition Attendance System")
        self.resize(900, 600)

        # ---- state
        self.mode = "idle"   # idle | attendance | register
        self.reg_name = ""
        self.reg_count = 0
        self.reg_total = 30

        self.bg = AnimatedBackground()
        main_layout = QVBoxLayout(self.bg)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        wrapper = QVBoxLayout(self)
        wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper.addWidget(self.bg)

        self.init_home_page()
        self.init_camera_page()
        self.stack.setCurrentWidget(self.home_page)

    # ==============================
    # HOME PAGE
    # ==============================
    def init_home_page(self):
        self.home_page = QWidget()
        layout = QVBoxLayout(self.home_page)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("Face Recognition Attendance System")
        title.setFont(QFont("Arial", 22, QFont.Bold))
        title.setStyleSheet("color: white;")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("AI-based automatic attendance using FaceNet")
        subtitle.setStyleSheet("color: #dddddd;")
        subtitle.setAlignment(Qt.AlignCenter)

        def styled_button(text):
            btn = QPushButton(text)
            btn.setFixedHeight(42)
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 14px;
                    background-color: rgba(0,0,0,120);
                    color: white;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: rgba(0,0,0,180);
                }
            """)
            return btn

        btn_start = styled_button("▶ Start Attendance")
        btn_register = styled_button("➕ Register New Face")
        btn_folder = styled_button("📂 Register From Folder")
        btn_view = styled_button("📄 View Attendance")
        btn_chart = styled_button("📊 Attendance Chart")
        btn_exit = styled_button("❌ Exit")

        btn_start.clicked.connect(self.start_attendance)
        btn_register.clicked.connect(self.start_registration)
        btn_folder.clicked.connect(self.register_from_folder_gui)
        btn_view.clicked.connect(self.view_attendance)
        btn_chart.clicked.connect(self.show_chart)
        btn_exit.clicked.connect(self.close)

        footer = QLabel("Made with ❤️ by Hemant, Gopal, Chetan")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #eeeeee; font-size: 11px;")

        for w in [
            title, subtitle, btn_start, btn_register,
            btn_folder, btn_view, btn_chart, btn_exit, footer
        ]:
            layout.addWidget(w)

        self.stack.addWidget(self.home_page)

    # ==============================
    # CAMERA PAGE
    # ==============================
    def init_camera_page(self):
        self.camera_page = QWidget()
        layout = QVBoxLayout(self.camera_page)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)

        back_btn = QPushButton("⬅ Back to Home")
        back_btn.clicked.connect(self.go_home)

        layout.addWidget(self.image_label)
        layout.addWidget(back_btn)

        self.cap = cv2.VideoCapture(1)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        self.stack.addWidget(self.camera_page)

    # ==============================
    # ACTIONS
    # ==============================
    def start_attendance(self):
        self.mode = "attendance"
        self.stack.setCurrentWidget(self.camera_page)
        self.timer.start(30)

    def start_registration(self):
        name, ok = QInputDialog.getText(self, "Register Face", "Enter name:")
        if ok and name.strip():
            self.mode = "register"
            self.reg_name = name.strip()
            self.reg_count = 0
            self.stack.setCurrentWidget(self.camera_page)
            self.timer.start(30)

    def go_home(self):
        self.timer.stop()
        self.mode = "idle"
        self.stack.setCurrentWidget(self.home_page)

    def register_from_folder_gui(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder:
            return
        name, ok = QInputDialog.getText(self, "Person Name", "Enter name:")
        if ok and name.strip():
            register_from_folder(name.strip(), folder)

    def view_attendance(self):
        name, ok = QInputDialog.getText(self, "View Attendance", "Enter Name:")
        if ok and name.strip():
            summary = get_attendance_summary(name.strip())

        if not summary:
            QMessageBox.information(self, "Attendance", "No records found")
            return

        text = f"""
Total Days: {summary['total_days']}
Present Days: {summary['present_days']}
Attendance %: {summary['percentage']}%
"""

        text += "\n\nMonthly Breakdown:\n"

        for month, count in summary["monthly"].items():
            text += f"{month} : {count} days\n"

        QMessageBox.information(self, "Attendance Summary", text)
        

    def show_chart(self):
        name, ok = QInputDialog.getText(self, "Attendance Chart", "Enter Name:")
        if ok and name.strip():
            show_attendance_chart(name.strip())

    # ==============================
    # CAMERA LOOP
    # ==============================
    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        faces = detect_faces(frame)

        # -------- REGISTER MODE --------
        if self.mode == "register" and faces:
            face = faces[0]

            x, y, w, h = face['bbox']
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            aligned = align_face(frame, face['keypoints'])
            register_face(self.reg_name, aligned)
            self.reg_count += 1

            cv2.rectangle(frame, (0, 0), (frame.shape[1], 60), (0, 180, 0), -1)
            cv2.putText(
                frame,
                f"Registering {self.reg_name} : {self.reg_count}/{self.reg_total}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2
            )

            if self.reg_count >= self.reg_total:
                self.timer.stop()
                self.mode = "idle"
                QMessageBox.information(
                    self, "Success",
                    f"{self.reg_name} registered successfully!"
                )
                self.stack.setCurrentWidget(self.home_page)
                return

        # -------- ATTENDANCE MODE --------
        if self.mode == "attendance":

            for f in faces:

                x, y, w, h = f['bbox']

                # 🔥 Liveness check
                is_real = check_blink(frame)

                if not is_real:
                    cv2.rectangle(frame, (x, y), (x + w, y + h),
                                  (0, 0, 255), 2)
                    cv2.putText(frame, "Blink Required",
                                (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.9, (0, 0, 255), 2)
                    continue

                # ✅ If blink detected → do recognition
                aligned = align_face(frame, f['keypoints'])
                name = recognize_face(aligned)

                if name:
                    mark_attendance(name)

                    cv2.rectangle(frame, (x, y), (x + w, y + h),
                                  (0, 255, 0), 2)
                    cv2.putText(frame, name,
                                (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.9, (0, 255, 0), 2)

        # -------- DISPLAY FRAME --------
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        self.image_label.setPixmap(
            QPixmap.fromImage(
                QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
            )
        )

# ==============================
# RUN APP
# ==============================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FaceAttendanceApp()
    window.show()
    sys.exit(app.exec_())
