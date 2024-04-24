# from typing import Literal
# from pydantic import BaseModel, conint

# class InputData(BaseModel):
#     type_energie: Literal[-1,1,2,3,4,5,6,7]
#     periode_construction: conint(ge=0, le=5)
#     secteur_activite: conint(ge=0, le=30)
#     type_usage_energie_n_1: Literal[-1,1,2,3,4,5,6,7,8,9,10]
#     type_energie_principale_chauffage: Literal[-1,1,2,3,4,5,6,7]
#     type_energie_n_1: Literal[-1,1,2,3,4,5,6,7]
#     version_dpe: int
#     surface_utile: int
#     conso_kwhep_m2_an: int
#     conso_e_finale_energie_n_1: int


from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/bonjour/{name}")
async def bonjour(name: str):
    return {"message": f"Bonjour {name}"}
