#!/bin/bash

cd /home/alexisperrier/airflow
docker-compose down
docker-compose up -d

cd /home/alexisperrier/ademe_mlops/
python3 -m pip install --user virtualenv
python3 -m virtualenv venv
source venv/bin/activate
pip3 install -r requirements.txt
git pull origin master

uvicorn api.main:app --host 0.0.0.0 &

