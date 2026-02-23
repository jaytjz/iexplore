from __future__ import annotations

import io
import os
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image

from .inference import InferenceService

ROOT_DIR = Path(__file__).resolve().parent.parent
ML_DIR = Path(__file__).resolve().parent
WEBSITE_DIR = ROOT_DIR / "website"

WEIGHTS_PATH = Path(os.getenv("WEIGHTS_PATH", str(ML_DIR / "best_model.pth"))).resolve()
TRAINING_DIR = Path(os.getenv("TRAINING_DIR", str(ML_DIR / "Training"))).resolve()
TEMPERATURE = float(os.getenv("TEMPERATURE", "1.0"))
NEIGHBORS_K = int(os.getenv("NEIGHBORS_K", "3"))

raw_names = os.getenv("CLASS_NAMES", "").strip()
CLASS_NAMES = [x.strip() for x in raw_names.split(",") if x.strip()] if raw_names else None

app = FastAPI(title="Brain Tumor Inference API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

service: InferenceService | None = None
service_error: str | None = None
try:
    service = InferenceService(
        weights_path=WEIGHTS_PATH,
        training_dir=TRAINING_DIR if TRAINING_DIR.exists() else None,
        class_names=CLASS_NAMES,
        temperature=TEMPERATURE,
        neighbors_k=NEIGHBORS_K,
    )
except Exception as exc:
    service_error = str(exc)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok" if service is not None else "degraded"}


"""
Returns 
{
"pred_label": string 
"confidence": float
"temperature": float
"probabilities": [{pred_label: string, probability: float}]
"gradcam_overlay": string - Image url
"neighbors": [
    {
        "pred_label": string,
        "similarity": float,
        "image": string - Image url
        "path": string - input image path,
    }
}
"""
@app.post("/api/predict")
async def predict(file: UploadFile = File(...)) -> JSONResponse:
    if service is None:
        detail = f"Service not ready: {service_error or 'unknown initialization error'}"
        raise HTTPException(status_code=500, detail=detail)

    if not file.filename:
        raise HTTPException(status_code=400, detail="Empty filename")

    try:
        content = await file.read()
        image = Image.open(io.BytesIO(content)).convert("RGB")
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid image") from exc

    try:
        result = service.predict(image)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Inference failed: {exc}") from exc
        
    print(result)

    return JSONResponse(result)


if WEBSITE_DIR.exists():
    app.mount("/", StaticFiles(directory=str(WEBSITE_DIR), html=True), name="site")
