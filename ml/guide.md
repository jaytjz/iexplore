# Brain Tumor MRI Classification — Guide

## Dataset
- **4 classes**: glioma, meningioma, pituitary, notumor
- **Structure**: `dataset/Training/` and `dataset/Testing/`, with subfolders per class
- **Format**: JPG images

---

## Step 1: Load the Data
Since your images are organized in folders by class name, use `torchvision.datasets.ImageFolder` — it automatically assigns labels based on subfolder names.

You'll also need to **transform** your images since MRI scans may be different sizes:
- Resize all images to a consistent size (e.g. 224x224)
- Convert to tensors
- Normalize pixel values

Use `torchvision.transforms.Compose` to chain these together.

## Step 2: Create DataLoaders
Wrap your datasets in `DataLoader` to handle batching and shuffling. Pick a batch size (e.g. 32).

## Step 3: Define Your Model
Since this is an image classification task, you want a **CNN (Convolutional Neural Network)**. Two options:

- **Build from scratch** — stack `Conv2d` -> `ReLU` -> `MaxPool2d` layers, then flatten and use `Linear` layers at the end. Good for learning.
- **Transfer learning** — e.g. `torchvision.models.resnet18(pretrained=True)` and replace the final layer to output 4 classes. Better results with less data.

## Step 4: Set Up Training
You'll need:
- A **loss function** — `nn.CrossEntropyLoss()` is the standard for multi-class classification
- An **optimizer** — `torch.optim.Adam` is a good default
- A **training loop** — iterate over epochs, and for each batch: forward pass -> compute loss -> backward pass -> optimizer step

## Step 5: Evaluate
Run your model on the test set and check accuracy. Consider also looking at a **confusion matrix** to see which tumor types it confuses.
