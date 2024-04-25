# from typing import Literal
# from pydantic import BaseModel, conint
# from pydantic import BaseModel, ValidationError, ValidationInfo, field_validator
# from enum import Enum

from dags.features import FeatureProcessor, FeatureSets

raw_data = {
    # 'n_dpe': '2391T1055502K',
    # 'etiquette_dpe': 'B',
    # 'etiquette_ges': 'A',
    'version_dpe': '2.2',
    'periode_construction': '1983-1988',
    'secteur_activite': 'W : Administrations, banques, bureaux',
    'type_energie_principale_chauffage': '',
    'type_energie_n_1': 'Électricité',
    'type_usage_energie_n_1': "périmètre de l'usage inconnu",
    'surface_utile': '100.0',
    'conso_kwhep_m2_an': '81.1',
    'conso_e_finale_energie_n_1': '2474.3'
}

train_columns = [
    "periode_construction",
    "secteur_activite",
    "type_energie_principale_chauffage",
    "type_energie_n_1",
    "type_usage_energie_n_1",
    "surface_utile",
    "conso_kwhep_m2_an",
    "conso_e_finale_energie_n_1",
    "version_dpe",
]


from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/bonjour/{name}")
async def bonjour(name: str):
    return {"message": f"Bonjour {name}"}
