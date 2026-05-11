"""X-ray inference — delegates to standalone subprocess script to avoid venv TF dependency."""

import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict

from .config import MODEL_PATH

logger = logging.getLogger(__name__)

# Try to find a Python interpreter with TensorFlow installed
_TF_PYTHON = None


def _find_tf_python():
    """Find a Python interpreter that has TensorFlow installed."""
    global _TF_PYTHON
    if _TF_PYTHON is not None:
        return _TF_PYTHON

    candidates = [
        sys.executable,  # current venv Python
        r"C:\Users\H\AppData\Local\Programs\Python\Python310\python.exe",
        r"C:\Python310\python.exe",
        "python",
        "python3",
    ]
    for py in candidates:
        try:
            result = subprocess.run(
                [py, "-c", "import tensorflow; print('ok')"],
                capture_output=True, text=True, timeout=10, check=False
            )
            if result.returncode == 0 and "ok" in result.stdout:
                _TF_PYTHON = py
                return py
        except Exception:
            continue
    _TF_PYTHON = False
    return False


def analyze_xray(image_path: str) -> Optional[Dict]:
    """
    Analyze an X-ray image via subprocess inference script.
    Returns dict with diagnosis, probability, body_part, note, class_probabilities.
    """
    if not MODEL_PATH.exists():
        return None

    tf_python = _find_tf_python()
    if tf_python is False:
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
