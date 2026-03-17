import os
import tempfile
import shutil
import numpy as np

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.model_loader import load_model, get_model
from app.lstm_model_loader import load_lstm_model, get_lstm_model, predict_with_lstm
from app.feature_extractor import extract_features
from app.behavioral_feature_extractor import (
    extract_behavioral_features,
    format_behavioral_features_for_lstm
)

app = FastAPI(title="Ransomware Detector API (Hybrid)", version="2.0.0")

# Allow the React dev-server and common deployment origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Load both CNN and LSTM models at startup."""
    load_model()  # Load CNN
    load_lstm_model()  # Load LSTM


# ── Endpoints ───────────────────────────────────────────────────────────


@app.get("/health")
async def health():
    """Health check endpoint."""
    cnn_loaded = get_model() is not None
    lstm_loaded = get_lstm_model() is not None
    
    return {
        "status": "healthy",
        "cnn_model_loaded": cnn_loaded,
        "lstm_model_loaded": lstm_loaded,
        "hybrid_enabled": cnn_loaded and lstm_loaded,
    }


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    """
    Hybrid Ransomware Detection Pipeline:
    
    1. Accept uploaded .exe file
    2. Run CNN static analysis (image-based)
    3. If CNN confidence < threshold (0.6), run LSTM behavioral analysis
    4. Return final prediction with confidence and analysis method used
    
    Response format:
    {
        "prediction": "Ransomware" | "Benign",
        "confidence": 0.95,
        "method": "CNN" | "LSTM" | "Hybrid (CNN+LSTM)",
        "details": {
            "cnn_prediction": "Benign",
            "cnn_confidence": 0.45,
            "lstm_prediction": "Ransomware",
            "lstm_confidence": 0.78
        }
    }
    """
    
    # Validate file extension
    if not file.filename or not file.filename.lower().endswith(".exe"):
        raise HTTPException(
            status_code=400,
            detail="Only .exe files are accepted.",
        )
    
    cnn_model = get_model()
    if cnn_model is None:
        raise HTTPException(
            status_code=503,
            detail="CNN model is not loaded. Set MODEL_PATH in model_loader.py and restart.",
        )
    
    # Save the upload to a temp file
    tmp_path = None
    try:
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp_path = tmp.name
            shutil.copyfileobj(file.file, tmp)
        
        # ── STEP 1: CNN Static Analysis ──
        features = extract_features(tmp_path)
        cnn_prediction = cnn_model.predict(np.array([features]))
        cnn_confidence = float(cnn_prediction[0][0])
        cnn_label = "Ransomware" if cnn_confidence >= 0.5 else "Benign"
        
        # Initialize response details
        details = {
            "cnn_prediction": cnn_label,
            "cnn_confidence": cnn_confidence,
        }
        
        # ── STEP 2: Confidence-Based Routing ──
        # If CNN confidence is low (between 0.3 and 0.7), use LSTM for confirmation
        CNN_CONFIDENCE_THRESHOLD = 0.6
        final_label = cnn_label
        final_confidence = cnn_confidence
        method_used = "CNN"
        
        if abs(cnn_confidence - 0.5) < (1 - CNN_CONFIDENCE_THRESHOLD):
            # CNN is uncertain, use LSTM for behavioral analysis
            lstm_model = get_lstm_model()
            
            if lstm_model is not None:
                try:
                    # Extract behavioral features
                    behavioral_features = extract_behavioral_features(tmp_path)
                    formatted_features = format_behavioral_features_for_lstm(behavioral_features)
                    
                    # Run LSTM prediction
                    lstm_label, lstm_confidence = predict_with_lstm(formatted_features)
                    
                    # Store LSTM details
                    details["lstm_prediction"] = lstm_label
                    details["lstm_confidence"] = lstm_confidence
                    
                    # Ensemble: Weight CNN and LSTM predictions
                    # Simple averaging (can be tuned)
                    ensemble_confidence = (cnn_confidence + lstm_confidence) / 2.0
                    final_label = "Ransomware" if ensemble_confidence >= 0.5 else "Benign"
                    final_confidence = ensemble_confidence
                    method_used = "Hybrid (CNN+LSTM)"
                    
                except Exception as lstm_error:
                    # LSTM failed, fall back to CNN
                    print(f"Warning: LSTM prediction failed: {lstm_error}")
                    method_used = "CNN (LSTM failed)"
        
        return {
            "prediction": final_label,
            "confidence": final_confidence,
            "method": method_used,
            "details": details,
        }
    
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)