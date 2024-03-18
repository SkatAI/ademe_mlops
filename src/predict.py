import os
import json

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import mlflow

mlflow.set_tracking_uri(uri="http://127.0.0.1:808")
mlflow.set_experiment("experiment_01")
mlflow.autolog()

if __name__ == "__main__":
    # find the best model
    # https://mlflow.org/docs/latest/python_api/mlflow.html?highlight=search_runs#mlflow.search_runs
    runs = mlflow.search_runs(experiment_ids=[2], order_by=["metrics.best_cv_score desc"])
    best_run = runs.head(1).to_dict(orient="records")[0]

    print(f"best run id: ", best_run["run_id"])

    # save to envt
    os.environ["MLFLOW_RUN_ID"] = best_run["run_id"]

    # reload some data for predictions

    data = pd.read_csv("./data/dpe_tertiaire_20240307.csv")
    data = data.sample(n=1, random_state=808).reset_index(drop=True)

    # save data to sample.json

    with open("./data/sample.json", "w") as f:
        json.dump(data.to_dict(orient="records"), f, indent=4)

    # Load model as a PyFuncModel.
    model_uri = f"runs:/{best_run['run_id']}/best_estimator"
    loaded_model = mlflow.pyfunc.load_model(model_uri)

    # Predict on a Pandas DataFrame.
    loaded_model.predict(pd.DataFrame(data))

