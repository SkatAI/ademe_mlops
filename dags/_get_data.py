"""
Builds the Ademe dataset from the Ademe API with Airflow
"""

import os

# import json
from urllib.parse import urlparse, parse_qs

# import time
# import glob
# import requests
# from azure.storage.blob import BlobServiceClient

CONTAINER_NAME = "ademe-dpe-tertiaire"
DATA_PATH = f"./data/{CONTAINER_NAME}"
API_PATH = "./data/api/"
URL_FILE = os.path.join(API_PATH, "url.json")
RESULTS_FILE = os.path.join(API_PATH, "results.json")

import sys

sys.path.append("./src")

import textwrap
from datetime import datetime, timedelta

import airflow
from airflow import DAG
from airflow.operators.python import PythonOperator

# from build_dataset import interrogate_api, process_results, upload_data


def interrogate_api():
    pass


def process_results():
    pass


def upload_data():
    pass


if __name__ == "__main__":
    default_args = {
        "depends_on_past": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    }

    with DAG(
        "ADEME_data",
        default_args=default_args,
        description="Get Ademe data",
        schedule=timedelta(minutes=10),
        start_date=datetime(2024, 1, 1),
        catchup=False,
        tags=["example"],
    ) as dag:
        interrogate_api = PythonOperator(
            task_id="interrogate_api",
            python_callable=interrogate_api,
        )

        process_results = PythonOperator(
            task_id="process_results",
            python_callable=process_results,
        )

        upload_data = PythonOperator(
            task_id="upload_data",
            python_callable=upload_data,
        )

        #  set dependencies between tasks.
        interrogate_api >> process_results >> upload_data
