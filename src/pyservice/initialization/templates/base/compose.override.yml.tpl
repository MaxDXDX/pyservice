# override docker services by your local environment
# git ignores this file - it's only for you

services:
  app:
    restart: 'always'
    environment:
      RABBITMQ_HOSTNAME: {{ app.app_name }}-rabbit
      RABBITMQ_PORT: '5672'
      SEQ_URL: 'http://{{ app.app_name }}-seq'
    volumes:
      - ./src:/etc/service/src
      - ./tests:/etc/service/tests
      - ./artefacts:/etc/service/artefacts

#  db:

#  nginx:

  # local rabbit (comment if you use an external one)
  rabbit:
    restart: 'no'
    hostname: {{ app.app_name }}-rabbit
    image: rabbitmq:3.13.3-management
    ports:
      - {{ app.docker_rabbit_port }}:15672
    environment:
      RABBITMQ_DEFAULT_USER: 'rabbit-admin'
      RABBITMQ_DEFAULT_PASS: 'rabbit-password'
      RABBITMQ_DEFAULT_VHOST: 'cluster-vhost'

  # local SEQ (comment if you use an external one)
  seq:
    restart: 'no'
    hostname: {{ app.app_name }}-seq
    image: datalust/seq:2024.3
    ports:
      - {{ app.docker_seq_port }}:80
    environment:
      ACCEPT_EULA: 'Y'
      # command for generating password hash: echo '<password>' | docker run --rm -i datalust/seq config hash
      # this password: nimda
      SEQ_FIRSTRUN_ADMINPASSWORDHASH: 'QO0ZLIUxclY/IoasdCnzJLzJ7pCBodyCD6iZuIjPVjtr1WFE2rR8iP6kwcGDPls8XU0CCMnI1lsDX+3cgwt5UygfpEcgdfaSc0yPSVKbZQyx'
      SEQ_API_CANONICALURI: 'http://{{ app.app_name }}-seq'
