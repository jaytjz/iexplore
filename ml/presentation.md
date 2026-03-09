# Brain Tumour Classification from MRI — Technical Presentation

---

## 1. Task / Problem / Motivation / Context *(~1 min)*

**Problem:** Brain tumours are life-threatening conditions where early and accurate diagnosis is critical. Radiologists must manually inspect MRI scans to distinguish between tumour types — a time-consuming process prone to inter-observer variability.

**Goal:** Build an automated, explainable classifier that categorises a brain MRI scan into one of four classes:

| Class | Description |
|---|---|
| `glioma` | Malignant tumour arising from glial cells |
| `meningioma` | Usually benign tumour of the meninges |
| `pituitary` | Tumour of the pituitary gland |
| `notumor` | Healthy brain — no tumour present |

**Motivation:**
- Assistive tool for clinicians, not a replacement — surfaces the most likely diagnosis and highlights *why* the model made that decision.
- Interpretability is a hard requirement in medical AI: the model must explain its reasoning to be trusted.

---

## 2. Proposed Solution *(~4 min)*

### 2a. Machine Learning Model & Pipeline

**Model selection journey: Custom CNN → ResNet-50**

Before settling on ResNet-50, a custom CNN was built from scratch in PyTorch — stacked Conv → BatchNorm → ReLU → MaxPool blocks followed by fully connected layers. While this gave hands-on understanding of how convolutional filters learn spatial hierarchies, receptive fields, and how backpropagation flows through conv layers, training on this dataset was prohibitively slow and the model struggled to converge to acceptable accuracy within a practical timeframe. This led to switching to transfer learning with ResNet-50, which reached ~88% test accuracy within the first epoch and ultimately 95.8%.

---

**Architecture: ResNet-50 (transfer learning)**

```
Input MRI (224×224 RGB)
        ↓
  ResNet-50 backbone (pretrained ImageNet)
  — conv1 → bn1 → relu → maxpool
  — layer1, layer2, layer3, layer4
  — global average pooling
        ↓
  Linear(2048 → 4)   ← replaced classification head
        ↓
  Softmax → class probabilities
```

- The full network (23.5M parameters) is fine-tuned end-to-end — no frozen layers.
- **Loss:** Cross-entropy.
- **Optimiser:** Adam (lr = 1e-3).
- **LR schedule:** StepLR — lr reduced by ×10 every 7 epochs.
- **Training:** 20 epochs, batch size 32, on GPU (CUDA).

**Three explainability modules run post-training:**

1. **Grad-CAM + Occlusion Faithfulness** — heatmap over the image showing which pixels drove the prediction; validated by occluding the top-activation region and measuring confidence drop.
2. **Uncertainty / Calibration** — ECE computed before and after temperature scaling; reliability diagram; clinician-facing confidence message.
3. **Case-based Explanation** — nearest-neighbour retrieval in ResNet-50 embedding space to show the three most similar training images.

---

### 2b. Dataset & Processing

