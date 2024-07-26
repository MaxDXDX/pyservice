"""Configurations for app and microservices."""

from pydantic_extra_types.timezone_name import TimeZoneName

from pyservice.domain.base import BaseSettings


class AppConfig(BaseSettings):
    """Configuration for arbitrary python app."""

    tz: TimeZoneName = 'Europe/Moscow'
    delete_logs_on_start: bool = True


class MicroserviceConfig(AppConfig):
    """Configuration for microservice in cluster with RabbitMQ and Celery."""

    instance_tag: str = '01'
    time_to_wait_celery_test_file: int = 10

    rabbitmq_hostname: str = 'mb.cebb.pro'
    rabbitmq_port: str = '50001'
    rabbitmq_vhost: str = 'vhost'
    rabbitmq_username: str = 'admin'
    rabbitmq_password: str = 'rabbit-initial-password'
    default_celery_queue: str = 'cluster'
    tgs_server_url: str = '10.0.80.2:50051'


default_app_config = AppConfig()
default_microservice_config = MicroserviceConfig()
