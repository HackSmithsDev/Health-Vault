import os
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image

from flask import current_app
from app.models.clinicals_models import DiagnosticUnit, Subject, Chapter

class ImageRouter:
    def __init__(self):
        self.device = torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")
        self.weights_base = current_app.config.get("AI_WEIGHTS_DIR")
        
        # --- TIER 1: GLOBAL UNIT ROUTER (4 Units) ---
        self.global_router = models.resnet18()
        self.global_router.fc = nn.Linear(self.global_router.fc.in_features, 4)
        self._load_weights(self.global_router, "router_global.pth")
        self.global_router.to(self.device).eval()

        # --- TIER 2: SUBJECT SELECTOR (7 Subjects) ---
        self.subject_selector = models.resnet18()
        self.subject_selector.fc = nn.Linear(self.subject_selector.fc.in_features, 7)
        self._load_weights(self.subject_selector, "subject_selector.pth")
        self.subject_selector.to(self.device).eval()

        # Optional binary gate trained with medical and non-medical examples.
        self.medical_gate = models.resnet18()
        self.medical_gate.fc = nn.Linear(self.medical_gate.fc.in_features, 2)
        self.medical_gate_ready = self._load_weights(self.medical_gate, "medical_gate.pth")
        self.medical_gate.to(self.device).eval()

        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

    def _load_weights(self, model, filename):
        path = os.path.join(self.weights_base, filename)
        if os.path.exists(path):
            model.load_state_dict(torch.load(path, map_location=self.device, weights_only=True))
            return True
        return False

    def validate_medical_image(self, image_path, threshold=0.75):
        """Return a gate decision when the dedicated binary model is trained."""
        if not self.medical_gate_ready:
            return {"ready": False, "is_medical": True, "confidence": None}

        image = Image.open(image_path).convert('RGB')
        image_tensor = self.transform(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            probabilities = torch.softmax(self.medical_gate(image_tensor), dim=1)[0]

        # ImageFolder sorts `medical` before `non_medical`, so class 0 is medical.
        medical_confidence = float(probabilities[0].item())
        return {
            "ready": True,
            "is_medical": medical_confidence >= threshold,
            "confidence": round(medical_confidence * 100, 2)
        }

    def _get_vision_expert(self, subject_id):
        """Loads the Tier 3 especialista weights."""
        expert_weight_map = {
            "pneumonia_triage": "specialist_pneumonia.pth",
            "tuberculosis": "specialist_tb.pth",
            "brain_tumors": "specialist_brain.pth",
            "malaria_detection": "specialist_malaria.pth",
            "leukemia_screening": "specialist_leukemia.pth",
            "stroke_protocol": "specialist_stroke.pth",
            "mri_segmentation": "specialist_mri.pth"
        }
        weight_file = expert_weight_map.get(subject_id)
        if not weight_file: return None

        expert_model = models.resnet18()
        expert_model.fc = nn.Linear(expert_model.fc.in_features, 3) # 3 Chapters per subject
        self._load_weights(expert_model, weight_file)
        return expert_model.to(self.device).eval()

    def route_and_diagnose(self, image_path):
        img_pil = Image.open(image_path).convert('RGB')
        img_t = self.transform(img_pil).unsqueeze(0).to(self.device)

        with torch.no_grad():
            # TIER 1: UNIT (Pulm, Rad, Hem, Neuro)
            unit_logits = self.global_router(img_t)
            unit_idx = torch.max(unit_logits, 1)[1].item()
            unit_confidence = torch.nn.functional.softmax(unit_logits, dim=1).max().item()
            
            # Fetch Unit IDs from DB ordered by creation/ID to match weights
            units = DiagnosticUnit.query.order_by(DiagnosticUnit.id).all()
            selected_unit_id = units[unit_idx].id if unit_idx < len(units) else "unknown"

            # TIER 2: SUBJECT (Pneumonia, Malaria, etc.)
            subject_logits = self.subject_selector(img_t)
            sub_idx = torch.max(subject_logits, 1)[1].item()
            subject_confidence = torch.nn.functional.softmax(subject_logits, dim=1).max().item()
            
            # Fetch only subjects belonging to that Unit
            subjects = Subject.query.order_by(Subject.id).all()
            selected_subject_id = subjects[sub_idx].id if sub_idx < len(subjects) else "unknown"

            # TIER 3: CHAPTER (Pathophysiology, etc.)
            expert = self._get_vision_expert(selected_subject_id)
            chapter_idx = 0
            final_conf = subject_confidence

            if expert:
                diag_logits = expert(img_t)
                chapter_idx = torch.max(diag_logits, 1)[1].item()
                final_conf = torch.nn.functional.softmax(diag_logits, dim=1).max().item()

            # Dynamic Chapter Lookup
            db_chapters = Chapter.query.filter_by(subject_id=selected_subject_id).order_by(Chapter.id).all()
            selected_chapter_id = db_chapters[chapter_idx].id if chapter_idx < len(db_chapters) else "intake"

        return {
            "unit_id": selected_unit_id,
            "subject_id": selected_subject_id,
            "chapter_id": selected_chapter_id, 
            "confidence": round(float(final_conf) * 100, 2),
            # A valid medical image must be plausible at every routing tier.
            "medical_confidence": round(
                min(unit_confidence, subject_confidence, final_conf) * 100, 2
            )
        }
