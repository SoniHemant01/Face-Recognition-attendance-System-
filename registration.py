# registration.py
import os
import cv2
from detection import detect_faces
from alignment import align_face
from updating_recognition import register_face

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Hide warnings

def register_new_user(name, num_samples=5):
    cap = cv2.VideoCapture(1)
    count = 0
    while count < num_samples:
        ret, frame = cap.read()
        faces = detect_faces(frame)
        if faces:
            aligned = align_face(frame, faces[0]['keypoints'])
            register_face(name, aligned)
            count += 1
            print(f"[INFO] Captured {count}/{num_samples}")
        cv2.imshow("Register Face", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()

# Registraiton from folder of images 
 
def register_from_folder(person_name, folder_path):
    if not os.path.exists(folder_path):
        print("❌ Folder does not exist")
        return

    image_files = [
        f for f in os.listdir(folder_path)
        if f.lower().endswith(('.jpg', '.jpeg', '.png'))
    ]

    print(f"[INFO] Registering {person_name} from folder...")
    count = 0

    for img_name in image_files:
        img_path = os.path.join(folder_path, img_name)
        image = cv2.imread(img_path)

        if image is None:
            continue

        faces = detect_faces(image)
        if not faces:
            continue

        aligned = align_face(image, faces[0]['keypoints'])
        register_face(person_name, aligned)
        count += 1

    print(f"✅ {count} embeddings stored for {person_name}")
