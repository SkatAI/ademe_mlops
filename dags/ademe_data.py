"""
### Tutorial Documentation
Documentation that goes along with the Airflow tutorial located
[here](https://airflow.apache.org/tutorial.html)
"""

from __future__ import annotations
import os
import re
import requests
import json
from datetime import datetime, timedelta
import time
import logging
from urllib.parse import urlparse, parse_qs
import glob
import typing as t
import pandas as pd
from azure.storage.blob import BlobServiceClient
from airflow.models.dag import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from db_utils import Database

DATA_PATH = f"/opt/airflow/data/"
DOWNLOADED_FILES_PATH = os.path.join(DATA_PATH, "ademe-dpe-tertiaire", "url.json")
URL_FILE = os.path.join(DATA_PATH, "api", "url.json")
RESULTS_FILE = os.path.join(DATA_PATH, "api", "results.json")
CONTAINER_NAME = "ademe-dpe-tertiaire"
ACCOUNT_NAME = "skatai4ademe4mlops"

try:
    ACCOUNT_KEY = Variable.get("STORAGE_BLOB_ADEME_MLOPS")
except:
    ACCOUNT_KEY = os.environ.get("STORAGE_BLOB_ADEME_MLOPS")

logger = logging.getLogger(__name__)


def rename_columns(columns: t.List[str]) -> t.List[str]:
    """
    rename columns
    """

    columns = [col.lower() for col in columns]

    rgxs = [
        (r"[°|/|']", "_"),
        (r"²", "2"),
        (r"[(|)]", ""),
        (r"é|è", "e"),
        (r"â", "a"),
        (r"^_", "dpe_"),
        (r"_+", "_"),
    ]
    for rgx in rgxs:
        columns = [re.sub(rgx[0], rgx[1], col) for col in columns]

    return columns


def save_postgresdb():
    assert os.path.isfile(RESULTS_FILE)

    # read previous API call output
    with open(RESULTS_FILE, encoding="utf-8") as file:
        data = json.load(file)

    data = pd.DataFrame(data["results"])

    logger.info(f"loaded {data.shape}")

    # set columns
    new_columns = rename_columns(data.columns)
    data.columns = new_columns

    # to_sql
    db = Database()
    data.to_sql(name="dpe_tertiaire", con=db.engine, if_exists="append", index=False)
    db.close()


def check_environment_setup():
    logger.info("--" * 20)
    logger.info(f"[info logger] cwd: {os.getcwd()}")
    logger.info(f"[info logger] URL_FILE: {URL_FILE}")
    assert os.path.isfile(URL_FILE)
    logger.info(f"[info logger] RESULTS_FILE: {RESULTS_FILE}")
    logger.info(f"[info logger] account_key: {ACCOUNT_KEY}")
    logger.info("--" * 20)
    assert ACCOUNT_KEY is not None


