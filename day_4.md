# day 4.1

voir https://docs.google.com/document/d/1G1Fyeb3qXDBaKz-dXn5e1Qa0ygrnSMTOopwSIdB6KvE/edit

##  airflow + MLflow sur instance Azure
- creer une instance
- connection ssh
- installer ce qui est necessaire: pip, docker, docker compose
- ouvrir la connection

--> creer une instance avec script de depart
--> creer une instance avec terraform

## airflow
- installer Airflow
- lancer airflow

## connecter votre compte github
- installer git
- downloader le code airflow

(## merger les 2 codes bases : airflow et ademe)

## nouvelle config airflow avec MLflow inside

- lancer airflow
acceder a airflow sur <IP>: 8080
acceder a MLflow sur <IP>: 5001

# deploy when pushing

On the VM create ssh key  with
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

no password

add ~/.ssh/id_rsa.pub to github SSH keys from your profile


sur la VM, verifier que vous pouvez pull from github

mkdir ademe_mlops
cd ademe_mlops
git init
git remote add origin git@github.com:SkatAI/ademe_mlops.git
git pull origin master

mainteant pour ajouter la cle pour le deploiement

add ~/.ssh/id_rsa to secrets on the repo

modifier le code
commit, push
verifier que le code est mis a jour sur la VM

maintenant, ne deployer le code que si le build passe

ajouter la ligne needs

deploy:
    needs: build  # This ensures deploy only runs if build is successful
    runs-on: ubuntu-latest



