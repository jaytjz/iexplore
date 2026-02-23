from __future__ import annotations

import base64
import io
import os
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from matplotlib import cm
from PIL import Image
from torch.utils.data import DataLoader
from torchvision import datasets
from torchvision.models import resnet50
from torchvision.transforms import v2

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


@dataclass
class NeighborResult:
    label: str
    similarity: float
    image_data_url: str
    path: str


class InferenceService:
    def __init__(
        self,
        weights_path: Path,
        training_dir: Path | None,
        class_names: list[str] | None = None,
        temperature: float = 1.0,
        neighbors_k: int = 3,
    ) -> None:
        self.weights_path = weights_path
        self.training_dir = training_dir
        self.temperature = max(1e-6, float(temperature))
        self.neighbors_k = max(1, int(neighbors_k))
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.transform = v2.Compose(
            [
                v2.Resize((224, 224)),
                v2.ToImage(),
                v2.ToDtype(torch.float32, scale=True),
                v2.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
            ]
        )

        self._model = self._load_model(weights_path)
        self.class_names = class_names or self._infer_class_names(training_dir)

        self._index_lock = Lock()
        self._index_ready = False
        self._train_embs: torch.Tensor | None = None
        self._train_labels: torch.Tensor | None = None
        self._train_paths: list[str] = []

    def _infer_class_names(self, training_dir: Path | None) -> list[str]:
        if training_dir and training_dir.exists():
            ds = datasets.ImageFolder(root=str(training_dir))
            return ds.classes
        raw = os.getenv("CLASS_NAMES", "glioma,meningioma,notumor,pituitary")
        return [x.strip() for x in raw.split(",") if x.strip()]

    def _load_model(self, weights_path: Path) -> nn.Module:
        class_count = len([x.strip() for x in os.getenv("CLASS_NAMES", "").split(",") if x.strip()])
        model = resnet50(weights=None)

        if not weights_path.exists():
            raise FileNotFoundError(f"Weights not found: {weights_path}")

        state = torch.load(weights_path, map_location=self.device)
        if class_count == 0:
            fc_w = state.get("fc.weight")
            class_count = int(fc_w.shape[0]) if isinstance(fc_w, torch.Tensor) else 4
        model.fc = nn.Linear(model.fc.in_features, class_count)
        model.load_state_dict(state)
        model = model.to(self.device)
        model.eval()
        return model

    def _ensure_index(self) -> None:
        if self._index_ready:
            return
        if not self.training_dir or not self.training_dir.exists():
            self._index_ready = True
            return

        with self._index_lock:
            if self._index_ready:
                return

            ds = datasets.ImageFolder(root=str(self.training_dir), transform=self.transform)
            loader = DataLoader(ds, batch_size=32, shuffle=False)

            embs: list[torch.Tensor] = []
            labels: list[torch.Tensor] = []
            with torch.no_grad():
                for x, y in loader:
                    x = x.to(self.device)
                    z = self._extract_resnet_embedding(x)
                    z = F.normalize(z, p=2, dim=1)
                    embs.append(z.cpu())
                    labels.append(y)

            if embs:
                self._train_embs = torch.cat(embs, dim=0)
                self._train_labels = torch.cat(labels, dim=0)
                self._train_paths = [s[0] for s in ds.samples]
                self.class_names = ds.classes

            self._index_ready = True

    def _extract_resnet_embedding(self, x: torch.Tensor) -> torch.Tensor:
        m = self._model
        x = m.conv1(x)
        x = m.bn1(x)
        x = m.relu(x)
        x = m.maxpool(x)
        x = m.layer1(x)
        x = m.layer2(x)
        x = m.layer3(x)
        x = m.layer4(x)
        x = m.avgpool(x)
        x = torch.flatten(x, 1)
        return x

    def _image_to_data_url(self, image: Image.Image, fmt: str = "PNG") -> str:
        buf = io.BytesIO()
        image.save(buf, format=fmt)
        data = base64.b64encode(buf.getvalue()).decode("ascii")
        mime = "image/png" if fmt.upper() == "PNG" else "image/jpeg"
        return f"data:{mime};base64,{data}"

    def _denormalize(self, t: torch.Tensor) -> torch.Tensor:
        mean = torch.tensor(IMAGENET_MEAN, device=t.device).view(1, 3, 1, 1)
        std = torch.tensor(IMAGENET_STD, device=t.device).view(1, 3, 1, 1)
        return t * std + mean

    def _compute_gradcam(self, x: torch.Tensor, class_idx: int) -> torch.Tensor:
        activations: list[torch.Tensor] = []
        gradients: list[torch.Tensor] = []

        def forward_hook(_: nn.Module, __: Any, output: torch.Tensor) -> None:
            activations.append(output.detach())

        def backward_hook(_: nn.Module, __: Any, grad_output: Any) -> None:
            gradients.append(grad_output[0].detach())

        layer = self._model.layer4[-1]
        fh = layer.register_forward_hook(forward_hook)
        bh = layer.register_full_backward_hook(backward_hook)
        try:
            out = self._model(x)
            self._model.zero_grad()
            out[0, class_idx].backward(retain_graph=True)

            acts = activations[0]
            grads = gradients[0]
            weights = grads.mean(dim=(2, 3), keepdim=True)
            cam = (weights * acts).sum(dim=1, keepdim=True)
            cam = F.relu(cam)
            cam = F.interpolate(cam, size=x.shape[-2:], mode="bilinear", align_corners=False)
            cam = cam[0, 0]
            cam = cam - cam.min()
            cam = cam / (cam.max() + 1e-8)
            return cam.detach().cpu()
        finally:
            fh.remove()
            bh.remove()

    def _overlay_gradcam(self, x: torch.Tensor, cam_t: torch.Tensor) -> Image.Image:
        img_np = self._denormalize(x).detach().cpu()[0].permute(1, 2, 0).numpy()
        img_np = np.clip(img_np, 0.0, 1.0)
        cam_np = cam_t.numpy()
        heat = cm.get_cmap("jet")(cam_np)[..., :3]
        overlay = np.clip(0.55 * img_np + 0.45 * heat, 0.0, 1.0)
        arr = (overlay * 255).astype(np.uint8)
        return Image.fromarray(arr)

    def _retrieve_neighbors(self, x: torch.Tensor) -> list[NeighborResult]:
        self._ensure_index()
        if self._train_embs is None or self._train_labels is None or not self._train_paths:
            return []

        with torch.no_grad():
            q = self._extract_resnet_embedding(x.to(self.device))
            q = F.normalize(q, p=2, dim=1).cpu()
            sims = torch.mm(q, self._train_embs.t()).squeeze(0)
            vals, idxs = torch.topk(sims, k=min(self.neighbors_k, len(self._train_paths)))

        out: list[NeighborResult] = []
        for score, idx in zip(vals.tolist(), idxs.tolist()):
            p = self._train_paths[int(idx)]
            label_idx = int(self._train_labels[int(idx)].item())
            label = self.class_names[label_idx] if label_idx < len(self.class_names) else str(label_idx)
            with Image.open(p) as im:
                vis = im.convert("RGB").resize((224, 224))
            out.append(
                NeighborResult(
                    label=label,
                    similarity=float(score),
                    image_data_url=self._image_to_data_url(vis, fmt="JPEG"),
                    path=Path(p).name,
                )
            )
        return out

    def predict(self, image: Image.Image) -> dict[str, Any]:
        rgb = image.convert("RGB")
        x = self.transform(rgb).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self._model(x).detach().cpu()
            probs = F.softmax(logits / self.temperature, dim=1)[0]
            conf, pred_idx_t = torch.max(probs, dim=0)
        pred_idx = int(pred_idx_t.item())

        cam = self._compute_gradcam(x, pred_idx)
        overlay = self._overlay_gradcam(x, cam)
        neighbors = self._retrieve_neighbors(x)

        labels = self.class_names
        probabilities = []
        for i in range(min(len(labels), probs.shape[0])):
            probabilities.append({"label": labels[i], "probability": float(probs[i].item())})

        pred_label = labels[pred_idx] if pred_idx < len(labels) else str(pred_idx)

        return {
            "pred_label": pred_label,
            "confidence": float(conf.item()),
            "temperature": float(self.temperature),
            "probabilities": probabilities,
            "gradcam_overlay": self._image_to_data_url(overlay, fmt="PNG"),
            "neighbors": [
                {
                    "label": n.label,
                    "similarity": n.similarity,
                    "image": n.image_data_url,
                    "path": n.path,
                }
                for n in neighbors
            ],
        }
