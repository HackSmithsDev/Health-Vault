import kagglehub
import os

def setup():
    # Use realpath to ensure we are in the 'ai' directory
    base_dir = os.path.dirname(os.path.realpath(__file__))
    data_base = os.path.join(base_dir, "ai_models")
    
    # 4 Units
    units = ["pulmonology", "radiology", "hematology", "neurology"]

    # This is now a Dictionary { "Local Path": "Kaggle Slug" }
    clinical_datasets = {
        # PULMONOLOGY
        "pulmonology/pneumonia_triage": "paultimothymooney/chest-xray-pneumonia",
        "pulmonology/tuberculosis": "tawsifurrahman/tuberculosis-tb-chest-xray-dataset",
        
        # RADIOLOGY 
        "radiology/brain_tumors": "sartajbhuvaji/brain-tumor-classification-mri",
        
        # HEMATOLOGY
        "hematology/malaria_detection": "iarunava/cell-images-for-detecting-malaria",
        "hematology/leukemia_screening": "paultimothymooney/blood-cells",
        
        # NEUROLOGY
        "neurology/stroke_protocol": "ozguraslank/brain-stroke-ct-dataset",
        "neurology/mri_segmentation": "navoneel/brain-mri-images-for-brain-tumor-detection"
    }

    print(f"🚀 Initializing Clinical Registry (8 Topics, Cardiology Removed)...")
    print(f"📂 Target Directory: {data_base}")
    
    for local_path, slug in clinical_datasets.items():
        try:
            print(f"\n📥 Syncing {slug}...")
            # This downloads to ~/.cache/kagglehub
            download_path = kagglehub.dataset_download(slug)
            
            # Full path where we want the symlink to live
            target_link = os.path.join(data_base, local_path)
            
            # Ensure the parent unit folder (e.g., ai_models/pulmonology) exists
            os.makedirs(os.path.dirname(target_link), exist_ok=True)
            
            if not os.path.exists(target_link):
                # Create the symlink pointing to the Kaggle cache
                os.symlink(os.path.abspath(download_path), target_link)
                print(f"🔗 Linked: {local_path} -> {slug}")
            else:
                print(f"✅ {local_path} already exists and is verified.")
                
        except Exception as e:
            print(f"⚠️ Failed to sync {slug}: {e}")

    print("\n✨ Data environment is ready for training.")

if __name__ == "__main__":
    setup()