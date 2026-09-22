import os
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, models, transforms
from torch.utils.data import DataLoader
from PIL import Image

# ==========================================
# CONFIGURATION
# ==========================================
MODE = "global"  # "global" for Unit Router, "subject" for Subject Selector
DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
current_dir = os.path.dirname(os.path.realpath(__file__))
BASE_DATA_DIR = os.path.join(current_dir, "ai_models")

# Updated counts: 4 Units, 7 Subjects (Bone Fractures Removed)
NUM_CLASSES = 4 if MODE == "global" else 7 
SAVE_PATH = os.path.join(current_dir, "weights", f"router_{MODE}.pth" if MODE == "global" else "subject_selector.pth")

# ==========================================
# DATASET LOGIC
# ==========================================
class HierarchicalRouterDataset(datasets.ImageFolder):
    def __init__(self, root, transform=None, mode="global"):
        super().__init__(root, transform=transform, is_valid_file=self.is_valid_image)
        self.mode = mode
        self.unit_map = {"pulmonology": 0, "radiology": 1, "hematology": 2, "neurology": 3}
        self.subject_map = {
            "pneumonia_triage": 0, "tuberculosis": 1,
            "brain_tumors": 2, # Bone Fractures Removed
            "malaria_detection": 3, "leukemia_screening": 4,
            "stroke_protocol": 5, "mri_segmentation": 6
        }

    @staticmethod
    def is_valid_image(path):
        """Strict 'Photo-Only' Logic: No metadata, no hidden files."""
        filename = os.path.basename(path)
        return not (filename.startswith('.') or '__MACOSX' in path) and \
               path.lower().endswith(('.png', '.jpg', '.jpeg'))

    def __getitem__(self, index):
        path, _ = self.samples[index]
        
        # Robust loader to handle any lingering bad files
        try:
            sample = self.loader(path)
        except Exception as e:
            print(f"Skipping corrupted image: {path}")
            return self.__getitem__((index + 1) % len(self.samples))
            
        if self.transform is not None:
            sample = self.transform(sample)

        parts = path.split(os.sep)
        try:
            # Locate the unit and subject in the path relative to ai_models
            base_idx = parts.index("ai_models")
            unit_name = parts[base_idx + 1]    
            subject_name = parts[base_idx + 2] 
            
            if self.mode == "global":
                target_label = self.unit_map[unit_name]
            else:
                target_label = self.subject_map[subject_name]
        except (ValueError, KeyError, IndexError):
            target_label = 0 

        return sample, target_label

# ==========================================
# TRAINING FUNCTION
# ==========================================
def train_router():
    print(f"--- 🚀 Initializing {MODE.upper()} Router Training ---")
    print(f"📍 Target: {NUM_CLASSES} Classes | Device: {DEVICE}")
    
    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    dataset = HierarchicalRouterDataset(BASE_DATA_DIR, transform=transform, mode=MODE)
    if len(dataset) == 0:
        print("❌ Error: No images found. Check your symlinks in ai_models.")
        return
        
    print(f"📊 Dataset Size: {len(dataset)} images verified.")

    loader = DataLoader(dataset, batch_size=16, shuffle=True, num_workers=0)

    # ResNet18 is ideal for rapid classification tasks on M2
    model = models.resnet18(weights='DEFAULT')
    model.fc = nn.Linear(model.fc.in_features, NUM_CLASSES)
    model = model.to(DEVICE)

    optimizer = optim.Adam(model.parameters(), lr=0.0001)
    criterion = nn.CrossEntropyLoss()

    epochs = 5 
    for epoch in range(epochs):
        model.train()
        running_loss, correct, total = 0.0, 0, 0
        
        for images, labels in loader:
            images, labels = images.to(DEVICE), labels.to(DEVICE)
            
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

        acc = 100 * correct / total
        print(f"Epoch {epoch+1}/{epochs} | Loss: {running_loss/len(loader):.4f} | Acc: {acc:.2f}%")

    torch.save(model.state_dict(), SAVE_PATH)
    print(f"✅ SUCCESS: {MODE.upper()} router saved to {SAVE_PATH}")

if __name__ == "__main__":
    train_router()