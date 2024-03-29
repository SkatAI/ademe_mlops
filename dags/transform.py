"""
### Tutorial Documentation
Documentation that goes along with the Airflow tutorial located
[here](https://airflow.apache.org/tutorial.html)
"""

from __future__ import annotations
import os
from functools import partial
from datetime import datetime, timedelta
import logging
import typing as t
import pandas as pd
from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from db_utils import Database
import numpy as np


# Function to call the class method dynamically
def execute_class_method(class_instance, method_name, ti=None):
    print(f"-- in execute_class_method: {method_name}")
    method = getattr(class_instance, method_name)
    return method()
    # if ti:
    #     # Assuming previous task's return values are used as method arguments
    #     data = ti.xcom_pull(task_ids=f"{method_name}_task")
    #     method = getattr(class_instance, method_name)
    #     return method(data)
    # else:
    #     method = getattr(class_instance, method_name)
    #     return method()


class DataProcessor:
    def __init__(self):
        logger.info("=== DataProcessor init")
        self.data = np.array([1, 2, 3])
        self.db = Database()

        self.query = "select count(*) from dpe_tertiaire;"
        cur = self.db.connection.cursor()
        cur.execute(self.query)
        n = cur.fetchone()
        logger.info(f"=== n ===:", n)

    def load_data(self):
        # Your code to load data
        logger.info(f"=== self Data loaded: {self.data}")
        cur = self.db.connection.cursor()
        cur.execute(self.query)
        n = cur.fetchone()
        logger.info(f"=== n ===: {n}")

        # return ['a','b','c']

    def transform_data(self):
        # Your code to transform data
        self.data += 1
        logger.info(f"=== self Data transformed: {self.data}")
        cur = self.db.connection.cursor()
        cur.execute(self.query)
        n = cur.fetchone()
        print(f"=== n ===: {n}")
        # return f"transformed {data}"

    def save_data(self):
        # Your code to save data
        logger.info(f"=== self Data saved: {self.data}")
        self.data += 2
        cur = self.db.connection.cursor()
        cur.execute(self.query)
        n = cur.fetchone()
        print(f"=== n ===: {n}")

        print(f"---- active connections {self.db.engine.pool.status()}")
        self.db.close()
        print(f"---- active connections after db.close {self.db.engine.pool.status()}")
        cur = self.db.connection.cursor()
        cur.execute(self.query)
        n = cur.fetchone()
        print(f"TAKE 2=== n ===: {n}")


logger = logging.getLogger(__name__)

# ---------------------------------------------
# instanciate class
# ---------------------------------------------
data_processor = DataProcessor()

# ---------------------------------------------
#  DAG
# ---------------------------------------------
with DAG(
    "ademe_transform_data",
    default_args={
        "depends_on_past": False,
        "email": ["alexis.perrier@gmail.com"],
        "email_on_failure": True,
        "email_on_retry": False,
        "retries": 0,
        "retry_delay": timedelta(minutes=10),
    },
    description="Get raw data from dpe-tertiaire, transform and store into training_data",
    schedule=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ademe"],
) as dag:
    # partials
    load_data_callable = partial(execute_class_method, data_processor, "load_data")
    transform_data_callable = partial(execute_class_method, data_processor, "transform_data")
    save_data_callable = partial(execute_class_method, data_processor, "save_data")

    load_data_task = PythonOperator(task_id="load_data_task", python_callable=load_data_callable)

    transform_data_task = PythonOperator(
        task_id="transform_data_task", python_callable=transform_data_callable, provide_context=True
    )

    save_data_task = PythonOperator(
        task_id="save_data_task", python_callable=save_data_callable, provide_context=True
    )

    load_data_task >> transform_data_task >> save_data_task
