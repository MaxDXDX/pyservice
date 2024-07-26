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

WORKDIR ${SERVICE_DIR}

ENV INSTANCE_TAG='first-instance'

## service specific:
# additional os packages:
# RUN apt-get install gpg --yes

ENV ROUND_TO='3'

WORKDIR ${SERVICE_DIR}/src/calculator/cli
ENTRYPOINT ["/bin/bash", "start.sh"]