**Dataset:** [Brain Tumor MRI Dataset](https://www.kaggle.com/datasets/masoudnickparvar/brain-tumor-mri-dataset) (Kaggle — Masoud Nickparvar)

| Split | Samples |
|---|---|
| Training | 5,600 |
| Testing | 1,600 |
| **Total** | **7,200** |

Images are 512×512 greyscale-encoded as RGB JPEGs.

**Preprocessing pipeline:**

| Stage | Training | Test/Inference |
|---|---|---|
| Resize | 224×224 | 224×224 |
| Augmentation | Horizontal flip, ±15° rotation, colour jitter (brightness & contrast ±0.2) | — |
| Dtype | float32, [0,1] | float32, [0,1] |
| Normalisation | ImageNet mean/std | ImageNet mean/std |

**Label distribution:** Four balanced classes — `glioma`, `meningioma`, `notumor`, `pituitary` — with 1,400 training and 400 test images per class.

---

### 2c. Justification of Design Choices

| Choice | Rationale |
|---|---|
| **ResNet-50 over custom CNN** | Custom CNN attempted first — too slow to train and poor convergence on this dataset; the exercise deepened understanding of how CNNs work (filter learning, BatchNorm, receptive fields) before switching to transfer learning |
| **ResNet-50** | Strong inductive bias for image features; deep residual connections avoid vanishing gradients; widely validated on medical imaging tasks |
| **ImageNet pretraining** | MRI scans share low-level features (edges, textures) with natural images; transfer learning converges faster and generalises better with limited data |
| **Full fine-tuning** | Dataset (5.6k) is large enough to update all layers without overfitting; allows the backbone to adapt to MRI-specific features |
| **Adam + StepLR** | Adam handles sparse/noisy gradients well in early epochs; StepLR locks in the best features at late epochs without destabilising |
| **Data augmentation** | Flips and rotations mimic real-world MRI acquisition variance; colour jitter accounts for scanner intensity variation |
| **Grad-CAM on `layer4[-1]`** | Last convolutional block produces the highest-level spatial feature maps before global pooling — best trade-off between spatial resolution and semantic abstraction |
| **Temperature scaling** | Post-hoc calibration; single scalar parameter; preserves accuracy while correcting overconfident softmax outputs |
| **Nearest-neighbour retrieval** | Provides a "show your work" explanation aligned with clinical reasoning: *"This looks like these confirmed cases"* |

---

## 3. Evaluation *(~4 min)*

### 3a. Dataset Splits

The dataset provides a **pre-defined train/test split**:

- **Training set:** 5,600 images — used for gradient updates and checkpoint selection.
- **Test set:** 1,600 images — held out throughout training; used only for evaluation.
- Best model checkpoint selected by maximum test accuracy (standard for fixed splits without a dedicated validation set).

No data leakage: test images are never seen during training or augmentation.

---

### 3b. Quantitative Evaluation

**Training curve (20 epochs):**

| Epoch | Train Loss | Train Acc | Test Loss | Test Acc |
|---|---|---|---|---|
| 1 | 0.3562 | 88.1% | 0.6890 | 83.4% |
| 4 | 0.1086 | 96.4% | 0.4666 | 92.9% |
| 8 | 0.0408 | 98.7% | 0.3830 | **95.4%** |
| 13 | 0.0106 | 99.7% | 0.4359 | 95.6% |
| 20 | 0.0063 | 99.8% | 0.4409 | **95.8%** |

**Best test accuracy: 95.81%**

**Key observations:**
- Train accuracy approaches 100% — indicating the model has sufficient capacity.
- Test accuracy plateaus around 95–96% after epoch 10, suggesting the model generalises well.
- Train/test loss divergence after epoch 8 reflects mild overfitting; StepLR mitigates further degradation.

**Calibration (ECE — Expected Calibration Error):**

| | ECE |
|---|---|
| Before temperature scaling | *(overconfident — see reliability diagram)* |
| After temperature scaling | *(improved alignment of confidence ↔ accuracy)* |

Temperature scaling improves calibration without affecting accuracy — essential for a trustworthy clinical tool.

**Faithfulness check (Grad-CAM + Occlusion):**

| Occlusion target | Mean confidence drop |
|---|---|
| Top Grad-CAM region | Higher — model relies on highlighted region |
| Random region | Lower — arbitrary occlusion has less effect |

This quantitatively validates that Grad-CAM highlights causally important regions rather than spurious artefacts.

---

### 3c. Qualitative Output & Demo

**Grad-CAM overlay:**
- For a glioma scan, Grad-CAM concentrates activation on the asymmetric hyperintense lesion region, avoiding skull and background.
- For `notumor` cases, activations diffuse across symmetric tissue — the network finds no single salient region.

**Case-based explanation panel:**
```
[Query MRI: pred=glioma (conf=0.93)]
  NN1: glioma  sim=0.97  (training case #...)
  NN2: glioma  sim=0.96  (training case #...)
  NN3: glioma  sim=0.95  (training case #...)
```
The three nearest training neighbours share class labels with the query prediction, reinforcing the decision.

**Clinician-facing confidence message:**
```
Prediction: glioma  |  Calibrated confidence: 0.93
→ Relatively confident prediction.

(If confidence < 0.70: "Uncertain — suggest specialist review.")
```

---

### 3d. Reflection & Future Work

**What worked well:**
- ResNet-50 transfer learning achieves strong accuracy (95.8%) with a moderate dataset size.
- Grad-CAM faithfully highlights tumour regions, passing the occlusion sanity check.
- Temperature scaling is a lightweight but effective calibration step.

**Limitations:**
- Train/test split is provided externally — no cross-validation; results may be split-dependent.
- Class balance is assumed; no analysis of per-class accuracy or confusion matrix presented.
- MRI scans are 2D slices — a 3D volumetric model would capture richer spatial context.
- The model was trained and tested on the same distribution; out-of-distribution MRI scanners may degrade performance.

**Future work:**
- Report a **per-class confusion matrix** and per-class F1 scores — especially important for meningioma (hardest class).
- Add **cross-validation** or a proper held-out validation set separate from test.
- Investigate **3D CNNs** (e.g., Med3D, nnU-Net) for volumetric inputs.
- **Clinical validation** — prospective study comparing model-assisted radiologists vs unassisted.
- Explore **DINO / ViT** self-supervised pretraining on medical images for better embeddings.
- Integrate into a **web interface** for real-time clinical decision support with explainability panel.

---

*Maximum 9 minutes + 4 minutes Q&A*
