from os import path
from airflow.providers.postgres.hooks.postgres import PostgresHook


def db_hook() -> PostgresHook:
    return PostgresHook(postgres_conn_id="warehouse_db_conn")


def sql_file_path(filename: str) -> str:
    return path.join(
        path.dirname(path.abspath(__file__)),
        "..",
        "sql",
        filename,
    )
