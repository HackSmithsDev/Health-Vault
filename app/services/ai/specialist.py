import os
from groq import Groq
from flask import current_app

class GroqSpecialist:
    def __init__(self):
        self._client = None
        self.model = "llama-3.3-70b-versatile"
        
        self.active_units = {
            "PULMONOLOGY": {"focus": "Respiratory Systems & Thoracic Imaging", "term": "Lung Health"},
            "RADIOLOGY": {"focus": "Diagnostic Imaging & Clinical Radiology", "term": "Imaging Services"},
            "HEMATOLOGY": {"focus": "Blood Disorders & Cytomorphology", "term": "Blood Health"},
            "NEUROLOGY": {"focus": "Central Nervous System & Neuro-Imaging", "term": "Brain & Nerves"}
        }

    @property
    def client(self):
        if self._client is None:
            api_key = current_app.config.get("GROQ_API_KEY")
            if not api_key:
                api_key = os.getenv("GROQ_API_KEY")
                if not api_key:
                    raise ValueError("GROQ_API_KEY is not set.")
            self._client = Groq(api_key=api_key)
        return self._client

    def generate_clinical_insight(self, unit_id, subject_name, chapter_name, vision_data, query=None, history=None):
        """
        TIER 3 ANCHORED: Peer-to-peer analysis. 
        Now supports an optional user 'query' while maintaining clinical grounding.
        """
        unit_info = self.active_units.get(unit_id.upper(), {"focus": "General Clinical Medicine"})
        confidence = vision_data.get('confidence', 0) if vision_data else 0
        
        system_prompt = f"""
        ROLE: Senior Clinical Consultant ({unit_id.upper()}).
        FOCUS: {unit_info['focus']}.
        CASE TRUTH: Scan matches {subject_name} ({chapter_name}).
        
        STRICT CLINICAL PROTOCOL:
        1. Context: Focus exclusively on '{chapter_name}' within '{subject_name}'.
        2. Evidence: Treat the vision confidence of {confidence}% as ground truth.
        3. Tone: Professional, peer-to-peer, Markdown-heavy.
        4. Constraint: Do not suggest specific medications.
        5. Requirement: ALWAYS end with '**Clinical Correlation Required.**'
        """

        messages = [{"role": "system", "content": system_prompt}]

        if history:
            for msg in history:
                role = "assistant" if msg.sender == "ai" else "user"
                messages.append({"role": role, "content": msg.content})

        # Logic: If user provided a specific question, ask that. Otherwise, ask for a briefing.
        user_content = query if query else f"Provide a clinical briefing for {subject_name}, focusing on {chapter_name} parameters."
        
        messages.append({"role": "user", "content": user_content})

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,
                max_tokens=800
            )
            return completion.choices[0].message.content
        except Exception as e:
            current_app.logger.error(f"Groq Clinical Insight Error: {str(e)}")
            return "⚠️ **Clinical Reasoning Engine Offline.**"

    def generate_patient_friendly_explanation(self, unit_id, subject_name, chapter_name, query=None, history=None):
        """
        8th-Grade Liaison: Empathetic explanation for the patient.
        Now supports an optional user 'query' for specific patient concerns.
        """
        unit_info = self.active_units.get(unit_id.upper(), {"term": "Specialist Care"})
        
        system_prompt = f"""
        ROLE: Patient Liaison for {unit_info['term']}.
        OFFICIAL FINDING: {subject_name} ({chapter_name}).

        ETHICAL PROTOCOL:
        1. Explain finding '{chapter_name}' in simple terms (8th-grade level).
        2. NO NEW DIAGNOSES. Only explain the findings provided by the doctor.
        3. STRICTLY avoid: mortality, life expectancy, or specific drug names.
        4. Tone: Empathetic, calm, and professional.
        5. Requirement: Always suggest following up with the {unit_info['term']} team.
        """

        messages = [{"role": "system", "content": system_prompt}]

        if history:
            for msg in history:
                role = "assistant" if msg.sender == "ai" else "user"
                messages.append({"role": role, "content": msg.content})

        # Logic: Use the patient's specific question if it exists, otherwise provide a general summary.
        user_content = query if query else f"I just got my results for {subject_name} ({chapter_name}). Can you explain what this means in simple terms?"
        
        messages.append({"role": "user", "content": user_content})

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.4, # Higher temperature for a more "human" and comforting tone
                max_tokens=500
            )
            return completion.choices[0].message.content
        except Exception as e:
            current_app.logger.error(f"Groq Patient Liaison Error: {str(e)}")
            return "I am currently unable to simplify your results. Please discuss these findings with your doctor for a clear explanation."