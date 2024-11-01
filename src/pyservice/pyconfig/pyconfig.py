"""Configurations for app and microservices."""

from pydantic_extra_types.timezone_name import TimeZoneName
from pydantic import HttpUrl

from pyservice.domain.base import BaseSettings


class AppConfig(BaseSettings):
    """Configuration for arbitrary python app."""

    tz: TimeZoneName = 'Europe/Moscow'
    delete_logs_on_start: bool = True

    app_human_name: str = 'Приложение на Python'

    # put here any loggers from other modules to create default handlers
    tracked_loggers: list[str] = []


class MicroserviceConfig(AppConfig):
    """Configuration for microservice in cluster with RabbitMQ and Celery."""

    instance_tag: str = '01'
    instance_human_name: str = 'Микросервис на Python'

    time_to_wait_celery_test_file: int = 60

    rabbitmq_hostname: str = 'mb.cebb.pro'
    rabbitmq_port: str = '50001'
    rabbitmq_vhost: str = 'vhost'
    rabbitmq_username: str = 'admin'
    rabbitmq_password: str = 'rabbit-initial-password'
    default_celery_queue: str = 'cluster'
    tgs_server_url: str = '10.0.80.2:50051'
    tg_group_for_system_notifications: str = '-4101022781'
    tg_group_for_tests: str = '-4138637604'
    tg_account_for_sending_notifications: str = '+88804692592'


class BackuperConfig(MicroserviceConfig):
    """Configuration for backuper microservice."""

    app_human_name: str = 'Бэкапер'
    main_service_name: str = 'Service with important data'
    main_service_human_name: str = 'Сервис с важными данными'
    dt_tag_format: str = '%y%m%d-%H%M%S%z'
    directory_name_with_data_to_backup: str = 'data_to_backup'
    directory_name_for_local_store_backups: str = 'backups'
    number_of_stored_backups_on_local: int = 2
    archive_extension: str = 'tar.gz'
    gpg_keys_params: dict = {
        'key_type': 'RSA',
        'key_length': 1024,
        'name_real': 'Phoenix Backuper',
        'name_email': 'phoenix@backuper.tech',
        'Passphrase': 'phoenix-backuper',
    }
    yandex_drive_folder_for_backups: str = '/phoenix-backups'

    everyday_backup_hour: str = '00'
    everyday_backup_min: str = '00'

    tg_account_for_notifications: str = '+88804692592'
    tg_group_for_notifications: str = '-4138637604'


class DjangoBasedMicroserviceConfig(MicroserviceConfig):
    """Configuration for microservice powered by Django."""

    is_django_server_in_dev_mode: bool = True
    is_django_server_in_debug_mode: bool = True

    # pylint: disable=C0301
    django_secret_key: str = 'django-insecure-96^_wtuv1c_rgzbo=7cxvj@4cw0$faxitl@a(e1pd@#)ueob6k'

    django_static_files_prefix: str = 'static'

    django_csrf_trusted_origins: list[str] = [
        'https://127.0.0.1',
        'http://localhost',
        'http://0.0.0.0'
    ]

    django_cors_allowed_origins: list[str] = [
        'https://127.0.0.1:5173',
        'http://localhost:5173',
    ]

    django_allowed_hosts: list[str] = [
        '127.0.0.1',
        'localhost',
        '0.0.0.0',
        'testserver',
    ]

    django_db_name: str = 'django_db'
    django_db_user: str = 'pgdb_superuser'
    django_db_password: str = 'test_password'
    django_db_hostname: str = 'localhost'
    django_db_port: str = '5432'

    super_users: list[tuple[str, str, str]] = [
        ('admin-1', 'nimda-1', 'admin-1@admin.net'),
        ('admin-2', 'nimda-2', 'admin-2@admin.net'),
    ]

    is_keycloak_auth_enabled: bool = True
    keycloak_url: HttpUrl = 'http://keycloak:8080/auth'


default_app_config = AppConfig()
default_microservice_config = MicroserviceConfig()
default_backuper_config = BackuperConfig()
default_django_based_microservice_config = DjangoBasedMicroserviceConfig()

