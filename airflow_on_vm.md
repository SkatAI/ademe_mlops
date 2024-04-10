Vous souhaitez utiliser airflow et MLflow pour un projet machine learning.

Mais votre machine rame, vous galerez entre les differents shell windows

Nous allons installer tout ca dans une petite instance Azure qui ne vous coutera pas grand chose.

Et si vous venez de creer cotre compte azure vous devriez avoir largement assez de crédits.

# le plan

Vous allez
- creer une instance (une VM) sur le portal azure
- vous connecter a cette instance en SSH
- setup l'instance avec le minimum (pip, git, ...)
- installer docker et airflow
- modifier le docker-compose.yml de airflow pour y ajouter MLflow

et enfin ajouter les DAGS que vous voulez executer
Vous pourrez ensuite acceder
- a airflow sur http:<instance_ip>:8080
- a MLflow sur http:<instance_ip>:5001




# prerequis

Pour suivre ce tuto, vous devez

1. avoir du crédit sur Azure
2. savoir utiliser SSH sur sa machine
    - et savoir gerer une clé .pem : localisation et changement de niveau de permission


# Variables
Les variables de l'instance sont :

- instance_name: nom que vous avez donné a l'instance
- instance_key_name: nom du fichier .pem
- instance_ip: IP de l';instance
- username: votre nom d'utilisateur sur azure

ces variables sont dispo sur la page de votre instance sur le portail azure.


# create VM: Ubuntu
Pour creer une machine virtuelle Azure

