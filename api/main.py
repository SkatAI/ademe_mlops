from fastapi import FastAPI
import mlflow
import pandas as pd
from dags import FeatureProcessor
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/bonjour/{name}")
async def bonjour(name:str):
    return {"message": f"Bonjour {name}"}

@app.get("/plus/")
async def plus(a: int, b: int):
    print("addition")
    return {"message": a+b}

mlflow.set_tracking_uri("http://20.51.187.25:5001")
mlflow.set_experiment("dpe_tertiaire")

@app.post("/predict/")  # Change to POST method
async def predict(data: Data):  # Use the Pydantic model for data validation
    raw_data = pd.DataFrame([data.data])
    fp = FeatureProcessor(raw_data, "etiquette_dpe")
    fp.process()

    champ = mlflow.sklearn.load_model(f"models:/dpe_champion/Staging")
    print(champ)
    yhat = champ.best_estimator_.predict(fp.data)
    return {"message": {
                "prediction": str(yhat[0])
            }
        }
