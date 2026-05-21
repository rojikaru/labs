from pyspark.sql import DataFrame
from pyspark.sql.functions import col, year, month, quarter, when


def build_hospitalizations(
    admissions: DataFrame,
    patients: DataFrame,
    diagnoses_icd: DataFrame,
    d_icd_diagnoses: DataFrame,
) -> DataFrame:
    # Join admissions with patient demographics
    hosp = (
        admissions.alias("a")
        .join(patients.alias("p"), "subject_id", "inner")
        .select(
            col("a.subject_id"),
            col("a.hadm_id"),
            col("a.admittime"),
            col("a.dischtime"),
            col("a.deathtime"),
            col("a.admission_type"),
            col("a.admission_location"),
            col("a.discharge_location"),
            col("a.insurance"),
            col("a.race"),
            col("a.hospital_expire_flag"),
            col("a.los_days"),
            col("a.edregtime"),
            col("p.gender"),
            col("p.anchor_age"),
        )
        .withColumn("admission_year", year("admittime"))
        .withColumn("admission_month", month("admittime"))
        .withColumn("admission_quarter", quarter("admittime"))
        .withColumn("age_group", when(col("anchor_age") <= 40, "18-40")
                    .when(col("anchor_age") <= 65, "41-65")
                    .when(col("anchor_age") <= 80, "66-80")
                    .otherwise("80+"))
    )

    # Primary diagnosis (seq_num=1) with ICD title
    primary_dx = (
        diagnoses_icd.filter(col("seq_num") == 1)
        .join(d_icd_diagnoses, ["icd_code", "icd_version"], "left")
        .select(
            col("hadm_id"),
            col("icd_code").alias("primary_icd_code"),
            col("long_title").alias("primary_diagnosis"),
        )
    )

    # Attach primary diagnosis to hospitalizations
    return hosp.join(primary_dx, "hadm_id", "left")
