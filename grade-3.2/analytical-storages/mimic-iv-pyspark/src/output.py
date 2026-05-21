from pyspark.sql import DataFrame
from src.constants import WAREHOUSE_DIR


def write_parquet(df: DataFrame, name: str, partition_by: list[str] | None = None):
    path = f"{WAREHOUSE_DIR}/{name}"
    writer = df.write.mode("overwrite")
    if partition_by:
        writer = writer.partitionBy(*partition_by)
    writer.parquet(path)
    print(f"[output] wrote {path}")
