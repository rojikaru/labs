import json
from os import path

from airflow.sdk import Asset
from airflow.sdk.bases.hook import BaseHook


car_charges_extra = BaseHook.get_connection("car_charges_conn").extra
assert (
    car_charges_extra
), "Connection 'car_charges_conn' must have 'extra' field with JSON content"
datasets_path = json.loads(car_charges_extra)["path"]

user_dim_asset = Asset(f"file://{path.join(datasets_path, 'dim_user.jsonl')}")
location_dim_asset = Asset(f"file://{path.join(datasets_path, 'dim_location.jsonl')}")
charger_dim_asset = Asset(f"file://{path.join(datasets_path, 'dim_charger.jsonl')}")
date_dim_asset = Asset(f"file://{path.join(datasets_path, 'dim_date.jsonl')}")
time_dim_asset = Asset(f"file://{path.join(datasets_path, 'dim_time.jsonl')}")
fact_charging_asset = Asset(f"file://{path.join(datasets_path, 'fact_charging.jsonl')}")

ASSETS = [
    user_dim_asset,
    location_dim_asset,
    charger_dim_asset,
    date_dim_asset,
    time_dim_asset,
    fact_charging_asset,
]
