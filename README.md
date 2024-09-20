# Airflow load csv to postgresql

### Create User for Airflow
```
docker-compose run airflow-webserver airflow users create --role Admin --username airflow --email airflow@example.com --firstname airflow --lastname airflow --password airflow
```
