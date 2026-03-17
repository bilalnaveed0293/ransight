# Ransomware Detector — Full-Stack Web App

Upload a Windows `.exe` file and classify it as **Benign** or **Ransomware** using a trained deep learning model.

---

## Project Structure

```
fyp/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app & /predict endpoint
│   │   ├── model_loader.py         # Loads the ML model (edit MODEL_PATH here)
│   │   └── feature_extractor.py    # Extracts features from .exe files
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── index.css
│   │   ├── main.jsx
│   │   └── components/
│   │       ├── FileUpload.jsx / .css
│   │       └── ResultCard.jsx / .css
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
│
└── README.md
```

---

## Quick Start (Local Development)

### 1. Backend

```bash
cd backend

# Create a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

pip install -r requirements.txt

# ⚠️  Open app/model_loader.py and set MODEL_PATH to your .pkl / .h5 / .pt file
# MODEL_PATH = "./models/ransomware_model.pkl"

uvicorn app.main:app --reload --port 8000
```

API docs: <http://localhost:8000/docs>

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Opens at <http://localhost:5173>.

The frontend calls `http://localhost:8000` by default.  
To override, create `frontend/.env`:

```
VITE_API_URL=http://localhost:8000
```

---

## Before You Run — Plug in Your Model

1. Open **`backend/app/model_loader.py`**
2. Change the placeholder:
   ```python
   MODEL_PATH = "PATH_TO_YOUR_MODEL"
   ```
   to the real path of your trained model file, e.g.:
   ```python
   MODEL_PATH = "./models/ransomware_model.pkl"
   ```
3. Open **`backend/app/feature_extractor.py`** and replace the placeholder feature-extraction logic with the same feature pipeline your model was trained on.

---

## API Reference

### `GET /health`

```json
{ "status": "healthy", "model_loaded": true }
```

### `POST /predict`

- **Content-Type:** `multipart/form-data`
- **Field:** `file` — a `.exe` file

**Response:**

```json
{ "prediction": "Ransomware" }
```

or

```json
{ "prediction": "Benign" }
```

---

## Deployment

### Deploy Frontend → Vercel

1. Push the repo to GitHub.
2. Go to [vercel.com](https://vercel.com) → **New Project** → import the repo.
3. Set:
   - **Root Directory:** `frontend`
   - **Framework Preset:** Vite
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
4. Add environment variable:
   ```
   VITE_API_URL=https://your-backend-url.onrender.com
   ```
5. Deploy.

### Deploy Backend → Render

1. Push the repo to GitHub.
2. Go to [render.com](https://render.com) → **New Web Service** → connect repo.
3. Set:
   - **Root Directory:** `backend`
   - **Runtime:** Docker (it will auto-detect the `Dockerfile`)
4. Make sure your model file is accessible (committed to the repo, or fetched at build time).
5. Deploy.

> After the backend is live, update `VITE_API_URL` in Vercel to point to the Render URL.

### Deploy Backend → Railway

1. Go to [railway.app](https://railway.app) → **New Project** → deploy from GitHub.
2. Set the root directory to `backend` and let Railway detect the Dockerfile.
3. Expose port **8000**.
4. Update `VITE_API_URL` in Vercel.

### Deploy Backend with Docker (anywhere)

```bash
cd backend
docker build -t ransomware-api .
docker run -p 8000:8000 ransomware-api
```

---

## Tech Stack

| Layer    | Technology           |
| -------- | -------------------- |
| Frontend | React + Vite         |
| Backend  | FastAPI + Uvicorn    |
| ML       | scikit-learn / joblib|
| Deploy   | Vercel + Render      |
