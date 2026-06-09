# quality.py
import cv2

def is_blurry(face_img, threshold=100.0):
    """Check if face image is blurry using Laplacian variance."""
    gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    return variance < threshold

def is_frontal(keypoints, tolerance=10):
    """Check frontal pose by comparing eye & nose positions."""
    left_eye = keypoints['left_eye']
    right_eye = keypoints['right_eye']
    nose = keypoints['nose']
    eye_diff = abs(left_eye[1]-right_eye[1])
    nose_center = (left_eye[0]+right_eye[0])//2
    nose_offset = abs(nose[0]-nose_center)
    return eye_diff < tolerance and nose_offset < tolerance
