#!/bin/bash

cd /home/alexisperrier/airflow
docker-compose up -d

cd /home/alexisperrier/ademe_mlops/
uvicorn api.main:app --host 0.0.0.0 &

