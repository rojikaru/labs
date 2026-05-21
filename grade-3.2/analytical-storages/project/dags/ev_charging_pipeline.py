from datetime import datetime, timedelta
from airflow.sdk import dag, Variable
from airflow.providers.standard.sensors.filesystem import FileSensor

from scripts.processing import (
    process_charger_dim,
    process_date_dim,
    process_fact_charging,
    process_location_dim,
    process_time_dim,
    process_user_dim,
)


@dag(
    dag_id="ev_charging_pipeline",
    tags=["ev_charging"],
    start_date=datetime(2026, 3, 1),
    schedule="*/5 * * * *",
    catchup=False,  # Skip runs since the start date until now
    dagrun_timeout=timedelta(minutes=10),
    is_paused_upon_creation=False,
)
def ev_charging_pipeline():
    wait_for_file = FileSensor(
        task_id="check_for_data",
        filepath=Variable.get("raw_data_filename"),
        fs_conn_id="my_filesystem_conn",
        poke_interval=5,
        timeout=10,
    )

    dim_user_task = process_user_dim()
    dim_location_task = process_location_dim()
    dim_date_task = process_date_dim()
    dim_time_task = process_time_dim()
    dim_charger_task = process_charger_dim()
    fact_task = process_fact_charging()

    wait_for_file >> [dim_user_task, dim_location_task, dim_date_task, dim_time_task]
    dim_location_task >> dim_charger_task
    fact_task << [
        dim_user_task,
        dim_location_task,
        dim_date_task,
        dim_time_task,
        dim_charger_task,
    ]


ev_charging_pipeline()
