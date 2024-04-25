# from typing import Literal
# from pydantic import BaseModel, conint
# from pydantic import BaseModel, ValidationError, ValidationInfo, field_validator
# from enum import Enum

from dags.features import FeatureProcessor, FeatureSets
from fastapi import FastAPI
from pydantic import BaseModel

from mlflow import MlflowClient
import mlflow
import pandas as pd


# raw_data = {
#     # 'n_dpe': '2391T1055502K',
#     # 'etiquette_dpe': 'B',
#     # 'etiquette_ges': 'A',
#     'version_dpe': '2.2',
#     'periode_construction': '1983-1988',
#     'secteur_activite': 'W : Administrations, banques, bureaux',
#     'type_energie_principale_chauffage': '',
#     'type_energie_n_1': 'Électricité',
#     'type_usage_energie_n_1': "périmètre de l'usage inconnu",
#     'surface_utile': '100.0',
#     'conso_kwhep_m2_an': '81.1',
#     'conso_e_finale_energie_n_1': '2474.3'
# }



app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/bonjour/{name}")
async def bonjour(name: str):
    return {"message": f"Bonjour {name}"}


class Data(BaseModel):  # Define a Pydantic model to correctly parse and validate incoming data
    data: dict

@app.post("/predict/")  # Change to POST method
async def predict(data: Data):  # Use the Pydantic model for data validation
    raw_data = pd.DataFrame([data.data])
    fp = FeatureProcessor(raw_data, "etiquette_dpe")
    fp.process()
    # load champion model
    # challenger_model_name = "dpe_challenger"
    # client = MlflowClient()
    champion_model_name = "dpe_champion"
    champ = mlflow.sklearn.load_model(f"models:/{champion_model_name}/Staging")
    print(champ)
    yhat = champ.best_estimator_.predict(fp.data)
    print(yhat)



    return yhat

