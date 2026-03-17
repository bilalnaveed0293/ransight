import os
import joblib  # or pickle, depending on how your LSTM was saved
import pandas as pd
from typing import Optional

# ── Configure LSTM Model Path ──
# Replace with the actual path to your trained LSTM model file
# Supported formats: .pkl, .joblib, .h5 (Keras), .pt (PyTorch)
LSTM_MODEL_PATH = r"C:\Users\bilal\Desktop\ransomware_lstm_dynamic.keras\model.weights.h5"

_lstm_model = None


def load_lstm_model():
    """Load the LSTM model from LSTM_MODEL_PATH. Called once at startup."""
    global _lstm_model
    
    if not os.path.isfile(LSTM_MODEL_PATH):
        print(
            f"⚠️  LSTM model file not found at '{LSTM_MODEL_PATH}'. "
            "Replace LSTM_MODEL_PATH in lstm_model_loader.py with the real path to your model."
        )
        return False
    
    try:
        # Try joblib first (scikit-learn, XGBoost, etc.)
        _lstm_model = joblib.load(LSTM_MODEL_PATH)
        print(f"✅ LSTM model loaded from {LSTM_MODEL_PATH} (joblib)")
        return True
    except Exception as e:
        print(f"⚠️  Failed to load LSTM model: {e}")
        return False


def get_lstm_model():
    """Return the loaded LSTM model (or None if not loaded)."""
    return _lstm_model


def predict_with_lstm(features_dict: dict) -> tuple:
    """
    Make a prediction with the LSTM model.
    
    Args:
        features_dict: Dictionary with keys ApiCall_0...ApiCall_499, Dll_0...Dll_9
    
    Returns:
        Tuple: (prediction_label, confidence_score)
        - prediction_label: "Ransomware" or "Benign"
        - confidence_score: Float between 0 and 1
    """
    model = get_lstm_model()
    if model is None:
        raise RuntimeError("LSTM model not loaded")
    
    try:
        # Convert dict to DataFrame (LSTM expects this format)
        df = pd.DataFrame([features_dict])
        
        # Make prediction
        prediction = model.predict(df)
        
        # Extract probability/confidence
        if hasattr(model, 'predict_proba'):
            # Scikit-learn style
            probas = model.predict_proba(df)[0]
            # Assuming class 1 = Ransomware, class 0 = Benign
            confidence = probas[1] if len(probas) > 1 else prediction[0]
        else:
            # Direct prediction or custom model
            confidence = float(prediction[0])
        
        label = "Ransomware" if confidence >= 0.5 else "Benign"
        
        return label, float(confidence)
    
    except Exception as e:
        print(f"Error during LSTM prediction: {e}")
        raise