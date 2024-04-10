import mlflow
import mlflow.pyfunc
from flask import Flask, request, jsonify
from db_utils import Database
import random
from features import FeatureSets
import pandas as pd
import numpy as np
import json
from mlflow import MlflowClient
experiment_name = "dpe_tertiaire"

# mlflow.set_tracking_uri("http://host.docker.internal:5001")
# mlflow.set_tracking_uri("http://localhost:9090")

mlflow.set_tracking_uri("http://localhost:5001")

def load_data_for_inference():
    db = Database()
    query = f"select * from dpe_training order by random() limit 500"
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
    data = data.sample(1)
    y = data['etiquette_dpe']
    X = data[FeatureSets.train_columns]

    return X, y


X, y = load_data_for_inference()

# Load the model from the MLflow Model Registry
champion_model_name = "dpe_champion"
champ = mlflow.sklearn.load_model(f"models:/{champion_model_name}/Staging")
yhat = champ.best_estimator_.predict(X)[0]
print(f"y: {y}")
print(f"yhat: {yhat}")
print(f"proba: {np.round(champ.best_estimator_.predict_proba(X)[0][yhat-1]*100.0,1)}%")
print(champ.best_estimator_.predict_proba(X)[0])




# # Initialize the Flask application
# app = Flask(__name__)

# # Define a prediction endpoint
# @app.route('/predict', methods=['POST'])
# def predict():
#     # Get the JSON data from the client
#     json_data = request.get_json(force=True)

#     # Predict using the MLflow model
#     predictions = model.predict(json_data)

#     # Return the predictions as JSON
#     return jsonify(predictions.tolist())

# # Start the Flask web server
# if __name__ == '__main__':
#     app.run(port=1234)
