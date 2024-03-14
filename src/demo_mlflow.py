import mlflow

# set to your server URI
remote_server_uri = "http://localhost:8088"
mlflow.set_tracking_uri(remote_server_uri)

# set experiment
mlflow.set_experiment("experiment_02")

with mlflow.start_run():
    mlflow.log_param("a", 1)
    mlflow.log_metric("b", 2)
