from datetime import timedelta

import polars as pl
import psycopg2

from airflow.sdk.bases.hook import BaseHook
from airflow.sdk import dag, task
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator

from helpers.assets import asset_path
from helpers.db import db_hook, sql_file_path

from scripts.assets import (
    ASSETS,
    charger_dim_asset,
    date_dim_asset,
    fact_charging_asset,
    location_dim_asset,
    time_dim_asset,
    user_dim_asset,
)


@task
def ensure_db() -> None:
    c = BaseHook.get_connection("warehouse_db_conn")
    params = {
        "host": c.host,
        "port": c.port or 5432,
        "user": c.login,
        "password": c.password,
    }

    conn = psycopg2.connect(**params, dbname="postgres")
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute(
        """
        DO $$ BEGIN
            IF NOT EXISTS (SELECT FROM pg_database WHERE datname = %(db)s) THEN
                EXECUTE 'CREATE DATABASE ' || quote_ident(%(db)s);
            END IF;
        END $$;
        """,
        {"db": c.schema},
    )

    cur.close()
    conn.close()


@task
def create_tables() -> None:
    sqlasset_path = sql_file_path("create_warehouse_tables.sql")
    with open(sqlasset_path) as f:
        db_hook().run(f.read())


@task
def truncate_tables() -> None:
    # Truncate in FK-safe order: children before parents
    db_hook().run(
        "TRUNCATE facts_charges, dim_time, dim_charger, dim_user, dim_date, dim_location"
        " RESTART IDENTITY;"
    )


@task
def load_user_dim() -> None:
    rows = (
        pl.read_ndjson(asset_path(user_dim_asset))
        .select(["id", "car_model", "membership_type"])
        .rows()
    )
    conn = db_hook().get_conn()
    cur = conn.cursor()
    cur.executemany(
        "INSERT INTO dim_user (id, car_model, membership_type) VALUES (%s, %s, %s)",
        rows,
    )
    conn.commit()
    cur.close()


@task
def load_location_dim() -> None:
    rows = pl.read_ndjson(asset_path(location_dim_asset)).select(["id", "name"]).rows()
    conn = db_hook().get_conn()
    cur = conn.cursor()
    cur.executemany("INSERT INTO dim_location (id, name) VALUES (%s, %s)", rows)
    conn.commit()
    cur.close()


@task
def load_date_dim() -> None:
    rows = (
        pl.read_ndjson(asset_path(date_dim_asset))
        .select(["id", "iso", "day", "month", "year", "day_of_week", "week"])
        .rows()
    )
    conn = db_hook().get_conn()
    cur = conn.cursor()
    cur.executemany(
        "INSERT INTO dim_date (id, iso, day, month, year, day_of_week, week)"
        " VALUES (%s, %s, %s, %s, %s, %s, %s)",
        rows,
    )
    conn.commit()
    cur.close()


@task
def load_charger_dim() -> None:
    rows = (
        pl.read_ndjson(asset_path(charger_dim_asset))
        .select(["id", "location_id", "type"])
        .rows()
    )
    conn = db_hook().get_conn()
    cur = conn.cursor()
    cur.executemany(
        "INSERT INTO dim_charger (id, location_id, type) VALUES (%s, %s, %s)", rows
    )
    conn.commit()
    cur.close()


@task
def load_time_dim() -> None:
    rows = (
        pl.read_ndjson(asset_path(time_dim_asset))
        .select(["id", "date_id", "time_of_day", "hours", "minutes"])
        .rows()
    )
    conn = db_hook().get_conn()
    cur = conn.cursor()
    cur.executemany(
        "INSERT INTO dim_time (id, date_id, time_of_day, hours, minutes) VALUES (%s, %s, %s, %s, %s)",
        rows,
    )
    conn.commit()
    cur.close()


@task
def load_facts() -> None:
    cols = [
        "id",
        "charger_id",
        "user_id",
        "start_time",
        "end_time",
        "duration_hours",
        "energy_consumed_kwh",
        "charging_rate_kwh",
        "charging_cost_kwh",
        "battery_percentage_start",
        "battery_percentage_end",
        "vehicle_age_years",
        "distance_since_last_charge_km",
        "ambient_temperature_celsius",
    ]
    rows = pl.read_ndjson(asset_path(fact_charging_asset)).select(cols).rows()
    conn = db_hook().get_conn()
    cur = conn.cursor()
    cur.executemany(
        "INSERT INTO facts_charges"
        " (id, charger_id, user_id, start_time, end_time, duration_hours,"
        "  energy_consumed_kwh, charging_rate_kwh, charging_cost_kwh,"
        "  battery_percentage_start, battery_percentage_end, vehicle_age_years,"
        "  distance_since_last_charge_km, ambient_temperature_celsius)"
        " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        rows,
    )
    conn.commit()
    cur.close()


@dag(
    dag_id="load_warehouse",
    tags=["load_warehouse"],
    schedule=ASSETS,
    catchup=False,
    is_paused_upon_creation=False,
    dagrun_timeout=timedelta(minutes=30),
)
def load_warehouse():
    # Pipeline wiring
    db_ready = ensure_db()
    tables_ready = create_tables()
    truncated = truncate_tables()
    db_ready >> tables_ready >> truncated

    user = load_user_dim()
    location = load_location_dim()
    date = load_date_dim()
    truncated >> [user, location, date]

    charger = load_charger_dim()
    time = load_time_dim()
    location >> charger
    date >> time

    facts = load_facts()
    [user, charger, time] >> facts

    trigger_marts = TriggerDagRunOperator(
        task_id="trigger_build_marts",
        trigger_dag_id="build_data_marts",
        wait_for_completion=False,
    )
    facts >> trigger_marts

load_warehouse()
