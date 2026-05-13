"""Seed common medicines into the database. Run once after deployment."""

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Medicine
from app.database import Base

# Create tables first
Base.metadata.create_all(bind=engine)

COMMON_MEDICINES = [
    {"name": "Paracetamol 500mg", "generic_name": "Paracetamol", "category": "Analgesic/Antipyretic", "form": "Tablet", "strength": "500mg"},
    {"name": "Paracetamol 1000mg", "generic_name": "Paracetamol", "category": "Analgesic/Antipyretic", "form": "Tablet", "strength": "1000mg"},
    {"name": "Ibuprofen 400mg", "generic_name": "Ibuprofen", "category": "NSAID", "form": "Tablet", "strength": "400mg"},
    {"name": "Ibuprofen 600mg", "generic_name": "Ibuprofen", "category": "NSAID", "form": "Tablet", "strength": "600mg"},
    {"name": "Amoxicillin 500mg", "generic_name": "Amoxicillin", "category": "Antibiotic", "form": "Capsule", "strength": "500mg"},
    {"name": "Amoxicillin 250mg/5ml", "generic_name": "Amoxicillin", "category": "Antibiotic", "form": "Syrup", "strength": "250mg/5ml"},
    {"name": "Augmentin 1g", "generic_name": "Amoxicillin/Clavulanate", "category": "Antibiotic", "form": "Tablet", "strength": "1g"},
    {"name": "Azithromycin 500mg", "generic_name": "Azithromycin", "category": "Antibiotic", "form": "Tablet", "strength": "500mg"},
    {"name": "Metformin 500mg", "generic_name": "Metformin", "category": "Antidiabetic", "form": "Tablet", "strength": "500mg"},
    {"name": "Metformin 850mg", "generic_name": "Metformin", "category": "Antidiabetic", "form": "Tablet", "strength": "850mg"},
    {"name": "Amlodipine 5mg", "generic_name": "Amlodipine", "category": "Antihypertensive", "form": "Tablet", "strength": "5mg"},
    {"name": "Amlodipine 10mg", "generic_name": "Amlodipine", "category": "Antihypertensive", "form": "Tablet", "strength": "10mg"},
    {"name": "Lisinopril 10mg", "generic_name": "Lisinopril", "category": "Antihypertensive", "form": "Tablet", "strength": "10mg"},
    {"name": "Losartan 50mg", "generic_name": "Losartan", "category": "Antihypertensive", "form": "Tablet", "strength": "50mg"},
    {"name": "Omeprazole 20mg", "generic_name": "Omeprazole", "category": "Antacid/Proton pump inhibitor", "form": "Capsule", "strength": "20mg"},
    {"name": "Omeprazole 40mg", "generic_name": "Omeprazole", "category": "Antacid/Proton pump inhibitor", "form": "Capsule", "strength": "40mg"},
    {"name": "Pantoprazole 40mg", "generic_name": "Pantoprazole", "category": "Antacid/Proton pump inhibitor", "form": "Tablet", "strength": "40mg"},
    {"name": "Ranitidine 150mg", "generic_name": "Ranitidine", "category": "Antacid/H2 blocker", "form": "Tablet", "strength": "150mg"},
    {"name": "Metronidazole 250mg", "generic_name": "Metronidazole", "category": "Antibiotic/Antiprotozoal", "form": "Tablet", "strength": "250mg"},
    {"name": "Metronidazole 500mg", "generic_name": "Metronidazole", "category": "Antibiotic/Antiprotozoal", "form": "Tablet", "strength": "500mg"},
    {"name": "Ciprofloxacin 500mg", "generic_name": "Ciprofloxacin", "category": "Antibiotic", "form": "Tablet", "strength": "500mg"},
    {"name": "Cetirizine 10mg", "generic_name": "Cetirizine", "category": "Antihistamine", "form": "Tablet", "strength": "10mg"},
    {"name": "Loratadine 10mg", "generic_name": "Loratadine", "category": "Antihistamine", "form": "Tablet", "strength": "10mg"},
    {"name": "Salbutamol 4mg", "generic_name": "Salbutamol", "category": "Bronchodilator", "form": "Tablet", "strength": "4mg"},
    {"name": "Salbutamol inhaler", "generic_name": "Salbutamol", "category": "Bronchodilator", "form": "Inhaler", "strength": "100mcg/dose"},
    {"name": "Aspirin 100mg", "generic_name": "Acetylsalicylic acid", "category": "Antiplatelet", "form": "Tablet", "strength": "100mg"},
    {"name": "Aspirin 300mg", "generic_name": "Acetylsalicylic acid", "category": "Analgesic/Antipyretic", "form": "Tablet", "strength": "300mg"},
    {"name": "Diclofenac 50mg", "generic_name": "Diclofenac", "category": "NSAID", "form": "Tablet", "strength": "50mg"},
    {"name": "Diclofenac 75mg", "generic_name": "Diclofenac", "category": "NSAID", "form": "Injection", "strength": "75mg/3ml"},
    {"name": "Tramadol 50mg", "generic_name": "Tramadol", "category": "Analgesic/Opioid", "form": "Capsule", "strength": "50mg"},
    {"name": "Tramadol 100mg", "generic_name": "Tramadol", "category": "Analgesic/Opioid", "form": "Injection", "strength": "100mg/2ml"},
    {"name": "Diazepam 5mg", "generic_name": "Diazepam", "category": "Anxiolytic", "form": "Tablet", "strength": "5mg"},
    {"name": "Diazepam 10mg", "generic_name": "Diazepam", "category": "Anxiolytic", "form": "Injection", "strength": "10mg/2ml"},
    {"name": "Phenobarbital 30mg", "generic_name": "Phenobarbital", "category": "Anticonvulsant", "form": "Tablet", "strength": "30mg"},
    {"name": "Carbamazepine 200mg", "generic_name": "Carbamazepine", "category": "Anticonvulsant", "form": "Tablet", "strength": "200mg"},
    {"name": "Chlorpheniramine 4mg", "generic_name": "Chlorpheniramine", "category": "Antihistamine", "form": "Tablet", "strength": "4mg"},
    {"name": "Promethazine 25mg", "generic_name": "Promethazine", "category": "Antihistamine", "form": "Tablet", "strength": "25mg"},
    {"name": "Vitamin C 500mg", "generic_name": "Ascorbic acid", "category": "Vitamin", "form": "Tablet", "strength": "500mg"},
    {"name": "Vitamin D3 1000IU", "generic_name": "Cholecalciferol", "category": "Vitamin", "form": "Capsule", "strength": "1000IU"},
    {"name": "Folic acid 5mg", "generic_name": "Folic acid", "category": "Vitamin/Mineral", "form": "Tablet", "strength": "5mg"},
    {"name": "Iron sulfate 200mg", "generic_name": "Ferrous sulfate", "category": "Mineral", "form": "Tablet", "strength": "200mg"},
    {"name": "Artemether/Lumefantrine 20/120mg", "generic_name": "Artemether/Lumefantrine", "category": "Antimalarial", "form": "Tablet", "strength": "20/120mg"},
    {"name": "Artesunate 50mg", "generic_name": "Artesunate", "category": "Antimalarial", "form": "Tablet", "strength": "50mg"},
    {"name": "Quinine 300mg", "generic_name": "Quinine", "category": "Antimalarial", "form": "Tablet", "strength": "300mg"},
    {"name": "Oral Rehydration Salts", "generic_name": "ORS", "category": "Electrolyte", "form": "Powder/Sachet", "strength": "N/A"},
    {"name": "Zinc sulfate 20mg", "generic_name": "Zinc", "category": "Mineral", "form": "Tablet/Syrup", "strength": "20mg"},
    {"name": "Hydrochlorothiazide 25mg", "generic_name": "Hydrochlorothiazide", "category": "Diuretic", "form": "Tablet", "strength": "25mg"},
    {"name": "Furosemide 40mg", "generic_name": "Furosemide", "category": "Diuretic", "form": "Tablet", "strength": "40mg"},
    {"name": "Spironolactone 25mg", "generic_name": "Spironolactone", "category": "Diuretic", "form": "Tablet", "strength": "25mg"},
    {"name": "Glipizide 5mg", "generic_name": "Glipizide", "category": "Antidiabetic", "form": "Tablet", "strength": "5mg"},
    {"name": "Insulin NPH", "generic_name": "Isophane insulin", "category": "Antidiabetic", "form": "Injection", "strength": "100IU/ml"},
    {"name": "Insulin Regular", "generic_name": "Regular insulin", "category": "Antidiabetic", "form": "Injection", "strength": "100IU/ml"},
    {"name": "Atorvastatin 20mg", "generic_name": "Atorvastatin", "category": "Antilipidemic", "form": "Tablet", "strength": "20mg"},
    {"name": "Simvastatin 20mg", "generic_name": "Simvastatin", "category": "Antilipidemic", "form": "Tablet", "strength": "20mg"},
    {"name": "Warfarin 5mg", "generic_name": "Warfarin", "category": "Anticoagulant", "form": "Tablet", "strength": "5mg"},
    {"name": "Heparin 5000IU", "generic_name": "Heparin", "category": "Anticoagulant", "form": "Injection", "strength": "5000IU/ml"},
    {"name": "Prednisolone 5mg", "generic_name": "Prednisolone", "category": "Corticosteroid", "form": "Tablet", "strength": "5mg"},
    {"name": "Prednisolone 20mg", "generic_name": "Prednisolone", "category": "Corticosteroid", "form": "Tablet", "strength": "20mg"},
    {"name": "Dexamethasone 4mg", "generic_name": "Dexamethasone", "category": "Corticosteroid", "form": "Injection", "strength": "4mg/ml"},
    {"name": "Hydrocortisone 100mg", "generic_name": "Hydrocortisone", "category": "Corticosteroid", "form": "Injection", "strength": "100mg"},
    {"name": "Loperamide 2mg", "generic_name": "Loperamide", "category": "Antidiarrheal", "form": "Capsule", "strength": "2mg"},
    {"name": "Metoclopramide 10mg", "generic_name": "Metoclopramide", "category": "Antiemetic", "form": "Tablet", "strength": "10mg"},
    {"name": "Ondansetron 4mg", "generic_name": "Ondansetron", "category": "Antiemetic", "form": "Tablet", "strength": "4mg"},
    {"name": "Ondansetron 8mg", "generic_name": "Ondansetron", "category": "Antiemetic", "form": "Injection", "strength": "8mg/4ml"},
    {"name": "Albendazole 400mg", "generic_name": "Albendazole", "category": "Antiparasitic", "form": "Tablet", "strength": "400mg"},
    {"name": "Mebendazole 100mg", "generic_name": "Mebendazole", "category": "Antiparasitic", "form": "Tablet", "strength": "100mg"},
    {"name": "Clotrimazole cream", "generic_name": "Clotrimazole", "category": "Antifungal", "form": "Cream", "strength": "1%"},
    {"name": "Fluconazole 150mg", "generic_name": "Fluconazole", "category": "Antifungal", "form": "Capsule", "strength": "150mg"},
    {"name": "Nystatin 100000IU", "generic_name": "Nystatin", "category": "Antifungal", "form": "Suspension", "strength": "100000IU/ml"},
    {"name": "Gentamicin 80mg", "generic_name": "Gentamicin", "category": "Antibiotic", "form": "Injection", "strength": "80mg/2ml"},
    {"name": "Ceftriaxone 1g", "generic_name": "Ceftriaxone", "category": "Antibiotic", "form": "Injection", "strength": "1g"},
    {"name": "Ceftriaxone 500mg", "generic_name": "Ceftriaxone", "category": "Antibiotic", "form": "Injection", "strength": "500mg"},
    {"name": "Ampicillin 500mg", "generic_name": "Ampicillin", "category": "Antibiotic", "form": "Capsule", "strength": "500mg"},
    {"name": "Ampicillin 1g", "generic_name": "Ampicillin", "category": "Antibiotic", "form": "Injection", "strength": "1g"},
    {"name": "Benzyl penicillin 1MU", "generic_name": "Penicillin G", "category": "Antibiotic", "form": "Injection", "strength": "1 million IU"},
    {"name": "Tetracycline 250mg", "generic_name": "Tetracycline", "category": "Antibiotic", "form": "Capsule", "strength": "250mg"},
    {"name": "Doxycycline 100mg", "generic_name": "Doxycycline", "category": "Antibiotic", "form": "Capsule", "strength": "100mg"},
    {"name": "Erythromycin 250mg", "generic_name": "Erythromycin", "category": "Antibiotic", "form": "Tablet", "strength": "250mg"},
    {"name": "Erythromycin 500mg", "generic_name": "Erythromycin", "category": "Antibiotic", "form": "Tablet", "strength": "500mg"},
    {"name": "Clarithromycin 500mg", "generic_name": "Clarithromycin", "category": "Antibiotic", "form": "Tablet", "strength": "500mg"},
    {"name": "Nitrofurantoin 100mg", "generic_name": "Nitrofurantoin", "category": "Antibiotic", "form": "Tablet", "strength": "100mg"},
    {"name": "Sulfamethoxazole/Trimethoprim 400/80mg", "generic_name": "Co-trimoxazole", "category": "Antibiotic", "form": "Tablet", "strength": "400/80mg"},
    {"name": "Clindamycin 300mg", "generic_name": "Clindamycin", "category": "Antibiotic", "form": "Capsule", "strength": "300mg"},
]


def seed_medicines():
    db = SessionLocal()
    try:
        count = 0
        for med in COMMON_MEDICINES:
            existing = db.query(Medicine).filter(Medicine.name == med["name"]).first()
            if not existing:
                db.add(Medicine(**med))
                count += 1
        db.commit()
        print(f"Seeded {count} new medicines. Total: {db.query(Medicine).count()}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_medicines()
