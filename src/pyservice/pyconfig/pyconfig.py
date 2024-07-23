"""Configurations for app and microservices."""

from pathlib import Path

from pydantic_extra_types.timezone_name import TimeZoneName
from pyservice.files.files import create_if_not_yet
from pyservice.files import files

from pyservice.ddd.model import BaseSettings

class AppConfig(BaseSettings):
    """Configuration for arbitrary python app."""

    _origin_file: Path

    tz: TimeZoneName = 'Europe/Moscow'

    def __init__(self, origin_file: str | Path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._origin_file = Path(origin_file)

    @property
    def directory_for_place_app_directory(self):
        # pylint: disable=W0612
        parent_for_app_dir, app_dir, app_root_module = (
            self.base_project_directories)
        return parent_for_app_dir

    @property
    def directory_for_app(self) -> Path:
        # pylint: disable=W0612
        parent_for_app_dir, app_dir, app_root_module = (
            self.base_project_directories)
        return app_dir

    @property
    def root_module(self) -> Path | None:
        # pylint: disable=W0612
        parent_for_app_dir, app_dir, app_root_module = (
            self.base_project_directories)
        return app_root_module

    @property
    def app_ref(self) -> str:
        return self.root_module.name if self.root_module else 'unknown'

    @property
    def base_project_directories(self) -> tuple[Path, Path, Path]:
        """Detect:
        - the parent for app directory
        - app directory
        - root module of app (the first after <src> directory)
        """
        root_module = None

        config_location = self._origin_file
        current_dir = config_location.parent
        previous_dir = None
        while True:
            if current_dir.name == 'src':
                root_module = previous_dir
            dirs = files.get_list_of_directories_in_directory(
                current_dir, mask='*')
            for directory in dirs:
                if directory.name in ['src', 'tests', 'test']:
                    app_dir = directory.parent
                    parent_for_app_dir = app_dir.parent
                    return parent_for_app_dir, app_dir, root_module
                elif directory.name == '/':
                    raise ValueError(
                        'Can not detect project dir and its parent!')
            previous_dir = current_dir
            current_dir = current_dir.parent

    @property
    @create_if_not_yet
    def artefacts_directory(self) -> Path:
        return self.directory_for_app / 'artefacts'

    @property
    @create_if_not_yet
    def directory_for_tmp(self) -> Path:
        return self.artefacts_directory / 'tmp'

    @property
    @create_if_not_yet
    def directory_for_logs(self) -> Path:
        return self.artefacts_directory / 'logs'

    @property
    @create_if_not_yet
    def directory_for_data(self) -> Path:
        return self.artefacts_directory / 'data'


class MicroserviceConfig(AppConfig):
    """Configuration for microservice in cluster with RabbitMQ and Celery."""

    instance_tag: str = '#01'
    time_to_wait_celery_test_file: int = 5

    rabbitmq_hostname: str = 'mb.cebb.pro'
    rabbitmq_port: str = '50001'
    rabbitmq_vhost: str = 'vhost'
    rabbitmq_username: str = 'admin'
    rabbitmq_password: str = 'rabbit-initial-password'
    default_celery_queue: str = 'cluster'


default_app_config = AppConfig(__file__)
default_microservice_config = MicroserviceConfig(__file__)
