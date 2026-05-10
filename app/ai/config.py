"""AI module configuration."""

from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
MODEL_DIR = BASE_DIR / "models"
MODEL_PATH = MODEL_DIR / "bone_fracture_model.h5"
MURA_DIR = BASE_DIR / "data" / "mura"

MODEL_DIR.mkdir(parents=True, exist_ok=True)

# Model config
IMG_SIZE = (224, 224)
BATCH_SIZE = 16
EPOCHS_FROZEN = 5
EPOCHS_FINE = 5
LEARNING_RATE_FROZEN = 1e-3
LEARNING_RATE_FINE = 1e-5

# Classes (MURA: binary normal/abnormal)
CLASS_NAMES = ["Normal", "Abnormal"]

# Body parts in MURA filenames
BODY_PARTS = {
    "XR_WRIST": "Wrist",
    "XR_ELBOW": "Elbow",
    "XR_SHOULDER": "Shoulder",
    "XR_HUMERUS": "Humerus",
    "XR_FOREARM": "Forearm",
    "XR_HAND": "Hand",
    "XR_FINGER": "Finger",
}

# Clinical notes based on prediction
CLINICAL_NOTES = {
    "Normal": "No obvious fracture detected. Clinical correlation advised.",
    "Abnormal": "Abnormality detected. Recommend radiologist review for fracture confirmation.",
}
