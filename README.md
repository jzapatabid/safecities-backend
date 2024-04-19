# safecities-backend

## Getting started

### Run webserver

#### Run locally

```console
cp .env.example .env
# edit env variables
source .env
pip install -r requirements
flask db migrate # optional
flask db upgrade
flask run
 ```

#### Run inside container

```console
docker build -t safecities-backend:latest . -f Dockerfile-Dev
cp .env.example .env
# edit env variables
docker network create safecities-network
docker run --name safecities-backend --network safecities-network --env-file=.env -d -p 5000:5000 safecities-backend:latest

docker exec -it safecities-backend flask db migrate
docker exec -it safecities-backend flask db upgrade
docker exec -it safecities-backend flask create_admin_user
```

### Run celery

#### Run locally

```console
celery -A wsgi.celery_app worker --loglevel INFO
```

#### Run inside container

```console
docker build -t safecities-celery:latest -f Dockerfile-Celery .
docker stop safecities-celery || docker rm safecities-celery
docker run -d --name rabbitmq --network safecities-network --hostname rabbitmq rabbitmq:3.11
docker run --name safecities-celery --network safecities-network --env-file=.env -d safecities-celery:latest 
```