- [Créer une machine virtuelle](https://portal.azure.com/#create/Microsoft.VirtualMachine-ARM)

choisissez un nom de machine virtuelle: <instance_name>

Airflow a besoin de 2 cpu et au minimum $GiB de mémoire.

- Ubuntu Server 20.04 LTS - x64 Gen

Il faut au minimum une VM avec 2 CPU et 4Gb de memoire

- Standard B2s - 2 vcpus 4GiB memory

Choisissez la Region. Par defaut Azure vous propose une region proche de la langue de votre cmpte (France Centrale si vous travaillez en Francais par exemple). les instances aux US (East US) sont souvent moins cher.

Une autre facon de reduire les couts est d'utiliser [Azure Spot](https://learn.microsoft.com/fr-ca/azure/virtual-machines/spot-vms). Si vous cochez "Exécuter avec la remise Azure Spot", votre VM utilise les ressources inutilisées de Azure mais peut etre arreté a tout moment. par contre le cout de l'instance est fortement reduit.

Vous aezv le choix de vous connecter a votre instance avec un mot  de passe ou avec une clé. Utiliser la clé est plus securisez. Mais si vous rencontrez des problemes pour vous connecter en SSH avec la cle, alors choisissez l'option mot de passe.


Téléchargez la ssh key (<instance_key_name>.pem) sur votre machine locale dans le folder ~/.ssh

Et réduisez le niveau d'acces au fichier pem:

> chmod 600  ~/.ssh/<nom de l'instance>.pem


Connectez vous à la VM en SSH

➜  ~ ssh -i ~/.ssh/<instance_name>.pem <user_name>@<instance_ip>



# setup de l'instance

une fois connecté, il vous faut au minimum installer pip

```shell
sudo apt update
sudo apt install python3-pip
```

puis installer airflow

```shell
export AIRFLOW_HOME=~/airflow
mkdir airflow
cd airflow/
mkdir -p ./dags ./logs ./plugins ./config
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.8.3/docker-compose.yaml'
```

et installer docker
```shell
sudo apt -y install docker.io ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo   "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
   $(. /etc/os-release && echo "$VERSION_CODENAME") stable" |   sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo groupadd docker
sudo usermod -aG docker ${USER}
```

enfin installer docker compose

```shell
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker compose --version
```

A ce stade vous devez rafraichir la session en tant que super user

```shell
su -s ${USER}
```

Ou si vous n'avez pas de mot de passe super user:

- exit
puis
- vous reconnectez en ssh

Verifier alors que docker est bien installé

```shell
docker run hello-world
```

# Le setup de Airflow

Dans un autre terminal local vous allez copier les fichiers docker sur l'instance

Il y en a trois

- le Dockerfile pour airflow qui ne fait qu'installer les librairies python utilisées dans vos DAG. Par exemple si vous souhaitez utiliser scikit-learn pour entrainer vos modeles, le Docfile.airflow est

```shell
FROM apache/airflow:2.8.3
RUN pip install mlflow scikit-learn
```

Nous allons installer MLflow en tant que service dans airflow en buildant MLflow a partir du Dockerfile.mlflow

```
FROM python:3.9.18-slim

# Set the working directory
WORKDIR /mlflow

# Install MLflow
RUN pip install mlflow

# Expose the port the app runs on
EXPOSE 5000

# Command to run the MLflow server
CMD mlflow ui --host 0.0.0.0
```

et enfin nous allons modifier le fichier docker-compose.yml pour


Le fichier complet est disponible dans ce [gist](https://gist.github.com/alexisperrier/e9270d4da88e4ee7accf491bd51ab791)

Il y a 3 changements

1. build airflow a partir du Dockerfile.airflow

```yml
    # Airflow est contruit a partir du Dockerfile.airflow et non plus a partir de l'image officielle
    # image: ${AIRFLOW_IMAGE_NAME:-apache/airflow:2.8.3}
    build:
    context: .
    dockerfile: Dockerfile.airflow

```

2. ajouter le service MLflow

```yml
  # ajouter MLflow service
  mlflow:
    build:
      context: .
      dockerfile: Dockerfile.mlflow  # Ensure this matches the name/location of your Dockerfile
    ports:
      - "5001:5000"                                   # Exposing MLflow's default port
```

3. enfin modifier la fin du fichier
```yml
volumes:
  postgres-db-volume:
  mlflow-artifacts:
```

Pour copier ces 3 fichiers sur la VM, utilisez ```scp```

```shell
scp -i ~/.ssh/<instance_key_name>.pem ./Dockerfile.airflow  <username>@<instance_ip>:~/airflow
scp -i ~/.ssh/<instance_key_name>.pem ./Dockerfile.mlflow  <username>@<instance_ip>:~/airflow
scp -i ~/.ssh/<instance_key_name>.pem ./docker-compose.yaml  <username>@<instance_ip>:~/airflow
```

Verifier que les 3 fichiers sont bien dans ~/airflow

Maintenant vous allez *build airflow*

Creer la variable d'environnement AIRFLOW_UID
```shell
echo -e "AIRFLOW_UID=$(id -u)" > .env
```

Initialiser airflow
```shell
docker compose up airflow-init
```

Enfin lancer Airflow
```shell
docker compose up
```

Cette derniere etape prends quelques minutes.
A la fin vous devriez avoir 7 running docker container

```docker ps``` retourne ces 2 premieres colonnes

```shell
CONTAINER ID   IMAGE
dee8a900b124   airflow_airflow-webserver
538c1059db2b   airflow_airflow-scheduler
5462ea356cce   airflow_airflow-worker
5fb40a4d2478   airflow_airflow-triggerer
1d146341b0b7   airflow_mlflow
8c9868efad03   postgres:13
46aa70d6027b   redis:latest
```


En cas de probleme, vous pouvez regarder les logs des containers avec ```docker logs <CONTAINER_ID>``` ou inspecter le container ```docker inspect <CONTAINER_ID>```

Puis pour deactiver le service airflow et aservice associés


```shell
docker compose down
```

Si necessaire supprimer les container docker

```shell
docker ps -a
```

```shell
docker container rm <CONTAINER ID>
```

Et pour les images

```shell
docker image ls
```

et pour  detruire les images:

```shell
docker image rm <IMAGE ID>
```

Enfin pour redemarrer le tout une fois que vous pensez avoir fixé le probleme, en fonction de

```shell
docker compose up airflow-init
```
ou / et
```shell
docker compose up build
docker compose up
```

# Ca marche !

A ce stade accedez au server Airflow sur

[http:<instance_ip>:8080](http:<instance_ip>:8080)

et au server MLflow sur

[http:<instance_ip>:5001](http:<instance_ip>:5001)


on va ensuite installer les DAGS que vous souhaitez executer.

Le plus simple est de copier vos fichier DAGS de votre local au repertoire ~/airflow/dags sur la VM avec scp.

Mais ca ne scale pas. Il vaut mieux ajouter votre repo github ou gitlab qui contient tous vos scripts sur la VM et a chaque modification de vos scripts, passer par la repo git pour mettre a jour le code.

Par soucis de simplification, nous allons simplement copier les DAGS locaux sur la VM avec scp

```shell
scp -i ~/.ssh/<instance_key_name>.pem <path to local DAGS>/*.py  <username>@<instance_ip>:~/airflow/dags
```
de meme pour les data
```shell
scp -i ~/.ssh/<instance_key_name>.pem <path to local data folder>/*.*  <username>@<instance_ip>:~/airflow/data
```

Dans le cadre du projet [Ademe MLops](https://github.com/SkatAI/ademe_mlops), il faut creer aussi les sous folder ~/airflow/data/api et ~/airflow/data/ademe-dpe-tertiaire

```shell
mkdir ~/airflow/data/api
mkdir ~/airflow/data/ademe-dpe-tertiaire
```

et copier au moins le fichier url.json dans ~/airflow/data/api

# sources

- https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-compose-on-ubuntu-20-04
- https://www.digitalocean.com/community/questions/how-to-fix-docker-got-permission-denied-while-trying-to-connect-to-the-docker-daemon-socket
