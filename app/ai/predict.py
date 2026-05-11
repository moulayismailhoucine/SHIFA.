"""X-ray inference — loads model in-process when TF is available, falls back to subprocess."""

import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict

from .config import MODEL_PATH

logger = logging.getLogger(__name__)

# Cached in-process model (for Docker/Render where TF is installed in same env)
_model = None
_TF_AVAILABLE = None


def _check_tf():
    """Check if TensorFlow is importable in this Python process."""
    global _TF_AVAILABLE
    if _TF_AVAILABLE is not None:
        return _TF_AVAILABLE
    try:
        import tensorflow
        _TF_AVAILABLE = True
        return True
    except Exception as e:
        logger.warning(f"TensorFlow not available in-process: {e}")
        _TF_AVAILABLE = False
        return False


def _load_model():
    """Load Keras model into memory (cached)."""
    global _model
    if _model is not None:
        return _model
    try:
        from tensorflow import keras
        if not MODEL_PATH.exists():
            return None
        _model = keras.models.load_model(str(MODEL_PATH))
        logger.info(f"Loaded model from {MODEL_PATH}")
        return _model
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return None


def _preprocess(image_path: str):
    """Load and preprocess image for MobileNetV2."""
    from tensorflow import keras
    import numpy as np
    from PIL import Image
    img = Image.open(image_path).convert("RGB")
    img = img.resize((224, 224))
    x = np.array(img, dtype=np.float32)
    x = keras.applications.mobilenet_v2.preprocess_input(x)
    return np.expand_dims(x, axis=0)


def _analyze_in_process(image_path: str) -> Optional[Dict]:
    """Run inference directly in this Python process."""
    if not _check_tf():
        return None
    model = _load_model()
    if model is None:
        return None
    try:
        x = _preprocess(image_path)
        probs = model.predict(x, verbose=0)[0]
        idx = int(probs.argmax())
        confidence = float(probs[idx]) * 100
        labels = ["Normal", "Fracture"]
        diagnosis = labels[idx] if idx < len(labels) else "Unknown"
        return {
            "diagnosis": diagnosis,
            "probability": round(confidence, 1),
            "body_part": "Unknown",
            "note": "AI analysis completed",
            "class_probabilities": {labels[i]: round(float(probs[i]) * 100, 1) for i in range(min(len(labels), len(probs)))}
        }
    except Exception as e:
        logger.error(f"In-process inference failed: {e}")
        return None


def _find_tf_python():
    """Find a Python interpreter that has TensorFlow installed (subprocess fallback)."""
    candidates = [
        sys.executable,
        r"C:\Users\H\AppData\Local\Programs\Python\Python310\python.exe",
        r"C:\Python310\python.exe",
        "python", "python3",
    ]
    for py in candidates:
        try:
            result = subprocess.run(
                [py, "-c", "import tensorflow; print('ok')"],
                capture_output=True, text=True, timeout=10, check=False
            )
            if result.returncode == 0 and "ok" in result.stdout:
                return py
        except Exception:
            continue
    return None


def _analyze_subprocess(image_path: str) -> Optional[Dict]:
    """Run inference via subprocess (for local Windows dev)."""
    tf_python = _find_tf_python()
    if not tf_python:
        logger.error("No Python with TensorFlow found")
        return None
    script_path = Path(__file__).with_name("inference.py")
    try:
        result = subprocess.run(
            [tf_python, str(script_path), image_path],
            capture_output=True, text=True, timeout=60, check=False
        )
        if result.returncode != 0:
            logger.error(f"AI subprocess failed (rc={result.returncode}): stderr={result.stderr[:500]}")
            return None
        data = json.loads(result.stdout.strip().splitlines()[-1])
        if "error" in data:
            logger.error(f"AI inference error: {data['error']}")
            return None
        return data
    except Exception as e:
        logger.error(f"AI exception: {e}")
        return None


def analyze_xray(image_path: str) -> Optional[Dict]:
    """
    Analyze an X-ray image.
    Tries in-process first (Docker/Render), falls back to subprocess (local Windows).
    Returns dict with diagnosis, probability, body_part, note, class_probabilities.
    """
    if not MODEL_PATH.exists():
        logger.warning(f"Model not found at {MODEL_PATH}")
        return None

    # 1. Try in-process (fast, works in Docker where TF is installed)
    result = _analyze_in_process(image_path)
    if result is not None:
        return result

    # 2. Fallback to subprocess (local Windows dev without TF in venv)
    logger.info("Falling back to subprocess inference")
    return _analyze_subprocess(image_path)
