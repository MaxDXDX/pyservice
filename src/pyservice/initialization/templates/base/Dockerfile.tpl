FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install git --yes

ENV SERVICE_DIR='/etc/service'
COPY src ${SERVICE_DIR}/src
COPY tests ${SERVICE_DIR}/tests
COPY pyproject.toml ${SERVICE_DIR}/
COPY setup.py ${SERVICE_DIR}/
RUN pip install -e ${SERVICE_DIR}/

WORKDIR ${SERVICE_DIR}/src/{{ app.app_name }}/cli

ENV django_db_port='5432'

ENTRYPOINT ["/bin/bash", "start.sh"]
