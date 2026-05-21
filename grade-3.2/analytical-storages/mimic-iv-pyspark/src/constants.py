BASE_DIR = "artifacts/mimic"
WAREHOUSE_DIR = "artifacts/results"

# Dimension tables
dim_patients_path = f"{BASE_DIR}/hosp/patients.csv.gz"
dim_d_icd_diagnoses_path = f"{BASE_DIR}/hosp/d_icd_diagnoses.csv.gz"
dim_diagnoses_icd_path = f"{BASE_DIR}/hosp/diagnoses_icd.csv.gz"

# Fact tables
facts_admissions_path = f"{BASE_DIR}/hosp/admissions.csv.gz"

# ICU
icu_stays_path = f"{BASE_DIR}/icu/icustays.csv.gz"
