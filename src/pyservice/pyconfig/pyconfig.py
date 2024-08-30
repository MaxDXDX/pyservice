"""Configurations for app and microservices."""

from pydantic_extra_types.timezone_name import TimeZoneName

from pyservice.domain.base import BaseSettings


class AppConfig(BaseSettings):
    """Configuration for arbitrary python app."""

    tz: TimeZoneName = 'Europe/Moscow'
    delete_logs_on_start: bool = True

    app_human_name: str = 'Приложение на Python'


class MicroserviceConfig(AppConfig):
    """Configuration for microservice in cluster with RabbitMQ and Celery."""

    instance_tag: str = '01'
    instance_human_name: str = 'Микросервис на Python'

    time_to_wait_celery_test_file: int = 30

    rabbitmq_hostname: str = 'mb.cebb.pro'
    rabbitmq_port: str = '50001'
    rabbitmq_vhost: str = 'vhost'
    rabbitmq_username: str = 'admin'
    rabbitmq_password: str = 'rabbit-initial-password'
    default_celery_queue: str = 'cluster'
    tgs_server_url: str = '10.0.80.2:50051'


class BackuperConfig(MicroserviceConfig):
    """Configuration for backuper microservice."""

    app_human_name: str = 'Бэкапер'
    main_service_name: str = 'Service with important data'
    main_service_human_name: str = 'Сервис с важными данными'
    dt_tag_format: str = '%y_%m_%d__%H_%M_%S'
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


default_app_config = AppConfig()
default_microservice_config = MicroserviceConfig()
default_backuper_config = BackuperConfig()
