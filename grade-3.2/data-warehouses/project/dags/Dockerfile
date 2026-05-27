# https://hub.docker.com/r/apache/airflow

ARG AIRFLOW_VERSION=3.2.1
ARG PYTHON_VERSION=3.14

FROM apache/airflow:slim-${AIRFLOW_VERSION}-python${PYTHON_VERSION}

WORKDIR /app

COPY ./pyproject.toml .

RUN pip install .
