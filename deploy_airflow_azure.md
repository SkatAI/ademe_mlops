Deploying Apache Airflow on Azure Container Instances (ACI) involves several steps, including preparing a Docker container for Airflow, pushing it to Azure Container Registry (ACR), and then deploying this container on ACI. This method provides a quick and straightforward way to get Airflow up and running in the cloud without managing virtual machines directly. Here's a step-by-step guide:

### 1. Prepare your environment

Ensure you have an Azure subscription and the Azure CLI installed on your local machine. Log in to your Azure account via the Azure CLI using `az login`.

### 2. Create an Azure Container Registry (ACR)

First, create a resource group if you don’t already have one:

```bash
az group create --name myResourceGroup --location eastus
```

#### Note
existing az resource group
```bash
az group list
```

```json
{
    "id": "/subscriptions/1b72e9bf-c028-4dbd-83d2-8d289e022716/resourceGroups/ademe-mlops",
    "location": "francecentral",
    "managedBy": null,
    "name": "ademe-mlops",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null,
    "type": "Microsoft.Resources/resourceGroups"
  }
```

=> use this one

Then, create an Azure Container Registry:

```bash
az acr create --resource-group ademe-mlops --name ademeairflowregistry --sku Basic
```



### 3. Prepare the Airflow Docker image

You can use the official Apache Airflow Docker image or customize one according to your needs. To customize, create a `Dockerfile` that starts with the official image and adds your DAGs, plugins, or any dependencies:

```Dockerfile
FROM apache/airflow:2.1.0
COPY ./dags /opt/airflow/dags
# Add additional steps as needed
```

Build your Docker image:

```bash
docker build -t myairflowimage .
```

### 4. Push the Docker image to ACR

First, log in to your ACR:

```bash
az acr login --name myAirflowRegistry
```

Tag your Docker image with the ACR login server name:

```bash
docker tag myairflowimage myAirflowRegistry.azurecr.io/myairflowimage:v1
```

Push the image to your ACR:

```bash
docker push myAirflowRegistry.azurecr.io/myairflowimage:v1
```

### 5. Deploy Airflow to Azure Container Instances

Create a container instance using the image from ACR. Make sure to replace placeholders with your actual resource group, ACR name, and image name:

```bash
az container create \
    --resource-group myResourceGroup \
    --name myAirflowInstance \
    --image myAirflowRegistry.azurecr.io/myairflowimage:v1 \
    --cpu 2 --memory 4 \
    --registry-login-server myAirflowRegistry.azurecr.io \
    --registry-username <ACR_USERNAME> \
    --registry-password <ACR_PASSWORD> \
    --dns-name-label my-airflow-instance \
    --ports 8080
```

Note: Obtain `<ACR_USERNAME>` and `<ACR_PASSWORD>` by running `az acr credential show --name myAirflowRegistry`.

### 6. Access Airflow

Once deployed, you can access the Airflow web interface. Retrieve the FQDN (Fully Qualified Domain Name) of your ACI instance:

```bash
az container show --resource-group myResourceGroup --name myAirflowInstance --query ipAddress.fqdn
```

Open a web browser and navigate to `http://<FQDN>:8080` to access the Airflow UI.

### Conclusion

You've deployed Apache Airflow on Azure using Container Instances. This setup is suitable for testing, development, or small workloads. For production environments, consider more robust solutions like Azure Kubernetes Service (AKS) for scalability and resilience.