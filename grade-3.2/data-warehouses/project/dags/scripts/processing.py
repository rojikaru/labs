import json
import os
from typing import Any, Mapping, cast
from airflow.sdk import task, Variable
from airflow.sdk.bases.hook import BaseHook
import polars as pl

from helpers.assets import asset_path
from scripts import assets

CHARGING_LOCATION_COLUMN = "Charging Station Location"
CHARGING_START_TIME_COLUMN = "Charging Start Time"
CHARGING_END_TIME_COLUMN = "Charging End Time"


def _get_raw_file_path() -> str:
    extra = BaseHook.get_connection("my_filesystem_conn").extra
    if not extra:
        raise ValueError(
            "Connection 'my_filesystem_conn' must have 'extra' field with JSON containing 'path' key."
        )

    filename: str = Variable.get("raw_data_filename")
    return os.path.join(json.loads(extra)["path"], filename)


def _get_datasets_path() -> str:
    extra = BaseHook.get_connection("car_charges_conn").extra
    if not extra:
        raise ValueError(
            "Connection 'car_charges_conn' must have 'extra' field with JSON containing 'path' key."
        )
    return json.loads(extra)["path"]


def _dataset_file_path(filename: str) -> str:
    return os.path.join(_get_datasets_path(), filename)


def _write_to_task_outlets(df: pl.DataFrame, **context: Mapping[str, Any]) -> None:
    task = cast(Any, context["task"])
    for outlet in task.outlets:
        target_path = asset_path(outlet)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        df.write_ndjson(target_path)


@task(outlets=[assets.user_dim_asset])
def process_user_dim(**context: Mapping[str, Any]) -> None:
    raw_df = pl.scan_csv(_get_raw_file_path())
    user_df = (
        raw_df.select(
            [
                pl.col("User ID").str.replace("User_", "").cast(pl.Int64).alias("id"),
                pl.col("Vehicle Model").alias("car_model"),
                pl.col("User Type").alias("membership_type"),
            ]
        )
        .unique()
        .sort("id")
        .collect()
    )
    _write_to_task_outlets(user_df, **context)


@task(outlets=[assets.location_dim_asset])
def process_location_dim(**context: Mapping[str, Any]) -> None:
    raw_df = pl.scan_csv(_get_raw_file_path())
    location_df = (
        raw_df.select(
            [
                pl.col(CHARGING_LOCATION_COLUMN).alias("name"),
            ]
        )
        .drop_nulls()
        .unique()
        .sort("name")
        .with_row_index("id", offset=1)
        .collect()
    )
    _write_to_task_outlets(location_df, **context)


@task(outlets=[assets.charger_dim_asset])
def process_charger_dim(**context: Mapping[str, Any]) -> None:
    raw_df = pl.scan_csv(_get_raw_file_path())
    location_path = _dataset_file_path("dim_location.jsonl")
    location_df = pl.read_ndjson(location_path).select(
        [
            pl.col("id").alias("location_id"),
            pl.col("name").alias("location_name"),
        ]
    )

    charger_df = (
        raw_df.select(
            [
                pl.col(CHARGING_LOCATION_COLUMN).alias("location_name"),
                pl.col("Charger Type").alias("type"),
            ]
        )
        .join(location_df.lazy(), on="location_name", how="left")
        .drop("location_name")
        .unique()
        .sort(["location_id", "type"])
        .with_row_index("id", offset=1)
        .collect()
    )
    _write_to_task_outlets(charger_df, **context)


@task(outlets=[assets.date_dim_asset])
def process_date_dim(**context: Mapping[str, Any]) -> None:
    raw_df = pl.scan_csv(_get_raw_file_path())
    date_df = (
        raw_df.select(
            [
                pl.col(CHARGING_START_TIME_COLUMN)
                .str.strptime(pl.Datetime, strict=False)
                .dt.date()
                .cast(pl.String)
                .alias("iso"),
            ]
        )
        .drop_nulls()
        .unique()
        .sort("iso")
        .with_row_index("id", offset=1)
        .with_columns(
            [
                pl.col("iso").str.strptime(pl.Date, "%Y-%m-%d").dt.day().alias("day"),
                pl.col("iso")
                .str.strptime(pl.Date, "%Y-%m-%d")
                .dt.month()
                .alias("month"),
                pl.col("iso").str.strptime(pl.Date, "%Y-%m-%d").dt.year().alias("year"),
                pl.col("iso")
                .str.strptime(pl.Date, "%Y-%m-%d")
                .dt.strftime("%A")
                .alias("day_of_week"),
                pl.col("iso").str.strptime(pl.Date, "%Y-%m-%d").dt.week().alias("week"),
            ]
        )
        .collect()
    )
    _write_to_task_outlets(date_df, **context)


@task(outlets=[assets.time_dim_asset])
def process_time_dim(**context: Mapping[str, Any]) -> None:
    raw_df = pl.scan_csv(_get_raw_file_path())
    date_df = pl.read_ndjson(_dataset_file_path("dim_date.jsonl")).select(
        [
            pl.col("id").alias("date_id"),
            pl.col("iso").alias("date_iso"),
        ]
    )
    start_times = raw_df.select(
        [
            pl.col(CHARGING_START_TIME_COLUMN)
            .str.strptime(pl.Datetime, strict=False)
            .alias("dt"),
        ]
    )
    end_times = raw_df.select(
        [
            pl.col(CHARGING_END_TIME_COLUMN)
            .str.strptime(pl.Datetime, strict=False)
            .alias("dt"),
        ]
    )

    time_df = (
        pl.concat([start_times, end_times], how="vertical")
        .select(
            [
                pl.col("dt").dt.date().cast(pl.String).alias("date_iso"),
                pl.col("dt").dt.hour().alias("hours"),
                pl.col("dt").dt.minute().alias("minutes"),
            ]
        )
        .drop_nulls()
        .unique()
        .sort(["date_iso", "hours", "minutes"])
        .join(date_df.lazy(), on="date_iso", how="left")
        .with_columns(
            [
                pl.when(pl.col("hours").is_between(5, 11))
                .then(pl.lit("Morning"))
                .when(pl.col("hours").is_between(12, 16))
                .then(pl.lit("Afternoon"))
                .when(pl.col("hours").is_between(17, 20))
                .then(pl.lit("Evening"))
                .otherwise(pl.lit("Night"))
                .alias("time_of_day"),
            ]
        )
        .select(["date_id", "time_of_day", "hours", "minutes"])
        .with_row_index("id", offset=1)
        .collect()
    )
    _write_to_task_outlets(time_df, **context)


