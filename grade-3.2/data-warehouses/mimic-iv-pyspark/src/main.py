import os

from pyspark.sql import SparkSession

from src.load import load_dataset
from src.clean import clean_admissions, clean_patients
from src.transform import build_hospitalizations
from src.analytics import (
    mortality_by_admission_type,
    top_diagnoses,
    los_by_insurance,
    readmissions_30d,
    seasonal_admission_trends,
    mortality_by_age_group,
    ed_utilization_by_quarter,
)
from src.output import write_parquet


if "JAVA_TOOL_OPTIONS" not in os.environ:
    os.environ["JAVA_TOOL_OPTIONS"] = "-Xmx12g -XX:+UseG1GC -XX:-UseContainerSupport"
else:
    os.environ["JAVA_TOOL_OPTIONS"] += " -Xmx12g -XX:+UseG1GC -XX:-UseContainerSupport"


def main():
    spark = (
        SparkSession.builder
        .appName("MIMIC-IV Hospitalization Analytics")
        .master("local[*]")
        # Give them enough heap space.
        .config("spark.driver.memory", "12g")
        .config("spark.executor.memory", "12g")
        # Increase the fraction of heap used for execution/storage (default 0.6).
        .config("spark.memory.fraction", "0.8")
        # Of that fraction, reserve less for cached data so execution tasks have
        # more room to work (default 0.5 - halved here to reduce spill pressure).
        .config("spark.memory.storageFraction", "0.3")
        # Limit the max size of a single collect result to avoid driver OOM.
        .config("spark.driver.maxResultSize", "4g")
        # More shuffle partitions spread the data more finely, keeping each
        # partition smaller and less likely to exhaust per-task memory.
        .config("spark.sql.shuffle.partitions", "200")
        # Avoid broadcasting large tables; let Spark sort-merge join instead.
        .config("spark.sql.autoBroadcastJoinThreshold", "-1")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    # Load raw data
    admissions_raw = load_dataset(spark, "admissions")
    patients_raw = load_dataset(spark, "patients")
    diagnoses_icd = load_dataset(spark, "diagnoses_icd")
    d_icd_diagnoses = load_dataset(spark, "d_icd_diagnoses")

    # Clean
    admissions = clean_admissions(admissions_raw)
    patients = clean_patients(patients_raw)

    # Transform: build enriched fact table
    hospitalizations = build_hospitalizations(
        admissions, patients, diagnoses_icd, d_icd_diagnoses
    )
    hospitalizations.cache()
    print(f"[main] hospitalization records: {hospitalizations.count()}")

    # Analytics: answer real-world questions
    results = {
        "mortality_by_admission_type": mortality_by_admission_type(hospitalizations),
        "top_diagnoses": top_diagnoses(hospitalizations),
        "los_by_insurance": los_by_insurance(hospitalizations),
        "readmissions_30d": readmissions_30d(hospitalizations),
        "seasonal_trends": seasonal_admission_trends(hospitalizations),
        "mortality_by_age_group": mortality_by_age_group(hospitalizations),
        "ed_utilization": ed_utilization_by_quarter(hospitalizations),
    }

    # Show sample results
    for name, result_df in results.items():
        print(f"\n{'[' + name + ']':^60}")
        result_df.show(10, truncate=False)

    # Write to parquet
    write_parquet(hospitalizations, "hospitalizations", ["admission_year", "admission_month"])
    for name, result_df in results.items():
        write_parquet(result_df, name)

    spark.stop()


if __name__ == "__main__":
    main()
