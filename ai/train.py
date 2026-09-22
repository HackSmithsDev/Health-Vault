"""Train and inspect all Health Vault vision models.

Examples:
    python3 ai/train.py router --mode global
    python3 ai/train.py router --mode subject
    python3 ai/train.py specialists
    python3 ai/train.py gate
    python3 ai/train.py test DATASET WEIGHTS
"""

import argparse
import os
from collections import Counter

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms


BASE_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "ai_models")
WEIGHTS_DIR = os.path.join(BASE_DIR, "weights")
DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
NORMALIZE = ([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
UNIT_MAP = {"pulmonology": 0, "radiology": 1, "hematology": 2, "neurology": 3}
SUBJECT_MAP = {
    "pneumonia_triage": 0, "tuberculosis": 1, "brain_tumors": 2,
    "malaria_detection": 3, "leukemia_screening": 4,
    "stroke_protocol": 5, "mri_segmentation": 6,
}
SPECIALISTS = [
    ("pulmonology/pneumonia_triage/chest_xray/train", "pulmonology/pneumonia_triage.pth"),
    ("pulmonology/tuberculosis/TB_Chest_Radiography_Database", "pulmonology/tuberculosis.pth"),
    ("radiology/brain_tumors/Training", "radiology/brain_tumors.pth"),
    ("hematology/malaria_detection/cell_images", "hematology/malaria_detection.pth"),
    ("hematology/leukemia_screening/dataset2-master/dataset2-master/images/TRAIN", "hematology/leukemia_screening.pth"),
    ("neurology/stroke_protocol/Brain_Stroke_CT_Dataset", "neurology/stroke_protocol.pth"),
    ("neurology/mri_segmentation/brain_tumor_dataset", "neurology/mri_segmentation.pth"),
]


def image_transform(augment=False):
    steps = [transforms.Resize((224, 224))]
    if augment:
        steps.extend([transforms.RandomHorizontalFlip(p=0.4), transforms.RandomRotation(15)])
    steps.extend([transforms.ToTensor(), transforms.Normalize(*NORMALIZE)])
    return transforms.Compose(steps)


class RouterDataset(datasets.ImageFolder):
    """Map the nested clinical directory to unit or subject labels."""

    def __init__(self, root, mode):
        super().__init__(root, transform=image_transform(), is_valid_file=self.is_valid_image)
        self.mode = mode

    @staticmethod
    def is_valid_image(path):
        return (
            "medical_gate" not in path
            and not os.path.basename(path).startswith(".")
            and path.lower().endswith((".png", ".jpg", ".jpeg"))
        )

    def __getitem__(self, index):
        image, _ = super().__getitem__(index)
        path, _ = self.samples[index]
        parts = path.split(os.sep)
        base = parts.index("ai_models")
        mapping = UNIT_MAP if self.mode == "global" else SUBJECT_MAP
        return image, mapping[parts[base + (1 if self.mode == "global" else 2)]]


def new_model(classes):
    model = models.resnet18(weights="DEFAULT")
    model.fc = nn.Linear(model.fc.in_features, classes)
    return model.to(DEVICE)


def train_model(model, loader, epochs, learning_rate=1e-4):
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    criterion = nn.CrossEntropyLoss()
    for epoch in range(epochs):
        model.train()
        correct = total = 0
        for images, labels in loader:
            optimizer.zero_grad()
            predictions = model(images.to(DEVICE))
            loss = criterion(predictions, labels.to(DEVICE))
            loss.backward()
            optimizer.step()
            correct += (predictions.argmax(1).cpu() == labels).sum().item()
            total += labels.size(0)
        print(f"Epoch {epoch + 1}/{epochs} | accuracy: {correct / total:.2%}")


def train_router(mode):
    dataset = RouterDataset(DATA_DIR, mode)
    if not dataset:
        raise SystemExit("No clinical images found. Run setup_clinical_data.py first.")
    model = new_model(4 if mode == "global" else 7)
    train_model(model, DataLoader(dataset, batch_size=16, shuffle=True, num_workers=0), 5)
    output = os.path.join(WEIGHTS_DIR, "router_global.pth" if mode == "global" else "subject_selector.pth")
    os.makedirs(WEIGHTS_DIR, exist_ok=True)
    torch.save(model.state_dict(), output)
    print(f"Saved {output}")


def train_specialist(dataset_path, output_path):
    dataset = datasets.ImageFolder(dataset_path, transform=image_transform(augment=True))
    if not dataset.classes:
        raise SystemExit("Dataset contains no labeled classes.")
    model = new_model(len(dataset.classes))
    for name, parameter in model.named_parameters():
        parameter.requires_grad = "layer4" in name or "fc" in name
    train_model(model, DataLoader(dataset, batch_size=32, shuffle=True, num_workers=0), 10, 1e-3)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    torch.save(model.state_dict(), output_path)
    print(f"Saved {output_path}")


def train_specialists():
    for data_relative, weights_relative in SPECIALISTS:
        dataset_path = os.path.join(DATA_DIR, data_relative)
        output_path = os.path.join(WEIGHTS_DIR, weights_relative)
        if os.path.exists(dataset_path):
            train_specialist(dataset_path, output_path)
        else:
            print(f"Skipping missing dataset: {dataset_path}")


def train_gate():
    gate_dir = os.path.join(DATA_DIR, "medical_gate", "training")
    dataset = datasets.ImageFolder(gate_dir, transform=image_transform(augment=True))
    if dataset.class_to_idx != {"medical": 0, "non_medical": 1}:
        raise SystemExit("Gate data must contain medical/ and non_medical/ folders.")
    counts = Counter(label for _, label in dataset.samples)
    if min(counts.get(0, 0), counts.get(1, 0)) < 100:
        raise SystemExit("Add at least 100 images to each gate class before training.")
    model = new_model(2)
    train_model(model, DataLoader(dataset, batch_size=16, shuffle=True, num_workers=0), 8)
    output = os.path.join(WEIGHTS_DIR, "medical_gate.pth")
    torch.save(model.state_dict(), output)
    print(f"Saved {output}")


def test_model(dataset_path, weights_path):
    dataset = datasets.ImageFolder(dataset_path, transform=image_transform())
    model = new_model(len(dataset.classes))
    model.load_state_dict(torch.load(weights_path, map_location=DEVICE, weights_only=True))
    model.eval()
    print(f"Loaded {weights_path}; classes: {dataset.classes}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    router = subparsers.add_parser("router")
    router.add_argument("--mode", choices=("global", "subject"), required=True)
    subparsers.add_parser("specialists")
    subparsers.add_parser("gate")
    test = subparsers.add_parser("test")
    test.add_argument("dataset")
    test.add_argument("weights")
    args = parser.parse_args()
    if args.command == "router":
        train_router(args.mode)
    elif args.command == "specialists":
        train_specialists()
    elif args.command == "gate":
        train_gate()
    else:
        test_model(args.dataset, args.weights)


if __name__ == "__main__":
    main()