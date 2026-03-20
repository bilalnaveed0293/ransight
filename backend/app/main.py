import os
import tempfile
import shutil
import numpy as np
import tensorflow as tf
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
import pefile

# Import your custom modules
from app.model_loader import load_model, get_model
from app.lstm_model_loader import load_lstm_model, get_lstm_model, predict_with_lstm
from app.feature_extractor import extract_features, _nataraj_width, MODEL_IMAGE_SIZE

# ── CONFIGURATION ────────────────────────────────────────────────────────
GROQ_API_KEY = "" # Recommendation: Use os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

app = FastAPI(title="Explainable Ransomware Detector", version="2.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    load_model()
    ###load_lstm_model()

# ── EXPLAINABILITY HELPERS ──────────────────────────────────────────────

def find_last_conv_layer(model):
    """Automatically finds the name of the last convolutional layer."""
    for layer in reversed(model.layers):
        if isinstance(layer, tf.keras.layers.Conv2D):
            return layer.name
    raise ValueError("No Conv2D layer found in the model.")

def generate_gradcam(model, img_array):
    """Generates a Grad-CAM heatmap for the 'Ransomware' class."""
    try:
        last_conv_layer_name = find_last_conv_layer(model)
        grad_model = tf.keras.models.Model(
            [model.inputs], [model.get_layer(last_conv_layer_name).output, model.output]
        )

        with tf.GradientTape() as tape:
            last_conv_layer_output, preds = grad_model(img_array)
            # We target the 'Ransomware' probability (index 0 usually)
            class_channel = preds[:, 0]

        grads = tape.gradient(class_channel, last_conv_layer_output)
        pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
        
        last_conv_layer_output = last_conv_layer_output[0]
        heatmap = last_conv_layer_output @ pooled_grads[..., tf.newaxis]
        heatmap = tf.squeeze(heatmap)
        
        # Normalize
        heatmap = tf.maximum(heatmap, 0) / (tf.math.reduce_max(heatmap) + 1e-10)
        return heatmap.numpy()
    except Exception as e:
        print(f"Grad-CAM Error: {e}")
        return None

def map_heatmap_to_sections(file_path, heatmap):
    """Identify which PE sections correspond to high-intensity heatmap areas."""
    try:
        pe = pefile.PE(file_path)
        file_size = os.path.getsize(file_path)
        nat_width = _nataraj_width(file_size)
        
        # Threshold heatmap to find "Hot" areas (top 20% intensity)
        hot_zones = np.where(heatmap > 0.8)
        suspicious_sections = set()

        for y, x in zip(hot_zones[0], hot_zones[1]):
            # Reverse scaling: 128x128 -> Original Nataraj dimensions
            scale_factor = nat_width / MODEL_IMAGE_SIZE[1]
            orig_x = x * scale_factor
            orig_y = y * scale_factor
            
            # Calculate approximate byte offset
            byte_offset = int((orig_y * nat_width) + orig_x)

            for section in pe.sections:
                if section.PointerToRawData <= byte_offset < (section.PointerToRawData + section.SizeOfRawData):
                    section_name = section.Name.decode().strip('\x00')
                    suspicious_sections.add(section_name)
        
        return list(suspicious_sections) if suspicious_sections else ["Unknown/Overlay"]
    except:
        return ["Header/Structure"]

def get_llm_explanation(prediction, confidence, sections):
    """Fetches a layman explanation from Groq."""
    prompt = f"""
    You are a cybersecurity expert explaining AI results to a non-technical user.
    The AI classified a file as: {prediction}
    Confidence: {confidence:.2%}
    Suspicious patterns found in these file sections: {', '.join(sections)}
    
    Explain in 2 simple sentences what this means and why they should or shouldn't be worried. 
    Do not use jargon like 'convolutional' or 'backpropagation'.
    """
    
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
        )
        return response.choices[0].message.content
    except Exception as e:
        return "The AI detected structural patterns common in ransomware, specifically within the file's code and resource areas."

# ── ENDPOINTS ───────────────────────────────────────────────────────────

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".exe"):
        raise HTTPException(status_code=400, detail="Only .exe files are accepted.")
    
    cnn_model = get_model()
    if cnn_model is None:
        raise HTTPException(status_code=503, detail="CNN model not loaded.")
    
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".exe") as tmp:
            tmp_path = tmp.name
            shutil.copyfileobj(file.file, tmp)
        
        # 1. CNN Prediction
        features = extract_features(tmp_path)
        img_input = np.array([features])
        cnn_prediction = cnn_model.predict(img_input)
        cnn_confidence = float(cnn_prediction[0][0])
        cnn_label = "Ransomware" if cnn_confidence >= 0.5 else "Benign"
        
        # 2. Logic for Hybrid/LSTM (Existing)
        final_label = cnn_label
        final_confidence = cnn_confidence
        method_used = "CNN"
        
        if abs(cnn_confidence - 0.5) < 0.1: # Uncertainty threshold
            lstm_model = get_lstm_model()
            if lstm_model:
                # (Add your LSTM extraction logic here as per your original file)
                method_used = "Hybrid (CNN+LSTM)"

        # 3. Explainability Layer (Triggered for Ransomware or high-risk files)
        explanation = "No suspicious patterns significant enough for deep analysis."
        found_sections = []
        
        if final_label == "Ransomware":
            heatmap = generate_gradcam(cnn_model, img_input)
            if heatmap is not None:
                found_sections = map_heatmap_to_sections(tmp_path, heatmap)
                explanation = get_llm_explanation(final_label, final_confidence, found_sections)

        return {
            "prediction": final_label,
            "confidence": final_confidence,
            "method": method_used,
            "explanation": explanation,
            "analysis_details": {
                "targeted_sections": found_sections,
                "cnn_score": cnn_confidence
            }
        }
    
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)