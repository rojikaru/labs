from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def clean_admissions(admissions: DataFrame) -> DataFrame:
    df = admissions.withColumn(
        "los_days",
        F.datediff("dischtime", "admittime")
    )

    # Define real-world data quality issues
    df = df.withColumn(
        "bad_null_times",
        F.col("admittime").isNull() | F.col("dischtime").isNull()
    )

    df = df.withColumn(
        "bad_time_order",
        F.col("los_days").isNotNull() & (F.col("los_days") < 0)
    )

    df = df.withColumn(
        "bad_los_outlier",
        (F.col("los_days") < 0) | (F.col("los_days") > 3650)
    )

    df = df.withColumn(
        "bad_death_inconsistency",
        (F.col("deathtime").isNotNull()) &
        (F.col("deathtime") < F.col("admittime"))
    )

    df = df.withColumn(
        "is_valid",
        ~(F.col("bad_null_times") |
          F.col("bad_time_order") |
          F.col("bad_los_outlier") |
          F.col("bad_death_inconsistency"))
    )

    # Audit stats (single pass counts via aggregation)
    stats = df.agg(
        F.count("*").alias("total"),
        F.sum(F.when(F.col("bad_null_times"), 1).otherwise(0)).alias("null_time"),
        F.sum(F.when(F.col("bad_time_order"), 1).otherwise(0)).alias("bad_order"),
        F.sum(F.when(F.col("bad_los_outlier"), 1).otherwise(0)).alias("outliers"),
        F.sum(F.when(F.col("bad_death_inconsistency"), 1).otherwise(0)).alias("death_issues"),
    ).collect()[0]

    print(f"[admissions-clean]")
    print(f" total={stats['total']}")
    print(f" null_times={stats['null_time']}")
    print(f" bad_order={stats['bad_order']}")
    print(f" los_outliers={stats['outliers']}")
    print(f" death_inconsistency={stats['death_issues']}")

    return (
        df
        .filter(F.col("is_valid"))
        .drop("is_valid",
              "bad_null_times",
              "bad_time_order",
              "bad_los_outlier",
              "bad_death_inconsistency")
    )

def clean_patients(patients: DataFrame) -> DataFrame:
    dupes = patients.groupBy("subject_id").count().filter(F.col("count") > 1)

    df = patients.join(
        dupes.select("subject_id").withColumn("is_duplicate", F.lit(True)),
        on="subject_id",
        how="left"
    ).withColumn(
        "is_duplicate",
        F.col("is_duplicate").isNotNull()
    )

    # Real constraints in MIMIC-IV
    df = df.withColumn(
        "bad_age",
        (F.col("anchor_age") < 0) | (F.col("anchor_age") > 120)
    )

    df = df.withColumn(
        "missing_gender",
        F.col("gender").isNull()
    )

    df = df.withColumn(
        "age_topcoded",
        F.col("anchor_age") >= 89  # MIMIC-IV top-coding behavior
    )

    df = df.withColumn(
        "is_valid",
        ~(F.col("bad_age") | F.col("missing_gender") | F.col("is_duplicate"))
    )

    stats = df.agg(
        F.count("*").alias("total"),
        F.sum(F.when(F.col("bad_age"), 1).otherwise(0)).alias("bad_age"),
        F.sum(F.when(F.col("missing_gender"), 1).otherwise(0)).alias("missing_gender"),
        F.sum(F.when(F.col("is_duplicate"), 1).otherwise(0)).alias("duplicates"),
    ).collect()[0]

    print(f"[patients-clean]")
    print(f" total={stats['total']}")
    print(f" bad_age={stats['bad_age']}")
    print(f" missing_gender={stats['missing_gender']}")
    print(f" duplicates={stats['duplicates']}")

    return (
        df
        .filter(F.col("is_valid"))
        .drop("is_valid", "bad_age", "missing_gender", "is_duplicate", "age_topcoded")
    )
