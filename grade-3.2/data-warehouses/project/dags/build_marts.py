from datetime import timedelta
from airflow.sdk import dag, task
from helpers.db import db_hook, sql_file_path


@task
def sql_task(filename: str) -> None:
    sqlasset_path = sql_file_path(filename)
    with open(sqlasset_path) as f:
        db_hook().run(f.read())


@dag(
    dag_id="build_data_marts",
    tags=["data_marts"],
    schedule=None,
    catchup=False,
    is_paused_upon_creation=False,
    dagrun_timeout=timedelta(minutes=30),
)
def build_data_marts():
    create_marts = sql_task("create_mart_tables.sql")
    monthly_by_location = sql_task("mart_monthly_stats_by_location.sql")
    usage_by_membership = sql_task("mart_usage_by_membership_and_timeofday.sql")
    charger_efficiency = sql_task("mart_charger_efficiency_by_type.sql")

    # marts are independent of each other, run in parallel after tables exist
    create_marts >> [monthly_by_location, usage_by_membership, charger_efficiency]


build_data_marts()
