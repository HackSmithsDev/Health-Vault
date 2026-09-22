import sys
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, models, transforms
from torch.utils.data import DataLoader
import time
import os

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python train_specialist.py <path_to_train_folder> <output_model_name.pth>")
        sys.exit(1)

    train_dir, save_path = sys.argv[1], sys.argv[2]

    # M2 ACCELERATION: Metal Performance Shaders
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"--- 🚀 Training on: {device} | Subject: {os.path.basename(train_dir)} ---")

    # ENHANCED DATA AUGMENTATION: Essential for 1GB+ datasets to prevent overfitting
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=0.4),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.1, contrast=0.1),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    try:
        train_dataset = datasets.ImageFolder(train_dir, transform=transform)
    except Exception as e:
        print(f"❌ Error: {e}"); sys.exit(1)

    num_classes = len(train_dataset.classes)
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, num_workers=4, pin_memory=False)

    # ACCURACY OPTIMIZATION: Fine-Tuning ResNet18
    model = models.resnet18(weights='DEFAULT')

    # Freeze early layers, but unfreeze 'layer4' for clinical feature adaptation
    for name, param in model.named_parameters():
        if "layer4" in name:
            param.requires_grad = True
        else:
            param.requires_grad = False

    # Replace head for your specific Subject's Chapters
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    model = model.to(device)

    # Differential Learning Rates: Low for backbone, standard for head
    optimizer = optim.Adam([
        {'params': model.layer4.parameters(), 'lr': 1e-4}, 
        {'params': model.fc.parameters(), 'lr': 1e-3}
    ])

    criterion = nn.CrossEntropyLoss()

    # Early Stopping Config
    epochs, patience = 10, 3
    best_loss, epochs_no_improve = float('inf'), 0
    best_acc = 0.0

    print(f"🩺 Fine-tuning Specialist ({num_classes} Chapters)...")

    for epoch in range(epochs):
        model.train()
        running_loss, correct, total = 0.0, 0, 0
        start_time = time.time()
        
        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
        avg_loss = running_loss / len(train_loader)
        epoch_acc = 100 * correct / total
        
        print(f"Epoch {epoch+1}/{epochs} | Loss: {avg_loss:.4f} | Acc: {epoch_acc:.2f}% | Time: {time.time() - start_time:.1f}s")

        # Save Best Weights
        if avg_loss < best_loss:
            best_loss, best_acc = avg_loss, epoch_acc
            epochs_no_improve = 0
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            torch.save(model.state_dict(), save_path)
            print(f"✨ Improvement Found. Weights Updated.")
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                print("🛑 Early stopping triggered.")
                break

    print(f"\n🏆 Final Accuracy for {os.path.basename(train_dir)}: {best_acc:.2f}%")