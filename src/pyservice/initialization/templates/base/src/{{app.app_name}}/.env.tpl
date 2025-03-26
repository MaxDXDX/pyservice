# your local settings (ignored by git, it's only for your local development)
# IMPORTANT: environment variables will always take priority over this file

INSTANCE_TAG='local-development'  # example

## database
DJANGO_DB_HOSTNAME='localhost'
DJANGO_DB_PORT='{{ app.docker_db_port }}'

## used RabbitMQ
RABBITMQ_HOSTNAME='localhost'
RABBITMQ_PORT='{{ app.docker_rabbit_port }}'
RABBITMQ_USERNAME='rabbit-admin'
RABBITMQ_PASSWORD='rabbit-password'
RABBITMQ_VHOST='cluster-vhost'

## used SEQ
SEQ_URL='http://localhost:{{ app.docker_seq_port }}'
SEQ_API_KEY='nimda'

KEYCLOAK_URL='https://auth.cebb.pro/auth'
KEYCLOAK_REALM='phoenix-production-1'
KEYCLOAK_CLIENT_ID='default-protected-client'
KEYCLOAK_SECRET_KEY='gLhLyIM16Vt4mZ7Gbbk3haP3tQnZE0xO'

DJANGO_CORS_ALLOWED_ORIGINS='["https://editor-next.swagger.io", "http://localhost:{{ app.docker_swagger_port }}"]'
