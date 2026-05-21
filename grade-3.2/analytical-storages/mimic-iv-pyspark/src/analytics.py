from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, count, round as spark_round, sum as Fsum, avg, lag, datediff, when,
)
from pyspark.sql.window import Window


def mortality_by_admission_type(df: DataFrame) -> DataFrame:
    # Q: Which admission types have highest in-hospital mortality?
    return (
        df.groupBy("admission_type")
        .agg(
            count("hadm_id").alias("total_admissions"),
            Fsum("hospital_expire_flag").alias("deaths"),
            spark_round(
                Fsum("hospital_expire_flag") / count("hadm_id") * 100, 2
            ).alias("mortality_pct"),
        )
        .orderBy(col("mortality_pct").desc())
    )


def top_diagnoses(df: DataFrame, top_n: int = 20) -> DataFrame:
    # Q: What are the most common primary diagnoses?
    return (
        df.filter(col("primary_diagnosis").isNotNull())
        .groupBy("primary_icd_code", "primary_diagnosis")
        .agg(count("hadm_id").alias("frequency"))
        .orderBy(col("frequency").desc())
        .limit(top_n)
    )


def los_by_insurance(df: DataFrame) -> DataFrame:
    # Q: How does average length of stay differ by insurance type?
    return (
        df.groupBy("insurance")
        .agg(
            count("hadm_id").alias("admissions"),
            spark_round(avg("los_days"), 2).alias("avg_los_days"),
            spark_round(avg(col("hospital_expire_flag")) * 100, 2).alias("mortality_pct"),
        )
        .orderBy(col("avg_los_days").desc())
    )


def readmissions_30d(df: DataFrame) -> DataFrame:
    # Q: Which patients were readmitted within 30 days?
    w = Window.partitionBy("subject_id").orderBy("admittime")
    with_prev = df.withColumn("prev_dischtime", lag("dischtime").over(w))
    readmit = (
        with_prev
        .withColumn("days_since_last", datediff("admittime", "prev_dischtime"))
        .filter(col("days_since_last").between(1, 30))
    )
    return (
        readmit.groupBy("primary_diagnosis")
        .agg(count("hadm_id").alias("readmission_count"))
        .orderBy(col("readmission_count").desc())
        .limit(20)
    )


def seasonal_admission_trends(df: DataFrame) -> DataFrame:
    # Q: How do admission volumes vary by quarter/month?
    return (
        df.groupBy("admission_year", "admission_quarter", "admission_month")
        .agg(count("hadm_id").alias("admissions"))
        .orderBy("admission_year", "admission_month")
    )


def mortality_by_age_group(df: DataFrame) -> DataFrame:
    # Q: How does in-hospital mortality vary across age groups?
    return (
        df.groupBy("age_group")
        .agg(
            count("hadm_id").alias("total_admissions"),
            Fsum("hospital_expire_flag").alias("deaths"),
            spark_round(
                Fsum("hospital_expire_flag") / count("hadm_id") * 100, 2
            ).alias("mortality_pct"),
        )
        .orderBy("age_group")
    )


def ed_utilization_by_quarter(df: DataFrame) -> DataFrame:
    # Q: What fraction of admissions come through the ED?
    return (
        df.groupBy("admission_year", "admission_quarter")
        .agg(
            count("hadm_id").alias("total_admissions"),
            Fsum(when(col("edregtime").isNotNull(), 1).otherwise(0)).alias("ed_admissions"),
            spark_round(
                Fsum(when(col("edregtime").isNotNull(), 1).otherwise(0))
                / count("hadm_id") * 100, 2
            ).alias("ed_pct"),
        )
        .orderBy("admission_year", "admission_quarter")
    )
