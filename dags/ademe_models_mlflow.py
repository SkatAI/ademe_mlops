"""
Training the model
"""
import json
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from sklearn.metrics import precision_score, recall_score

import logging

from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable

# local
from db_utils import Database
from train import TrainDPE
from features import FeatureSets

logger = logging.getLogger(__name__)

# --------------------------------------------------
# set up MLflow
# --------------------------------------------------
import mlflow
from mlflow import MlflowClient
experiment_name = "dpe_tertiaire"

mlflow.set_tracking_uri("http://host.docker.internal:5001")
# mlflow.set_tracking_uri("http://localhost:9090")


print("--"*40)
print("mlflow set experiment")
print("--"*40)
mlflow.set_experiment(experiment_name)

mlflow.sklearn.autolog()

# --------------------------------------------------
# load data
# --------------------------------------------------

def load_data_for_inference(n_samples):
    db = Database()
    query = f"select * from dpe_training order by created_at desc limit {n_samples}"
    df = pd.read_sql(query, con=db.engine)
    db.close()
    # dump payload into new dataframe
    df["payload"] = df["payload"].apply(lambda d: json.loads(d))
    data = pd.DataFrame(list(df.payload.values))

    data.drop(columns="n_dpe", inplace=True)
    data = data.astype(int)
    data = data[data.etiquette_dpe >0].copy()
    data.reset_index(inplace = True, drop = True)
    print(data.shape)
    y = data['etiquette_dpe']
    X = data[FeatureSets.train_columns]

    return X, y

def load_data_for_training(n_samples):
    # TODO simply load payload not all columns
    db = Database()
    query = f"select * from dpe_training order by random() limit {n_samples}"
    df = pd.read_sql(query, con=db.engine)
    db.close()
    # dump payload into new dataframe
    df["payload"] = df["payload"].apply(lambda d: json.loads(d))
    data = pd.DataFrame(list(df.payload.values))
    data.drop(columns="n_dpe", inplace=True)
    data = data.astype(int)
    data = data[data.etiquette_dpe >0].copy()
    data.reset_index(inplace = True, drop = True)
    return data

# ---------------------------------------------
#  tasks
# ---------------------------------------------
challenger_model_name = "dpe_challenger"
champion_model_name = "dpe_champion"
client = MlflowClient()

def train_model():
    data = load_data_for_training(n_samples = 2000)
    with mlflow.start_run() as run:
        train = TrainDPE(data)
        train.main()
        train.report()

        try:
            model = client.get_registered_model(challenger_model_name)
        except:
            print("model does not exist")
            print("registering new model", challenger_model_name)
            client.create_registered_model(challenger_model_name, description = "sklearn random forest for dpe_tertiaire")

        # set version and stage
        run_id = run.info.run_id
        model_uri = f"runs:/{run_id}/model"
        model_version = client.create_model_version(
            name=challenger_model_name,
            source=model_uri,
            run_id=run_id
        )

        client.transition_model_version_stage(
            name=challenger_model_name,
            version=model_version.version,
            stage = 'Staging'
        )

def create_champion():
    '''
    if there is not champion yet, creates a champion from current challenger
    '''
    results = client.search_registered_models(filter_string=f"name='{champion_model_name}'")
    # if not exists: promote current model
    if len(results) == 0:
        print("champion model not found, promoting challenger to champion")

        champion_model = client.copy_model_version(
            src_model_uri=f"models:/{challenger_model_name}/Staging",
            dst_name=champion_model_name,
        )
        client.transition_model_version_stage(
            name=champion_model_name,
            version=champion_model.version,
            stage = 'Staging'
        )

        # reload champion and print info
        results = client.search_registered_models(filter_string=f"name='{champion_model_name}'")
        print(results[0].latest_versions)


def promote_model():

    X, y = load_data_for_inference(1000)
    # inference challenger and champion
    # load model & inference
    chl = mlflow.sklearn.load_model(f"models:/{challenger_model_name}/Staging")
    yhat = chl.best_estimator_.predict(X)
    challenger_precision = precision_score(y, yhat, average="weighted")
    challenger_recall = recall_score(y, yhat, average="weighted")
    print(f"\t challenger_precision: {np.round(challenger_precision, 2)}")
    print(f"\t challenger_recall: {np.round(challenger_recall, 2)}")

    # inference on production model
    champ = mlflow.sklearn.load_model(f"models:/{champion_model_name}/Staging")
    yhat = champ.best_estimator_.predict(X)
    champion_precision = precision_score(y, yhat, average="weighted")
    champion_recall = recall_score(y, yhat, average="weighted")
    print(f"\t champion_precision: {np.round(champion_precision, 2)}")
    print(f"\t champion_recall: {np.round(champion_recall, 2)}")

    # if performance 5% above current champion: promote
    if challenger_precision > champion_precision * 1.05:
        print(f"{challenger_precision} > {champion_precision}")
        print("Promoting new model to champion ")
        champion_model = client.copy_model_version(
            src_model_uri=f"models:/{challenger_model_name}/Staging",
            dst_name=champion_model_name,
        )

        client.transition_model_version_stage(
            name=champion_model_name,
            version=champion_model.version,
            stage = 'Staging'
        )
    else:
        print(f"{challenger_precision} < {champion_precision}")
        print("champion remains undefeated ")

# ---------------------------------------------
#  DAG
# ---------------------------------------------
with DAG(
    "ademe_models",
    default_args={
        "retries": 0,
        "retry_delay": timedelta(minutes=10),
    },
    description="Model training and promotion",
    schedule=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ademe"],
) as dag:
    train_model_task = PythonOperator(
        task_id="train_model_task",
        python_callable=train_model
    )

    # create_champion_task = PythonOperator(
    #     task_id="create_champion_task",
    #     python_callable=create_champion
    # )

    # promote_model_task = PythonOperator(
    #     task_id="promote_model_task",
    #     python_callable=promote_model
    # )

    # train_model_task >> create_champion_task >> promote_model_task
    train_model_task

