services:
  app:
    restart: 'always'
    hostname: {{ app.app_name }}-app
    environment:
      instance_tag: 'in-docker'
      django_db_hostname: {{ app.app_name }}-db
      django_csrf_trusted_origins: '["http://127.0.0.1", "http://localhost", "http://0.0.0.0"]'
      django_allowed_hosts: '["127.0.0.1", "localhost", "0.0.0.0"]'
      is_django_server_in_dev_mode: 'True'
      is_django_server_in_debug_mode: 'True'
    build:
      context: .
      dockerfile: Dockerfile
    volumes:
      - ./src:/etc/service/src
      - ./artefacts:/etc/service/artefacts
      - postgres_data:/var/lib/postgresql/data

  db:
    restart: 'always'
    hostname: {{ app.app_name }}-db
    image: postgres:{{ app.docker_db_version }}
    environment:
      POSTGRES_USER: pgdb_superuser
      POSTGRES_PASSWORD: test_password
      POSTGRES_DB: django_db
    volumes:
      - postgres_data:/var/lib/postgresql/data

  nginx:
    restart: 'always'
    hostname: {{ app.app_name }}-nginx
    build:
      context: ./nginx
    volumes:
      - ./artefacts:/artefacts

  swagger:
    restart: 'always'
    hostname: {{ app.app_name }}-swagger
    build:
      context: ./swagger

volumes:
  postgres_data:
