# import json
# import pathlib
# import airflow
# import requests
# import requests.exceptions as requests_exceptions
# from airflow import DAG
# from airflow.operators.bash import BashOperator
# from airflow.operators.python import PythonOperator

# import glob

# import pandas as pd
# import os

# class AdemeData(object):

#     FILE_FOLDER = "./data/ademe/"
#     def __init__(self) -> None:
#         self.base_url = "https://data.ademe.fr/data-fair/api/v1/datasets/dpe-v2-tertiaire-2/lines"
#         # self.sort = "sort=Date_visite_diagnostiqueur"
#         self.sort = "sort=N%C2%B0DPE"
#         self.format = "format=json"

#     def set_output_file(self):
#         self.output_file = "sample.json"
#         self.output_path = os.path.join(AdemeData.FILE_FOLDER, self.output_file)

#     def next_url(self):
#         # either load it or use default
#         self.url = f"{self.base_url}?{self.sort}&{self.format}"

#     def bash_command(self):
#         self.bash_command = f"curl --request GET -o ./data/ademe/{self.output_file} --url '{self.url}'"


# def parse_output(output_file: str):
#     df = pd.read_json(output_file)
#     next_url = df.loc[0].next
#     # save url somewhere
#     data = df['results']
#     # save data somewhere

# def _parse_data():
#     pass

# def _store_data():
#     pass


# dag = DAG(
#     dag_id="get_ADEME_data",
#     start_date=airflow.utils.dates.days_ago(1),
#     schedule_interval=None,
# )



# get_data = BashOperator(
#     task_id="download_data",
#     bash_command=f"curl --request GET -o ./data/ademe/{local_file} --url '{url}'",
#     dag=dag
# )

# parse_data = PythonOperator(
#     task_id="parse_data",
#     python_callable=_parse_data,
#     dag=dag,
# )

# store_data = PythonOperator(
#     task_id="store_data",
#     python_callable=_store_data,
#     dag=dag,
# )

# #  set dependencies between tasks.
# get_data >> parse_data >> store_data
