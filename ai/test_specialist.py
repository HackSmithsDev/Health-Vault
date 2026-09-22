import sys
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, models, transforms
from torch.utils.data import DataLoader
import time

import ssl
import os

# This bypasses the SSL check for downloading weights
ssl._create_default_https_context = ssl._create_unverified_context

def is_valid_file(path):
    return not os.path.basename(path).startswith('._') and \
           not '__MACOSX' in path

if __name__ == '__main__':
    # DEBUG: See what is being passed
    print(f"DEBUG: Received {len(sys.argv)} arguments: {sys.argv}")

    if len(sys.argv) != 3:
        print("❌ Error: Missing arguments.")
        print("Usage: python train_specialist.py <path_to_train_folder> <output_model_name.pth>")
        sys.exit(1)

    train_dir, save_path = sys.argv[1], sys.argv[2]

    # Device Setup for M2
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    
    # 1. Transform setup
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    # 2. Dataset loading
    if not os.path.exists(train_dir):
        print(f"❌ Error: Folder {train_dir} does not exist.")
        sys.exit(1)

    try:
        # Use the is_valid_file filter to ignore hidden Mac junk
        train_dataset = datasets.ImageFolder(
            train_dir, 
            transform=transform,
            is_valid_file=is_valid_file
        )
    except Exception as e:
        print(f"❌ Error: {e}"); sys.exit(1)

    num_classes = len(train_dataset.classes)
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, num_workers=2)

    # 3. Model setup (Fine-Tuning)
    model = models.resnet18(weights='DEFAULT')
    for name, param in model.named_parameters():
        if "layer4" in name:
            param.requires_grad = True
        else:
            param.requires_grad = False

    model.fc = nn.Linear(model.fc.in_features, num_classes)
    model = model.to(device)

    # 4. Optimizer and Loss
    optimizer = optim.Adam([
        {'params': model.layer4.parameters(), 'lr': 1e-4}, 
        {'params': model.fc.parameters(), 'lr': 1e-3}
    ])
    criterion = nn.CrossEntropyLoss()

    # 5. Training Loop
    print(f"🩺 Training {os.path.basename(train_dir)} on {device}...")
    
    best_loss = float('inf')
    for epoch in range(5): # Small epoch count for testing stability
        model.train()
        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
        
        print(f"Epoch {epoch+1} complete.")
        
        # Save model
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        torch.save(model.state_dict(), save_path)

    print(f"✅ Model saved to {save_path}")