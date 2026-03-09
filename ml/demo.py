import gradio as gr
import torch
import torch.nn.functional as F
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from torchvision.models import ResNet50_Weights, resnet50
from torchvision.transforms import v2
from torch import nn

# ── Config ────────────────────────────────────────────────────────────────────
CLASSES = ["glioma", "meningioma", "notumor", "pituitary"]
CHECKPOINT = "best_model.pth"
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD  = [0.229, 0.224, 0.225]

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ── Load model ────────────────────────────────────────────────────────────────
model = resnet50(weights=ResNet50_Weights.IMAGENET1K_V2)
model.fc = nn.Linear(model.fc.in_features, 4)
model.load_state_dict(torch.load(CHECKPOINT, map_location=device))
model = model.to(device)
model.eval()

# ── Transforms ────────────────────────────────────────────────────────────────
transform = v2.Compose([
    v2.Resize((224, 224)),
    v2.ToImage(),
    v2.ToDtype(torch.float32, scale=True),
    v2.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
])

def denormalize(tensor):
    mean = torch.tensor(IMAGENET_MEAN, device=tensor.device).view(3, 1, 1)
    std  = torch.tensor(IMAGENET_STD,  device=tensor.device).view(3, 1, 1)
    return (tensor * std + mean).clamp(0, 1)

# ── Grad-CAM ──────────────────────────────────────────────────────────────────
def gradcam(input_tensor, class_idx):
    activations, gradients = [], []

    fh = model.layer4[-1].register_forward_hook(
        lambda _, __, out: activations.append(out.detach()))
    bh = model.layer4[-1].register_full_backward_hook(
        lambda _, gi, go: gradients.append(go[0].detach()))

    out = model(input_tensor)
    model.zero_grad()
    out[0, class_idx].backward()

    fh.remove(); bh.remove()

    acts  = activations[0]
    grads = gradients[0]
    weights = grads.mean(dim=(2, 3), keepdim=True)
    cam = F.relu((weights * acts).sum(dim=1, keepdim=True))
    cam = F.interpolate(cam, size=(224, 224), mode="bilinear", align_corners=False)
    cam = cam[0, 0]
    cam = (cam - cam.min()) / (cam.max() + 1e-8)
    return cam.cpu().numpy()

# ── Inference function ─────────────────────────────────────────────────────────
def predict(pil_image):
    if pil_image is None:
        return None, "No image provided."

    img_rgb = pil_image.convert("RGB")
    tensor  = transform(img_rgb).unsqueeze(0).to(device)

    with torch.no_grad():
        logits = model(tensor)
    probs = F.softmax(logits, dim=1)[0].cpu()
    pred_idx = int(probs.argmax())

    # Grad-CAM needs grad so re-run with grad enabled
    tensor.requires_grad_(True)
    cam = gradcam(tensor, pred_idx)

    # ── Build figure ──
    img_np = denormalize(tensor[0].detach().cpu()).permute(1, 2, 0).numpy()

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    fig.patch.set_facecolor("#1a1a2e")
    for ax in axes:
        ax.set_facecolor("#1a1a2e")
        ax.axis("off")

    # Original
    axes[0].imshow(img_np)
    axes[0].set_title("Input MRI", color="white", fontsize=13)

    # Grad-CAM overlay
    axes[1].imshow(img_np)
    axes[1].imshow(cam, cmap="jet", alpha=0.45)
    axes[1].set_title("Grad-CAM", color="white", fontsize=13)

    # Bar chart of probabilities
    colors = ["#4cc9f0" if i == pred_idx else "#3b4a6b" for i in range(4)]
    axes[2].set_facecolor("#1a1a2e")
    bars = axes[2].barh(CLASSES, probs.numpy(), color=colors, height=0.5)
    axes[2].set_xlim(0, 1)
    axes[2].tick_params(colors="white", labelsize=11)
    for spine in axes[2].spines.values():
        spine.set_edgecolor("#3b4a6b")
    axes[2].set_title("Confidence", color="white", fontsize=13)
    for bar, p in zip(bars, probs.numpy()):
        axes[2].text(min(p + 0.02, 0.95), bar.get_y() + bar.get_height() / 2,
                     f"{p:.2f}", va="center", color="white", fontsize=10)

    plt.tight_layout(pad=1.5)

    # ── Text label ──
    conf = float(probs[pred_idx])
    if conf >= 0.70:
        flag = "Confident prediction"
    else:
        flag = "Uncertain — suggest specialist review"
    label = (
        f"Prediction:  {CLASSES[pred_idx].upper()}\n"
        f"Confidence:  {conf:.2%}\n"
        f"{flag}"
    )

    return fig, label

# ── Gradio UI ─────────────────────────────────────────────────────────────────
with gr.Blocks(title="Brain Tumour MRI Classifier") as demo:
    gr.Markdown(
        """
        # Brain Tumour MRI Classifier
        Upload an MRI scan to get a prediction, Grad-CAM heatmap, and confidence scores.
        """
    )
    with gr.Row():
        image_input = gr.Image(type="pil", label="Input MRI", height=300)
        with gr.Column():
            output_plot  = gr.Plot(label="Results")
            output_label = gr.Textbox(label="Prediction", lines=3)

    image_input.change(predict, inputs=image_input, outputs=[output_plot, output_label])

    gr.Examples(
        examples=[],
        inputs=image_input,
    )

if __name__ == "__main__":
    demo.launch(theme=gr.themes.Base())
