from functools import partial
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

class DataProcessor:
    def __init__(self):
        self.payload = "hello world"

    def load_data(self):
        print("Data loaded")
        print(self.payload)
        return "some data"

    def transform_data(self, data):
        print(f"Data transformed: {data}")
        print(self.payload)
        return f"transformed {data}"


# Function to call the class method dynamically
def execute_class_method(class_instance, method_name, ti=None):
    if ti:
        # Assuming previous task's return values are used as method arguments
        payload = ti.xcom_pull(task_ids=f"{method_name}_task")
        method = getattr(class_instance, method_name)
        return method(payload)
    else:
        method = getattr(class_instance, method_name)
        return method()

# Initialize your class
data_processor = DataProcessor()

with DAG('data_processing_dag', start_date=datetime(2021, 1, 1)) as dag:
    # Partial functions to pass to the PythonOperator
    load_data_callable = partial(execute_class_method, 'load_data', data_processor)
    transform_data_callable = partial(execute_class_method, 'transform_data', data_processor)
    save_data_callable = partial(execute_class_method, 'save_data', data_processor)

    load_data_task = PythonOperator(
        task_id='load_data_task',
        python_callable=load_data_callable
    )

    transform_data_task = PythonOperator(
        task_id='transform_data_task',
        python_callable=transform_data_callable,
        provide_context=True
    )

    save_data_task = PythonOperator(
        task_id='save_data_task',
        python_callable=save_data_callable,
        provide_context=True
    )

    load_data_task >> transform_data_task >> save_data_task
