# animated-disco
A Flask - Docker/Postgres data ingestion api project

![image](https://github.com/3vivekb/animated-disco/assets/4524205/ba3e585c-a85e-482c-9381-c639c439934d)


## SETUP

Start postgres docker:

```docker run --name alpine-postgres -e POSTGRES_PASSWORD=password -e POSTGRES_HOST_AUTH_METHOD=password -p 5432:5432 -d postgres:14.0-alpine```

Create miniconda environment:

```conda create --name flask_postgres --file requirements.txt```

```conda activate flask_postgres```

Run data ingestion with 

```python ingestion.py```

Run Flask with

```flask --app app run```

You can run queries at:
- http://127.0.0.1:5000/api/weather
- http://127.0.0.1:5000/api/weather/stats


Here is a sample query:

```http://127.0.0.1:5000/api/weather?station=USC00257715&page_size=10&page=3```


API Spec (WIP)
http://127.0.0.1:5000/spec

## Design/Reasoning:

The database and data processing etl were deliberately separated from the api front end.  This increases code simplicity and division of responsibility.

AWS Deployment depends on how much bigger the data will get and existing infrastructure.  If you expect more and variable traffic,
deployment to Elastic Beanstalk makes the most sense.  If the data will get huge (over 10000x), you could do something like pySpark + Glue for the ETL or integrating
with your existing data orchestration stack.  You could also integrate Terraform and CI/CD, but only if the use case is justified.  

But for this current set up, with data only growing by 100x or less,  i'd probably just push the source data to s3, deploy to a small ec2, set up a cron job for the ETL, have the postgres/docker be changed to RDS, 
and modify the pandas etl to handle the situation in memory if necessary.  Then add gunicorn and nginx. 
Perhaps properly use docker-compose. There are lots of [guides](https://testdriven.io/blog/deploying-django-to-ec2-with-docker-and-gitlab/) for this stack!
Simplicity is usually better, it creates less overhead and less code complexity.

## Look/Feel

Seeing between 20-50 seconds for ingestion and processing:
![image](https://github.com/3vivekb/animated-disco/assets/4524205/bafdad8f-ce5f-4702-b558-39b6e7c44721)

<img width="679" alt="image" src="https://github.com/3vivekb/animated-disco/assets/4524205/62813a20-e949-4217-9440-2a679a95c0cc">






