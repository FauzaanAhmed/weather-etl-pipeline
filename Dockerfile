FROM apache/airflow:2.8.1-python3.11

COPY requirements.txt /opt/airflow/requirements.txt

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow
RUN pip install --no-cache-dir -r /opt/airflow/requirements.txt