def ademe_api():
    """
    Interrogates the ADEME API using the specified URL and payload from a JSON file.

    - Reads the URL and payload from a JSON file defined by the constant `URL_FILE`.
    - Performs a GET request to the obtained URL with the given payload.
    - Saves the results to a JSON file defined by the constant `RESULTS_FILE`.

    Raises:
        AssertionError: If the URL file does not exist, or if the retrieved URL or payload is None.
        requests.exceptions.RequestException: If the GET request encounters an error.

    """

    # test url file exists
    assert os.path.isfile(URL_FILE)
    # open url file
    with open(URL_FILE, encoding="utf-8") as file:
        url = json.load(file)
    assert url.get("url") is not None
    assert url.get("payload") is not None

    # make GET requests
    results = requests.get(url.get("url"), params=url.get("payload"), timeout=5)
    assert results.raise_for_status() is None

    data = results.json()

    # save results to file
    with open(RESULTS_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def process_results():
    """
    Processes the results obtained from the previous API call,
    updates the URL file,
    and saves the data to a new file.

    - Reads the results from a JSON file defined by the constant `RESULTS_FILE`.
    - Extracts the base URL and payload from the 'next' field of the results.
    - Updates the URL file with the same URL and the new payload.
    - Saves the results data to a new JSON file with a filename containing a timestamp.

    Raises:
        AssertionError: If the results file does not exist.

    """
    # test url file exists
    assert os.path.isfile(RESULTS_FILE)

    # read previous API call output
    with open(RESULTS_FILE, encoding="utf-8") as file:
        data = json.load(file)

    # new url is same as old url
    base_url = data.get("next").split("?")[0]

    # extract payload as dict
    parsed_url = urlparse(data.get("next"))
    query_params = parse_qs(parsed_url.query)
    new_payload = {k: v[0] if len(v) == 1 else v for k, v in query_params.items()}

    # save new url (same as old url) with new payload into url.json
    new_url = {"url": base_url, "payload": new_payload}

    with open(URL_FILE, "w", encoding="utf-8") as file:
        json.dump(new_url, file, indent=4, ensure_ascii=False)

    # saves data to data file
    # append current timestamp (up to the second to the filename)
    timestamp = int(time.time())
    data_filename = os.path.join(DOWNLOADED_FILES_PATH, f"data_{timestamp}.json")

    with open(data_filename, "w", encoding="utf-8") as file:
        json.dump(data["results"], file, indent=4, ensure_ascii=False)


def upload_data():
    """
    Uploads local data files to Azure Blob Storage container.

    - Establishes a connection to the Azure Blob Storage using the provided account credentials.
    - Retrieves the list of existing blobs in the specified container.
    - Gets a list of local data files to upload.
    - Uploads each local file to the container if it doesn't already exist.

    Environment Variables:
        STORAGE_BLOB_ADEME_MLOPS: Azure Storage account key.

    """

    connection_string = f"DefaultEndpointsProtocol=https;AccountName={ACCOUNT_NAME};"
    connection_string += f"AccountKey={ACCOUNT_KEY};EndpointSuffix=core.windows.net"

    blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    container_client = blob_service_client.get_container_client(container=CONTAINER_NAME)

    # List all blobs in the container
    blobs_list = [file["name"] for file in container_client.list_blobs()]

    # get all data files on local
    local_data_files = glob.glob(f"{DOWNLOADED_FILES_PATH}/*.json")
    for filename in local_data_files:
        blob_name = filename.split("/")[-1]
        if blob_name not in blobs_list:
            # upload file to container
            blob_client = blob_service_client.get_blob_client(
                container=CONTAINER_NAME, blob=blob_name
            )

            logger.info("\nUploading to Azure Storage as blob:\n\t" + blob_name)

            # Upload the created file
            with open(filename, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)

            logger.info("Upload completed")


with DAG(
    "ademe_data",
    default_args={
        "depends_on_past": False,
        "email": ["alexis.perrier@gmail.com"],
        "email_on_failure": True,
        "email_on_retry": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    },
    description="Sandbox",
    # schedule=timedelta(hours=1),
    schedule="*/30 * * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ademe"],
) as dag:
    check_environment_setup = PythonOperator(
        task_id="check_environment_setup",
        python_callable=check_environment_setup,
    )

    ademe_api = PythonOperator(
        task_id="ademe_api",
        python_callable=ademe_api,
    )

    process_results = PythonOperator(
        task_id="process_results",
        python_callable=process_results,
    )

    upload_data = PythonOperator(
        task_id="upload_data",
        python_callable=upload_data,
    )

    save_postgresdb = PythonOperator(
        task_id="save_postgresdb",
        python_callable=save_postgresdb,
    )

    # check_environment_setup >> ademe_api >> [save_postgresdb, process_results >> upload_data]

    check_environment_setup.set_downstream(ademe_api)
    # ademe_api.set_downstream([save_postgresdb, process_results])
    ademe_api.set_downstream(save_postgresdb)
    ademe_api.set_downstream(process_results)
    process_results.set_downstream(upload_data)
    # t1.set_downstream([t2, t3])
