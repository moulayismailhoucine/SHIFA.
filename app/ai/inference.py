"""Standalone X-ray inference script — can be run by any Python that has TensorFlow.

Usage:
    python app/ai/inference.py <image_path>
Output (JSON to stdout):
    {"diagnosis": "Normal", "probability": 87.5, "body_part": "Wrist", "note": "..."}
"""

import json
import os
import sys
from pathlib import Path

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

try:
    import numpy as np
    import tensorflow as tf
    from tensorflow import keras
    TF_AVAILABLE = True
except Exception as _tf_err:
    TF_AVAILABLE = False
    _TF_ERROR = str(_tf_err)

# ── Config (duplicated here to keep script standalone) ────────────
IMG_SIZE = (224, 224)
CLASS_NAMES = ["Normal", "Abnormal"]
BODY_PARTS = {
    "XR_WRIST": "Wrist", "XR_ELBOW": "Elbow", "XR_SHOULDER": "Shoulder",
    "XR_HUMERUS": "Humerus", "XR_FOREARM": "Forearm", "XR_HAND": "Hand",
    "XR_FINGER": "Finger",
}
CLINICAL_NOTES = {
    "Normal": "No obvious fracture detected. Clinical correlation advised.",
    "Abnormal": "Abnormality detected. Recommend radiologist review for fracture confirmation.",
}


def _detect_body_part(file_path: str) -> str:
    path_upper = file_path.upper()
    for key, label in BODY_PARTS.items():
        if key in path_upper:
            return label
    return "Unknown"


def _load_model():
    if not TF_AVAILABLE:
        return None
    script_dir = Path(__file__).parent
    model_path = script_dir / "models" / "bone_fracture_model.h5"
    if not model_path.exists():
        return None
    try:
        class CustomDense(keras.layers.Dense):
            def __init__(self, **kwargs):
                kwargs.pop('quantization_config', None)
                super().__init__(**kwargs)
        return keras.models.load_model(str(model_path), custom_objects={'Dense': CustomDense})
    except Exception as e:
        print(json.dumps({"error": f"Failed to load model: {e}"}), file=sys.stderr)
        return None


def _preprocess(image_path: str):
    img = keras.utils.load_img(image_path, target_size=IMG_SIZE, color_mode="rgb")
    arr = keras.utils.img_to_array(img)
    arr = keras.applications.mobilenet_v2.preprocess_input(arr)
    return np.expand_dims(arr, axis=0)


def analyze(image_path: str) -> dict:
    if not TF_AVAILABLE:
        return {"error": f"TensorFlow not available: {_TF_ERROR}"}

    model = _load_model()
    if model is None:
        return {"error": "Model not found. Train first with: python -m app.ai.train"}

    x = _preprocess(image_path)
    raw_probs = model.predict(x, verbose=0)[0]

    if len(raw_probs) == 1:
        prob_abnormal = float(raw_probs[0])
        prob_normal = 1.0 - prob_abnormal
        probs = [prob_normal, prob_abnormal]
    else:
        probs = [float(p) for p in raw_probs]

    pred_idx = int(np.argmax(probs))
    diagnosis = CLASS_NAMES[pred_idx]
    probability = float(probs[pred_idx] * 100)

    body_part = _detect_body_part(image_path)
    note = CLINICAL_NOTES.get(diagnosis, "AI analysis complete. Please verify with a specialist.")
    if 40 <= probability <= 60:
        note = "Low confidence prediction. Strongly recommend specialist review."

    class_probs = {CLASS_NAMES[i]: float(probs[i] * 100) for i in range(min(len(CLASS_NAMES), len(probs)))}

    return {
        "diagnosis": diagnosis,
        "probability": round(probability, 1),
        "body_part": body_part,
        "note": note,
        "class_probabilities": class_probs,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python inference.py <image_path>"}))
        sys.exit(1)

    result = analyze(sys.argv[1])
    print(json.dumps(result))
