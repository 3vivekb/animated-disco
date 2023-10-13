# animated-disco
A Flask - Docker/Postgres data ingestion api project

Start postgres docker:

```docker run --name itsa-postgres -e POSTGRES_PASSWORD=password -e POSTGRES_HOST_AUTH_METHOD=password -p 5432:5432 -d postgres:14.0-alpine```

Run the following commands to create the initial db 

```docker exec -it itsa-postgres bash```

```su postgres```

```psql -c 'create database wxdata;'```

Create conda environment (or venv as you desire)

```conda create --name flask_postgres --file requirements.txt -c conda-forge flask-smorest```

```conda activate flask_postgres```

Run data ingestion with 

```python ingestion.py```