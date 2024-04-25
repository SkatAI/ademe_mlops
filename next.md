# Next, final session

- load model with MLFlow
- serve prediction with FastAPI
- add data transform FastAPI
- create streamlit
- add FastAPI to docker compose

- make sure airflow and FastAPI start when the VM starts

- simplify evaluation

# Next airflow pipeline

- get new data
- make predictions
- if predictions are bad or model too old => retrain model
- deploy model if better / not worse

## train model pipeline

- get data from db
- feature eng.
- Feast + Great expectations
-

## Infer
gets data from streamlit app ?
gets model prediction


Donc
### async data transformation

how to store encoders ? in local json files

0) get data from dpe-tertiaire
join on not exists in training_data

1)
- transformer le features.py en class
- distinguer data transformation pour training (many samples) et pour infer (1 sample)
see https://chat.openai.com/share/ed78df52-60a9-4612-9eff-69b5e70c193a
- make class available for training and for inference

2) creer pipeline extraction et transformation
store training data in new table ?

training_data table:
n_dpe, date, status : valid, not valid, error
DPE etiquette et GES etiquette
features as json string

### modele training
get data from training_data table
train sklearn models on recent data (time window: 7 past days since most recent data, n_samples ...)

train, test, validation 60, 20, 20
if new model on validation is better than current model
deploy model to production
else ??

Fast API for inference!





