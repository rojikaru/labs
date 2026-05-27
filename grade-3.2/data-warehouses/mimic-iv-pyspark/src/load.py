from typing import Mapping

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import StructType

from src import schema, constants

DATASETS: Mapping[schema.SchemaName, tuple[StructType, str]] = {
    "patients": (schema.patients_schema, constants.dim_patients_path),
    "d_icd_diagnoses": (schema.d_icd_diagnoses_schema, constants.dim_d_icd_diagnoses_path),
    "diagnoses_icd": (schema.diagnoses_icd_schema, constants.dim_diagnoses_icd_path),
    "admissions": (schema.admissions_schema, constants.facts_admissions_path),
    "icustays": (schema.icustays_schema, constants.icu_stays_path),
}


def load_dataset(session: SparkSession, name: schema.SchemaName) -> DataFrame:
    ds_schema, path = DATASETS[name]
    return session.read.csv(path, header=True, schema=ds_schema)
