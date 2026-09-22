from app import create_app, db
from app.models.clinicals_models import DiagnosticUnit, Subject, Chapter

# Optimized Curriculum: 4 Units | 7 Subjects | 3 Chapters each
# Matches the 'router_subject' and 'specialist' registry exactly
CLINICAL_CURRICULUM = {
    'Pulmonology': {
        'Pneumonia Triage': ['Pathophysiology', 'Radiographic Signs', 'Antibiotics'],
        'Tuberculosis': ['Screening', 'Cavitation', 'Treatment Response']
    },
    'Radiology': {
        'Brain Tumors': ['Grading', 'Edema', 'Surgical Planning']
    },
    'Hematology': {
        'Malaria Detection': ['Morphology', 'Parasitemia', 'Treatment'],
        'Leukemia Screening': ['RBC Uniformity', 'Platelet Count', 'Clarity']
    },
    'Neurology': {
        'Stroke Protocol': ['NIHSS Scoring', 'TPA Window', 'Penumbra'],
        'MRI Segmentation': ['Localization', 'Contrast', 'Voxel Analysis']
    }
}

def seed_db():
    app = create_app()
    with app.app_context():
        print("--- 🩺 Starting Clinical Database Seeding (7-Subject Suite) ---")
        
        try:
            # Clear existing data to prevent ID conflicts
            Chapter.query.delete()
            Subject.query.delete()
            DiagnosticUnit.query.delete()
            db.session.commit()
            print("🗑️  Old curriculum cleared.")
        except Exception as e:
            db.session.rollback()
            print(f"⚠️  Cleanup warning: {e}")

        unit_count = 0
        subject_count = 0
        chapter_count = 0
        
        for unit_name, subjects in CLINICAL_CURRICULUM.items():
            # Create Unit ID (e.g., pulmonology)
            unit_id = unit_name.lower().strip()
            unit = DiagnosticUnit(
                id=unit_id, 
                name=unit_name, 
                category="Imaging Diagnostics"
            )
            db.session.add(unit)
            db.session.flush() 
            unit_count += 1
            
            for sub_name, chapters in subjects.items():
                # Create Subject ID (e.g., pneumonia_triage)
                # This MUST match the 'subject_ids' list in your ImageRouter
                sub_id = sub_name.strip().replace(' ', '_').lower()
                subject = Subject(
                    id=sub_id, 
                    name=sub_name, 
                    unit_id=unit.id
                )
                db.session.add(subject)
                db.session.flush()
                subject_count += 1
                
                for chap_name in chapters:
                    # Create Chapter ID (e.g., pathophysiology)
                    # We use simple slugs to match the 'chapter_map' in the router
                    chap_id = chap_name.strip().replace(' ', '_').lower()
                    
                    chapter = Chapter(
                        id=chap_id, 
                        name=chap_name, 
                        subject_id=subject.id
                    )
                    db.session.add(chapter)
                    chapter_count += 1
        
        try:
            db.session.commit()
            print(f"✨ SUCCESS: Seeded {unit_count} Units, {subject_count} Subjects, and {chapter_count} Chapters.")
            print("🚀 The database is now perfectly synced with the AI Specialist Registry.")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error committing to database: {e}")

if __name__ == "__main__":
    seed_db()