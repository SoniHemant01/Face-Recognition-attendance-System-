import sys
import cv2
from PyQt5.QtWidgets import (
    QApplication, QLabel, QPushButton,
    QVBoxLayout, QWidget, QInputDialog,
    QFileDialog, QStackedWidget
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import (
    QImage, QPixmap, QFont,
    QPainter, QLinearGradient, QColor
)

from detection import detect_faces
from alignment import align_face
from recognition import recognize_face
from attendance import mark_attendance
from registration import (
    register_new_user, register_from_folder
)

# ==============================
# ANIMATED BACKGROUND WIDGET
# ==============================
class AnimatedBackground(QWidget):
    def __init__(self):
        super().__init__()
        self.shift = 0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(40)  # smooth animation

    def animate(self):
        self.shift += 1
        if self.shift > self.width():
            self.shift = 0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QLinearGradient(self.shift, 0, self.width(), self.height())

        gradient.setColorAt(0.0, QColor(44, 123, 229))   # blue
        gradient.setColorAt(0.5, QColor(108, 117, 125))  # gray
        gradient.setColorAt(1.0, QColor(44, 123, 229))   # blue

        painter.fillRect(self.rect(), gradient)


# ==============================
# MAIN APP
# ==============================
class FaceAttendanceApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Face Recognition Attendance System")
        self.resize(900, 600)

        self.bg = AnimatedBackground()
        main_layout = QVBoxLayout(self.bg)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        wrapper = QVBoxLayout(self)
        wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper.addWidget(self.bg)

        self.init_home_page()
        self.init_attendance_page()

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
        subtitle.setFont(QFont("Arial", 12))
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
        btn_exit = styled_button("❌ Exit")

        btn_start.clicked.connect(self.start_attendance)
        btn_register.clicked.connect(self.register_face)
        btn_folder.clicked.connect(self.register_from_folder_gui)
        btn_exit.clicked.connect(self.close)

        footer = QLabel("Made with ❤️ by Hemant, Gopal, Chetan")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #eeeeee; font-size: 11px;")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(30)
        layout.addWidget(btn_start)
        layout.addWidget(btn_register)
        layout.addWidget(btn_folder)
        layout.addSpacing(10)
        layout.addWidget(btn_exit)
        layout.addSpacing(40)
        layout.addWidget(footer)

        self.stack.addWidget(self.home_page)

    # ==============================
    # ATTENDANCE PAGE
    # ==============================
    def init_attendance_page(self):
        self.attendance_page = QWidget()
        layout = QVBoxLayout(self.attendance_page)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)

        back_btn = QPushButton("⬅ Back to Home")
        back_btn.setFixedHeight(36)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0,0,0,140);
                color: white;
                border-radius: 6px;
            }
        """)
        back_btn.clicked.connect(self.go_home)

        layout.addWidget(self.image_label)
        layout.addWidget(back_btn)

        self.cap = cv2.VideoCapture(1)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        self.stack.addWidget(self.attendance_page)

    # ==============================
    # ACTIONS
    # ==============================
    def start_attendance(self):
        self.stack.setCurrentWidget(self.attendance_page)
        self.timer.start(30)

    def go_home(self):
        self.timer.stop()
        self.stack.setCurrentWidget(self.home_page)

    def register_face(self):
        name, ok = QInputDialog.getText(self, "Register Face", "Enter name:")
        if ok and name.strip():
            register_new_user(name.strip())

    def register_from_folder_gui(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder:
            return
        name, ok = QInputDialog.getText(self, "Person Name", "Enter name:")
        if ok and name.strip():
            register_from_folder(name.strip(), folder)

    # ==============================
    # CAMERA LOOP
    # ==============================
    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        faces = detect_faces(frame)

        for f in faces:
            aligned = align_face(frame, f['keypoints'])
            name = recognize_face(aligned)

            if name:
                mark_attendance(name)
                x, y, w, h = f['bbox']
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, name, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        self.image_label.setPixmap(
            QPixmap.fromImage(QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888))
        )


# ==============================
# RUN APP
# ==============================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FaceAttendanceApp()
    window.show()
    sys.exit(app.exec_())
