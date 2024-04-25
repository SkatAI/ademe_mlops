#!/bin/bash


cd /home/alexisperrier/airflow
docker-compose up -d

cd /home/alexisperrier/ademe_mlops/api
uvicorn main:app --host 0.0.0.0 &

