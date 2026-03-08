import os
from tensorflow import keras

# ── Placeholder: replace with the actual path to your .keras model file ──
MODEL_PATH = "C:\\Users\\bilal\\Downloads\\ransomware_model_v2_custom (2).keras"
# Example:
#   MODEL_PATH = "./models/ransomware_model.keras"
# ──────────────────────────────────────────────────────────────────────────

_model = None


def load_model():
    """Load the Keras model from MODEL_PATH. Called once at startup."""
    global _model
    if not os.path.isfile(MODEL_PATH):
        print(
            f"⚠️  Model file not found at '{MODEL_PATH}'. "
            "Replace MODEL_PATH in model_loader.py with the real path to your .keras model."
        )
        return
    _model = keras.models.load_model(MODEL_PATH)
    print(f"✅ Model loaded from {MODEL_PATH}")


def get_model():
    """Return the loaded model (or None if not yet loaded)."""
    return _model
