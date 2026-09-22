import subprocess
import os

# Updated paths to match the actual Kaggle structures linked by setup_clinical_data.py
specialists = [
    # PULMONOLOGY
    ("pulmonology/pneumonia_triage/chest_xray/train", "pulmonology/pneumonia_triage.pth"),
    ("pulmonology/tuberculosis/TB_Chest_Radiography_Database", "pulmonology/tuberculosis.pth"), # Fixed path
    
    # RADIOLOGY 
    ("radiology/brain_tumors/Training", "radiology/brain_tumors.pth"),
    
    # HEMATOLOGY
    ("hematology/malaria_detection/cell_images", "hematology/malaria_detection.pth"),
    ("hematology/leukemia_screening/dataset2-master/dataset2-master/images/TRAIN", "hematology/leukemia_screening.pth"),
    
    # NEUROLOGY
    ("neurology/stroke_protocol/Brain_Stroke_CT_Dataset", "neurology/stroke_protocol.pth"),
    ("neurology/mri_segmentation/brain_tumor_dataset", "neurology/mri_segmentation.pth") # Added missing
]

def run_batch_training():
    # Use realpath to resolve absolute paths correctly on macOS
    ai_dir = os.path.dirname(os.path.realpath(__file__))
    script_path = os.path.join(ai_dir, "train_specialist.py")
    
    if not os.path.exists(script_path):
        print(f"❌ ERROR: Could not find {script_path}")
        print("Ensure 'train_specialist.py' is in the same folder as this script.")
        return

    print("👨‍⚕️ Training Clinical Suite: 8 Imaging Specialists Initiated")
    
    for data_rel, weight_rel in specialists:
        full_data_path = os.path.join(ai_dir, "ai_models", data_rel)
        full_weight_path = os.path.join(ai_dir, "weights", weight_rel)

        # CRITICAL: Create the weight sub-directory (e.g., ai/weights/pulmonology)
        os.makedirs(os.path.dirname(full_weight_path), exist_ok=True)

        if os.path.exists(full_data_path):
            print(f"\n--- 🩺 Training Specialist: {weight_rel.split('/')[-1].upper()} ---")
            try:
                # Use absolute path for the script to avoid 'file not found' errors
                subprocess.run(["python3", script_path, full_data_path, full_weight_path], check=True)
            except Exception as e:
                print(f"❌ Error during execution: {e}")
        else:
            # Helpful debug info so you know WHY it's skipping
            print(f"⏭️ Skipping: Folder not found at {full_data_path}")

    print("\n✅ All Specialists processed.")

if __name__ == "__main__":
    run_batch_training()