@task(outlets=[assets.fact_charging_asset])
def process_fact_charging(**context: Mapping[str, Any]) -> None:
    raw_df = pl.scan_csv(_get_raw_file_path())
    date_df = pl.read_ndjson(_dataset_file_path("dim_date.jsonl")).select(
        [
            pl.col("id").alias("date_id"),
            pl.col("iso").alias("date_iso"),
        ]
    )
    location_df = pl.read_ndjson(_dataset_file_path("dim_location.jsonl")).select(
        [
            pl.col("id").alias("location_id"),
            pl.col("name").alias("location_name"),
        ]
    )
    charger_df = pl.read_ndjson(_dataset_file_path("dim_charger.jsonl")).select(
        [
            pl.col("id").alias("charger_id"),
            pl.col("location_id"),
            pl.col("type"),
        ]
    )
    time_df = pl.read_ndjson(_dataset_file_path("dim_time.jsonl")).select(
        [
            pl.col("id").alias("time_id"),
            pl.col("date_id"),
            pl.col("hours"),
            pl.col("minutes"),
        ]
    )

    fact_df = (
        raw_df.select(
            [
                pl.col("User ID")
                .str.replace("User_", "")
                .cast(pl.Int64)
                .alias("user_id"),
                pl.col(CHARGING_LOCATION_COLUMN).alias("location_name"),
                pl.col("Charger Type").alias("type"),
                pl.col(CHARGING_START_TIME_COLUMN)
                .str.strptime(pl.Datetime, strict=False)
                .alias("start_dt"),
                pl.col(CHARGING_END_TIME_COLUMN)
                .str.strptime(pl.Datetime, strict=False)
                .alias("end_dt"),
                pl.col("Charging Duration (hours)").alias("duration_hours"),
                pl.col("Energy Consumed (kWh)").alias("energy_consumed_kwh"),
                pl.col("Charging Rate (kW)").alias("charging_rate_kwh"),
                pl.col("Charging Cost (USD)").alias("charging_cost_kwh"),
                pl.col("State of Charge (Start %)").alias("battery_percentage_start"),
                pl.col("State of Charge (End %)").alias("battery_percentage_end"),
                pl.col("Vehicle Age (years)").alias("vehicle_age_years"),
                pl.col("Distance Driven (since last charge) (km)").alias(
                    "distance_since_last_charge_km"
                ),
                pl.col("Temperature (°C)").alias("ambient_temperature_celsius"),
            ]
        )
        .join(location_df.lazy(), on="location_name", how="left")
        .join(charger_df.lazy(), on=["location_id", "type"], how="left")
        .with_columns(
            [
                pl.col("start_dt").dt.date().cast(pl.String).alias("start_date_iso"),
                pl.col("start_dt").dt.hour().alias("start_hours"),
                pl.col("start_dt").dt.minute().alias("start_minutes"),
                pl.col("end_dt").dt.date().cast(pl.String).alias("end_date_iso"),
                pl.col("end_dt").dt.hour().alias("end_hours"),
                pl.col("end_dt").dt.minute().alias("end_minutes"),
            ]
        )
        .join(
            date_df.lazy().rename(
                {
                    "date_id": "start_date_id",
                    "date_iso": "start_date_iso",
                }
            ),
            on="start_date_iso",
            how="left",
        )
        .join(
            date_df.lazy().rename(
                {
                    "date_id": "end_date_id",
                    "date_iso": "end_date_iso",
                }
            ),
            on="end_date_iso",
            how="left",
        )
        .join(
            time_df.lazy().rename(
                {
                    "time_id": "start_time",
                    "date_id": "start_date_id",
                    "hours": "start_hours",
                    "minutes": "start_minutes",
                }
            ),
            on=["start_date_id", "start_hours", "start_minutes"],
            how="left",
        )
        .join(
            time_df.lazy().rename(
                {
                    "time_id": "end_time",
                    "date_id": "end_date_id",
                    "hours": "end_hours",
                    "minutes": "end_minutes",
                }
            ),
            on=["end_date_id", "end_hours", "end_minutes"],
            how="left",
        )
        .select(
            [
                pl.col("charger_id"),
                pl.col("user_id"),
                pl.col("start_time"),
                pl.col("end_time"),
                pl.col("duration_hours"),
                pl.col("energy_consumed_kwh"),
                pl.col("charging_rate_kwh"),
                pl.col("charging_cost_kwh"),
                pl.col("battery_percentage_start"),
                pl.col("battery_percentage_end"),
                pl.col("vehicle_age_years"),
                pl.col("distance_since_last_charge_km"),
                pl.col("ambient_temperature_celsius"),
            ]
        )
        .with_row_index("id", offset=1)
        .collect()
    )

    _write_to_task_outlets(fact_df, **context)
