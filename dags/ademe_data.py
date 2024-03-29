"""
### Tutorial Documentation
Documentation that goes along with the Airflow tutorial located
[here](https://airflow.apache.org/tutorial.html)
"""

from __future__ import annotations
import os
import re
import json
import time
from datetime import datetime, timedelta
import logging
from urllib.parse import urlparse, parse_qs
import typing as t
import glob
import requests
import pandas as pd
from azure.storage.blob import BlobServiceClient
from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from db_utils import Database

try:
    ACCOUNT_KEY = Variable.get("STORAGE_BLOB_ADEME_MLOPS")
    DATA_PATH = "/opt/airflow/data/"
except:
    ACCOUNT_KEY = os.environ.get("STORAGE_BLOB_ADEME_MLOPS")
    DATA_PATH = "/Users/alexis/work/ademe_mlops/data/"

DOWNLOADED_FILES_PATH = os.path.join(DATA_PATH, "ademe-dpe-tertiaire")
URL_FILE = os.path.join(DATA_PATH, "api", "url.json")
RESULTS_FILE = os.path.join(DATA_PATH, "api", "results.json")
CONTAINER_NAME = "ademe-dpe-tertiaire"
ACCOUNT_NAME = "skatai4ademe4mlops"


logger = logging.getLogger(__name__)


def init_container_client():
    connection_string = f"DefaultEndpointsProtocol=https;AccountName={ACCOUNT_NAME};"
    connection_string += f"AccountKey={ACCOUNT_KEY};EndpointSuffix=core.windows.net"

    blob_service_client_ = BlobServiceClient.from_connection_string(connection_string)

    container_client_ = blob_service_client_.get_container_client(container=CONTAINER_NAME)
    return blob_service_client_, container_client_


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


def check_environment_setup(*op_args):
    logger.info("--" * 20)
    logger.info(f"[info logger] cwd: {os.getcwd()}")
    logger.info(f"[info logger] URL_FILE: {URL_FILE}")
    assert os.path.isfile(URL_FILE)
    logger.info(f"[info logger] RESULTS_FILE: {RESULTS_FILE}")
    logger.info(f"[info logger] account_key: {ACCOUNT_KEY}")
    assert ACCOUNT_KEY is not None

    container_client_ = op_args[0]
    logger.info(f"[info logger] assert container_client exists \n{container_client_.exists()}")
    assert container_client_.exists()

    try:
        pg_password = Variable.get("AZURE_PG_PASSWORD")
    except:
        pg_password = os.environ.get("AZURE_PG_PASSWORD")

    assert pg_password is not None

    logger.info("--" * 20)


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


def upload_data(*op_args):
    """
    Uploads local data files to Azure Blob Storage container.

    - Establishes a connection to the Azure Blob Storage using the provided account credentials.
    - Retrieves the list of existing blobs in the specified container.
    - Gets a list of local data files to upload.
    - Uploads each local file to the container if it doesn't already exist.

    Environment Variables:
        STORAGE_BLOB_ADEME_MLOPS: Azure Storage account key.

    """

    blob_service_client_ = op_args[0]
    container_client_ = op_args[1]

    # List all blobs in the container
    blobs_list = [file["name"] for file in container_client_.list_blobs()]

    # get all data files on local
    local_data_files = glob.glob(f"{DOWNLOADED_FILES_PATH}/*.json")
    for filename in local_data_files:
        blob_name = filename.split("/")[-1]
        if blob_name not in blobs_list:
            # upload file to container
            blob_client = blob_service_client_.get_blob_client(
                container=CONTAINER_NAME, blob=blob_name
            )

            logger.info("\nUploading to Azure Storage as blob:\n\t" + blob_name)

            # Upload the created file
            with open(filename, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)

            logger.info("Upload completed")


def cleanup_local_data(*op_args):
    """
    removes downlaoded files only keeps {keep_n}
    """
    keep_n = 4
    container_client_ = op_args[0]

    # List all blobs in the container
    blobs_list = [file["name"] for file in container_client_.list_blobs()]

    # get all data files on local
    local_data_files = sorted(glob.glob(f"{DOWNLOADED_FILES_PATH}/*.json"))
    local_data_files = local_data_files[:-keep_n]
    # delete all files on local that are in the container

    for filename in local_data_files:
        blob_name = filename.split("/")[-1]
        if blob_name in blobs_list:
            print(blob_name)

            try:
                os.remove(filename)
            except Exception as e:
                print(f"Error occurred: {e}.")


def save_postgresdb():
    assert os.path.isfile(RESULTS_FILE)

    # read previous API call output
    with open(RESULTS_FILE, encoding="utf-8") as file:
        data = json.load(file)

    data = pd.DataFrame(data["results"])
    # set columns
    new_columns = rename_columns(data.columns)
    data.columns = new_columns
    data = data.astype(str).replace("nan", "")

    # now check that the data does not have columns not already in the table
    db = Database()
    check_cols_query = """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name   = 'dpe_tertiaire';
    """
    table_cols = pd.read_sql(check_cols_query, con=db.engine)
    table_cols = [col for col in table_cols["column_name"] if col != "id"]

    # drop data columns not in table_cols
    for col in data.columns:
        if col not in table_cols:
            data.drop(columns=[col], inplace=True)
            logger.info(f"dropped column {col} from dataset")

    # add empty columns in data that are in the table
    for col in table_cols:
        if col not in data.columns:
            if col in ["created_at", "modified_at"]:
                data[col] = datetime.now()
            else:
                data[col] = ""
            logger.info(f"added column {col} in data")

    # data = data[table_cols].copy()
    assert sorted(data.columns) == sorted(table_cols)

    logger.info(f"loaded {data.shape}")

    # to_sql
    data.to_sql(name="dpe_tertiaire", con=db.engine, if_exists="append", index=False)
    db.close()


def drop_duplicates():
    query = """
        DELETE FROM dpe_tertiaire
        WHERE id IN (
        SELECT id
        FROM (
            SELECT id, ROW_NUMBER() OVER (PARTITION BY n_dpe ORDER BY id DESC) AS rn
            FROM dpe_tertiaire
        ) t
        WHERE t.rn > 1
        );
    """

    db = Database()
    db.execute(query)
    db.close()


with DAG(
    "ademe_data",
    default_args={
        "depends_on_past": False,
        "email": ["alexis.perrier@gmail.com"],
        "email_on_failure": True,
        "email_on_retry": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=2),
    },
    description="Get data from ADEME API, save to postgres and in azure bucket, then clean up",
    schedule="*/5 * * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ademe"],
) as dag:
    blob_service_client, container_client = init_container_client()

    check_environment_setup = PythonOperator(
        task_id="check_environment_setup",
        python_callable=check_environment_setup,
        op_args=[container_client],
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
        op_args=[blob_service_client, container_client],
    )

    cleanup_local_data = PythonOperator(
        task_id="cleanup_local_data", python_callable=cleanup_local_data, op_args=[container_client]
    )

    save_postgresdb = PythonOperator(
        task_id="save_postgresdb",
        python_callable=save_postgresdb,
    )

    drop_duplicates = PythonOperator(
        task_id="drop_duplicates",
        python_callable=drop_duplicates,
    )

    check_environment_setup.set_downstream(ademe_api)
    ademe_api.set_downstream(process_results)
    # save to postgres
    ademe_api.set_downstream(save_postgresdb)
    save_postgresdb.set_downstream(drop_duplicates)
    # upload data
    process_results.set_downstream(upload_data)
    upload_data.set_downstream(cleanup_local_data)
