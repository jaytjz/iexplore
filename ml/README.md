## Backend + Inference Setup

This project now includes a FastAPI inference server that:
- loads `best_model.pth`
- predicts class + confidence
- returns Grad-CAM overlay
- returns nearest training neighbors using embedding similarity

### 1) Install dependencies

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2) Place model and training data

- Put weights at `ml/best_model.pth` (or set `WEIGHTS_PATH`).
- Put training images at `ml/Training/<class_name>/*.jpg` (or set `TRAINING_DIR`).

### 3) Run the API + website

From the repo root:

```bash
uvicorn ml.app:app --host 0.0.0.0 --port 8000 --reload
```

Then open:

`http://localhost:8000`

### Optional environment variables

- `WEIGHTS_PATH` (default: `ml/best_model.pth`)
- `TRAINING_DIR` (default: `ml/Training`)
- `CLASS_NAMES` (comma-separated, e.g. `glioma,meningioma,notumor,pituitary`)
- `TEMPERATURE` (default: `1.0`)
- `NEIGHBORS_K` (default: `3`)
