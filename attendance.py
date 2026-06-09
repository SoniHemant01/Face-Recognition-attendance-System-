# attendance.py
import pandas as pd
from datetime import datetime
import os

# ==============================
# ATTENDANCE DIRECTORY
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ATTENDANCE_DIR = os.path.join(BASE_DIR, "logs", "attendance")
os.makedirs(ATTENDANCE_DIR, exist_ok=True)

# ==============================
# MARK ATTENDANCE (ONCE PER DAY)
# ==============================
def mark_attendance(name):
    today = datetime.now().strftime("%Y-%m-%d")
    time_now = datetime.now().strftime("%H:%M:%S")

    file_path = os.path.join(ATTENDANCE_DIR, f"{today}.csv")

    # Case 1: file does not exist
    if not os.path.exists(file_path):
        df = pd.DataFrame(columns=["Name", "Time"])
    else:
        df = pd.read_csv(file_path)

    # ✅ Check: already marked today?
    if name in df["Name"].values:
        print(f"⚠️ Attendance already marked today for {name}")
        return

    # ✅ Add attendance
    new_row = {
        "Name": name,
        "Time": time_now
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(file_path, index=False)

    print(f"✅ Attendance marked for {name} ({today})")
