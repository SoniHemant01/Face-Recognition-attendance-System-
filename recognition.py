#used to update recognition.py
import numpy as np
import pickle
import os
import cv2
from scipy.spatial.distance import cosine
from keras_facenet import FaceNet

# ==============================
# PATHS
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EMBEDDINGS_PATH = os.path.join(BASE_DIR, "embeddings", "embeddings.pkl")

# ==============================
# LOAD FACENET
# ==============================
facenet_model = FaceNet()
print("✅ FaceNet loaded successfully (keras-facenet)")

# ==============================
# LOAD EXISTING EMBEDDINGS
# ==============================
registered_faces = {}

if os.path.exists(EMBEDDINGS_PATH):
    try:
        with open(EMBEDDINGS_PATH, "rb") as f:
            registered_faces = pickle.load(f)

        # 🔥 IMPORTANT FIX: ensure all values are LIST
        for name in registered_faces:
            if isinstance(registered_faces[name], np.ndarray):
                registered_faces[name] = [registered_faces[name]]

    except (EOFError, pickle.UnpicklingError):
        print("⚠️ embeddings.pkl corrupted. Recreating...")
        registered_faces = {}


# ==============================
# PREPROCESS FACE
# ==============================
def preprocess_face(face_img):
    face_img = cv2.resize(face_img, (160, 160))
    face_img = face_img.astype("float32")
    return face_img

# ==============================
# GET EMBEDDING
# ==============================
def get_embedding(face_img):
    face = preprocess_face(face_img)
    embedding = facenet_model.embeddings([face])[0]
    return embedding

# ==============================
# REGISTER FACE (MULTI-EMBEDDING)
# ==============================
def register_face(name, face_img):
    embedding = get_embedding(face_img)

    if name in registered_faces:
        registered_faces[name].append(embedding)
    else:
        registered_faces[name] = [embedding]

    os.makedirs(os.path.dirname(EMBEDDINGS_PATH), exist_ok=True)
    with open(EMBEDDINGS_PATH, "wb") as f:
        pickle.dump(registered_faces, f)

    print(f"✅ Face registered: {name}")

# ==============================
# RECOGNIZE FACE
# ==============================
def recognize_face(face_img, threshold=0.5):
    embedding = get_embedding(face_img)

    best_match = None
    best_score = -1

    for name, embeddings in registered_faces.items():
        for reg_emb in embeddings:
            sim = 1 - cosine(embedding, reg_emb)
            if sim > best_score:
                best_score = sim
                best_match = name

    if best_score > threshold:
        return best_match

    return None
