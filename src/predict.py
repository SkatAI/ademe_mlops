import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV, KFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import numpy as np
import mlflow

mlflow.set_tracking_uri(uri="http://127.0.0.1:808")
mlflow.set_experiment("experiment_01")
mlflow.autolog()

import os
import json

if __name__ == "__main__":
    """
    find the best model
    https://mlflow.org/docs/latest/python_api/mlflow.html?highlight=search_runs#mlflow.search_runs
    """
    runs = mlflow.search_runs(experiment_ids=[2], order_by=["metrics.best_cv_score desc"])
    best_run = runs.head(1).to_dict(orient="records")[0]

    print(f"best run id: ", best_run["run_id"])

    # save to envt
    os.environ["MLFLOW_RUN_ID"] = best_run["run_id"]

    """
    reload some data for predictions
    """

    data = pd.read_csv("./data/dpe_tertiaire_20240307.csv")
    data = data.sample(n=1, random_state=808).reset_index(drop=True)

    # save data to sample.json

    with open("./data/sample.json", "w") as f:
        json.dump(data.to_dict(orient="records"), f, indent=4)

    """
    load the model
    """

    # Load model as a PyFuncModel.
    model_uri = f"runs:/{best_run['run_id']}/best_estimator"
    loaded_model = mlflow.pyfunc.load_model(model_uri)

    # Predict on a Pandas DataFrame.
    loaded_model.predict(pd.DataFrame(data))

    """
    Questions
    - peut on obtenir des probas au lieu de la categorie ?
    - explorer mlflow.pyfunc, quelles fonctionnalités sont intéréssantes?
    https://mlflow.org/docs/latest/python_api/mlflow.pyfunc.html
    - pourquoi on ne peut pas loader
    logged_sk_model = f"runs:/{best_run['run_id']}/sk_models"
    sk_model = mlflow.sklearn.load_model(logged_sk_model)

    """
