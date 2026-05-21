
from airflow import Asset


def asset_path(asset: Asset) -> str:
    return asset.uri.replace("file://", "")
