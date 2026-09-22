import os

from PIL import Image
from torchvision.datasets import CIFAR10


BASE_DIR = os.path.dirname(os.path.realpath(__file__))
CLINICAL_DIR = os.path.join(BASE_DIR, "ai_models")
GATE_DIR = os.path.join(CLINICAL_DIR, "medical_gate")
TRAINING_DIR = os.path.join(GATE_DIR, "training")
MEDICAL_DIR = os.path.join(TRAINING_DIR, "medical")
NON_MEDICAL_DIR = os.path.join(TRAINING_DIR, "non_medical")
CIFAR_DIR = os.path.join(GATE_DIR, "datasets")
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
MAX_MEDICAL_IMAGES = 10000


def copy_clinical_images():
    os.makedirs(MEDICAL_DIR, exist_ok=True)
    count = 0
    for root, _, files in os.walk(CLINICAL_DIR, followlinks=True):
        if os.path.abspath(root).startswith(os.path.abspath(GATE_DIR)):
            continue
        for filename in files:
            if count >= MAX_MEDICAL_IMAGES:
                return count
            source = os.path.join(root, filename)
            if os.path.splitext(filename)[1].lower() not in SUPPORTED_EXTENSIONS:
                continue
            try:
                with Image.open(source) as image:
                    image.verify()
            except (OSError, ValueError):
                continue
            destination = os.path.join(MEDICAL_DIR, f"clinical_{count:07d}{os.path.splitext(filename)[1].lower()}")
            if not os.path.exists(destination):
                os.symlink(os.path.abspath(source), destination)
            count += 1
    return count


def download_non_medical_images(limit=10000):
    os.makedirs(NON_MEDICAL_DIR, exist_ok=True)
    dataset = CIFAR10(root=CIFAR_DIR, train=True, download=True)
    count = 0
    for index, (image, _) in enumerate(dataset):
        if index >= limit:
            break
        destination = os.path.join(NON_MEDICAL_DIR, f"cifar10_{index:07d}.png")
        if not os.path.exists(destination):
            image.save(destination)
        count += 1
    return count


def main():
    medical_count = copy_clinical_images()
    if medical_count == 0:
        raise SystemExit(
            "No clinical images found. Run `python3 ai/setup_clinical_data.py` first, "
            "then run this preparation command again."
        )

    non_medical_count = download_non_medical_images()
    if non_medical_count == 0:
        raise SystemExit("No non-clinical images were downloaded.")

    print(f"Prepared medical gate data: {medical_count} medical, {non_medical_count} non-medical images")
    print(f"Dataset directory: {GATE_DIR}")


if __name__ == "__main__":
    main()
