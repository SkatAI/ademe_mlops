# Day 3
Retour au modele

Maybe
- possibilité de travailler que sur une instance Azure
- [S] créer une machine
- [S] se connecter a la machine
- probleme de runner Airflow sur la machine

Given
- airflow pipeline: get data from ademe API, stores in storage and sql db
    - [S] create db on Azure: instanciate,
    - [S] create table
    - run new pipelines: get data et transform

Retour au modele
- get data from db
- transform data
    - [poss]: Great expectations
    - simplify data process
**- train model**
    - simple training class
    - [S] create databricks community account
    - track with MLflow (which one: local or databricks)
    - register model if good enough model

- DAG model training and promotion
    - add requirements to airflow docker compose
    - add MLFLOW URI to airflow docker compose

see https://mlflow.org/docs/latest/model-registry.html for concepts
- promote model logic



- THEN
    - serve with Fast API


& Interface Streamlit
- create simple interface with all the menus and dropdowns
- get prediction

Unknowns
- databrick MLflow: registry and serve
    - log on dbricks and trace a model
    - send model to registry
    - serve model
    - train another model
    - select best model
    - promote model

- FastAI:
- Great Expectations



