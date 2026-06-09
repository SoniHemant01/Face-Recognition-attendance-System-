import cv2
import mediapipe as mp
import numpy as np

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

# Eye landmark indices
LEFT_EYE = [33, 160, 158, 133, 153, 144]

def eye_aspect_ratio(landmarks, eye_indices):
    points = [landmarks[i] for i in eye_indices]

    vertical1 = np.linalg.norm(points[1] - points[5])
    vertical2 = np.linalg.norm(points[2] - points[4])
    horizontal = np.linalg.norm(points[0] - points[3])

    ear = (vertical1 + vertical2) / (2.0 * horizontal)
    return ear


def check_blink(frame):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    if not results.multi_face_landmarks:
        return False

    for face_landmarks in results.multi_face_landmarks:
        h, w, _ = frame.shape

        landmarks = []
        for lm in face_landmarks.landmark:
            landmarks.append(np.array([lm.x * w, lm.y * h]))

        ear = eye_aspect_ratio(landmarks, LEFT_EYE)

        if ear < 0.20:  # threshold
            return True

    return False
