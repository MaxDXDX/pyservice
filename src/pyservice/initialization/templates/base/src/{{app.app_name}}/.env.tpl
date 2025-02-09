# your local settings (ignored by git, it's only for your local development)
# IMPORTANT: environment variables will always take priority over this file

INSTANCE_TAG='local-development'  # example

## used RabbitMQ
RABBITMQ_HOSTNAME='localhost'
RABBITMQ_PORT='{{ app.docker_seq_port }}'
RABBITMQ_USERNAME='rabbit-admin'
RABBITMQ_PASSWORD='rabbit-password'
RABBITMQ_VHOST='cluster-vhost'

## used SEQ
# SEQ_URL='http://localhost:{{ app.seq_local_port }}'
# SEQ_API_KEY='put here api key from seq'
