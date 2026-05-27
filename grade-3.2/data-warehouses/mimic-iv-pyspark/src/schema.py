from typing import Literal
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, TimestampType, FloatType,
)

# https://mimic.mit.edu/docs/IV/modules/hosp/

patients_schema = StructType([
    StructField("subject_id", IntegerType(), False),
    StructField("gender", StringType(), False),
    StructField("anchor_age", IntegerType(), False),
    StructField("anchor_year", IntegerType(), False),
    StructField("anchor_year_group", StringType(), False),
    StructField("dod", TimestampType(), True),
])

d_icd_diagnoses_schema = StructType([
    StructField("icd_code", StringType(), False),
    StructField("icd_version", IntegerType(), False),
    StructField("long_title", StringType(), True),
])

diagnoses_icd_schema = StructType([
    StructField("subject_id", IntegerType(), False),
    StructField("hadm_id", IntegerType(), False),
    StructField("seq_num", IntegerType(), False),
    StructField("icd_code", StringType(), True),
    StructField("icd_version", IntegerType(), True),
])

admissions_schema = StructType([
    StructField("subject_id", IntegerType(), False),
    StructField("hadm_id", IntegerType(), False),
    StructField("admittime", TimestampType(), False),
    StructField("dischtime", TimestampType(), True),
    StructField("deathtime", TimestampType(), True),
    StructField("admission_type", StringType(), False),
    StructField("admit_provider_id", StringType(), True),
    StructField("admission_location", StringType(), True),
    StructField("discharge_location", StringType(), True),
    StructField("insurance", StringType(), True),
    StructField("language", StringType(), True),
    StructField("marital_status", StringType(), True),
    StructField("race", StringType(), True),
    StructField("edregtime", TimestampType(), True),
    StructField("edouttime", TimestampType(), True),
    StructField("hospital_expire_flag", IntegerType(), True),
])

icustays_schema = StructType([
    StructField("subject_id", IntegerType(), False),
    StructField("hadm_id", IntegerType(), False),
    StructField("stay_id", IntegerType(), False),
    StructField("first_careunit", StringType(), True),
    StructField("last_careunit", StringType(), True),
    StructField("intime", TimestampType(), False),
    StructField("outtime", TimestampType(), True),
    StructField("los", FloatType(), True),
])

SchemaName = Literal[
    "patients", "d_icd_diagnoses", "diagnoses_icd", "admissions", "icustays"
]
