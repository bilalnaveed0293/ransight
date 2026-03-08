import os
import tempfile
import shutil

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.model_loader import load_model, get_model
from app.feature_extractor import extract_features

app = FastAPI(title="Ransomware Detector API", version="1.0.0")

# Allow the React dev-server and common deployment origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    load_model()


# ── Endpoints ─────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "model_loaded": get_model() is not None,
    }


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    """
    Accept an uploaded .exe file, extract features,
    run inference, and return 'Benign' or 'Ransomware'.
    """
    # Validate file extension
    if not file.filename or not file.filename.lower().endswith(".exe"):
        raise HTTPException(
            status_code=400,
            detail="Only .exe files are accepted.",
        )

    model = get_model()
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Model is not loaded. Set MODEL_PATH in model_loader.py and restart.",
        )

    # Save the upload to a temp file so feature extraction can read it
    tmp_path = None
    try:
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp_path = tmp.name
            shutil.copyfileobj(file.file, tmp)

        features = extract_features(tmp_path)
        import numpy as np
        prediction = model.predict(np.array([features]))
        label = "Ransomware" if float(prediction[0][0]) >= 0.5 else "Benign"
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    return {"prediction": label}
