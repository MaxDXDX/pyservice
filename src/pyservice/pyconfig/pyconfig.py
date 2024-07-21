"""
PyConfig class for building service`s config.
"""


import inspect
import json
import os
from pathlib import Path
from pytz import tzinfo, timezone
from pyservice.files import files


ENV_PREFIX_FOR_CLUSTER_LEVEL_OPTIONS = 'cluster'


def create_if_not_yet(func):
    def wrapper(*args):
        path: Path = func(*args)
        path.mkdir(exist_ok=True, parents=True)
        return path
    return wrapper


class ConfigMeta:
    secret_options = []
    config_location: Path = None
    # project_directory: Path = None

    # auto_creating_directories: bool = False


class PyConfig:
    """Config class."""

    meta: ConfigMeta

    service_ref: str = ''
    env_var_prefix: str = ''

    tz = timezone('Europe/Moscow')

    parent_for_service_directory: Path = None
    directory_for_tmp: Path
    directory_for_logs: Path
    directory_for_data: Path

    # def update_service_directory_and_its_parent(self) -> Path | None:

    def create_text_file_in_tmp_directory(
            self, content: str = None, filename: str = None) -> Path:
        return files.create_text_file_in_directory(
            self.directory_for_tmp, content, filename
        )

    def erase_tmp_directory(self):
        files.erase_directory(self.directory_for_tmp)

    @property
    def project_directory(self) -> Path:
        # pylint: disable=W0612
        parent_of_project_dir, project_dir = self.base_project_directories
        return project_dir

    @property
    def base_project_directories(self) -> tuple[Path, Path]:
        """The parent for project directory and project directory."""
        config_location = self.meta.config_location
        if not config_location:
            raise ValueError('Can not detect config location!')
        potential_dir = config_location.parent
        while True:
            dirs = files.get_list_of_directories_in_directory(
                potential_dir, mask='*')
            for directory in dirs:
                if directory.name == 'src':
                    project_dir = directory.parent
                    new_parent_of_service_dir = project_dir.parent
                    current_parent = self.parent_for_service_directory
                    if current_parent and len(str(current_parent)) > 0:
                        assert current_parent == new_parent_of_service_dir
                    else:
                        self.parent_for_service_directory = (
                            new_parent_of_service_dir)
                    return new_parent_of_service_dir, project_dir
                elif directory.name == '/':
                    raise ValueError(
                        'Can not detect project dir and its parent!')
            potential_dir = potential_dir.parent

    @property
    @create_if_not_yet
    def artefacts_directory(self) -> Path:
        return self.project_directory / 'artefacts'

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

    # def disable_auto_creating_directories(self):
    #     self.meta.auto_creating_directories = False
    #
    # def enable_auto_creating_directories(self):
    #     self.meta.auto_creating_directories = True

    def __init__(self, config_file: Path = None):
        self.meta = ConfigMeta()
        if config_file:
            self.meta.config_location = Path(config_file)
            # self.update_parent_for_service_directory()
        if not self.env_var_prefix:
            self.env_var_prefix = self.service_ref
        self._validate()
        self.override_from_environment()

    def _validate(self):
        try:
            assert isinstance(self.service_ref, str)
            assert len(self.service_ref) > 0
        except (AttributeError, AssertionError) as e:
            raise ValueError(
                'You must provide <service_ref> '
                'value for your config') from e

        self._directories_should_be_created = False
        for option_name in self.all_keys:
            value = getattr(self, option_name)
            # if value is None:
            #     raise ValueError(f'config option can not be None: '
            #                      f'{option_name}')
            if isinstance(value, Path):
                if (('directory' not in option_name) and
                        ('file' not in option_name)):
                    msg = (f'Bad option "{option_name}" ({value}) - '
                           f'directory or file must contain '
                           f'<directory> or <file> word in option name')
                    raise ValueError(msg)
        self._directories_should_be_created = True

    def __repr__(self):
        rows = []
        for key in self.all_keys:
            if ('password' in key or 'token' in key
                    or key in self.meta.secret_options):
                value = getattr(self, key)
                first_letter = value[0]
                last_letter = value[-1]
                value = f'{first_letter}******************{last_letter}'
            else:
                value = getattr(self, key)
            rows.append(f'- {key}: {value}')
        return '\n'.join(rows)

    def override_from_environment(self):
        for env_var in self.keys_from_environment:
            value = os.getenv(env_var)
            key = self.restore_key_from_env_key(env_var)
            if value:
                setattr(self, key, value)

    @classmethod
    def _class_attributes(cls) -> list:
        members = inspect.getmembers_static(
            cls, lambda a: not (inspect.isroutine(a) or inspect.ismethod(a)))
        filtered = [k for (k, v) in members if cls._attribute_filter(k, v)]
        return filtered

    @staticmethod
    def _attribute_filter(attr_name: str, attr_object):
        """Functon for filter only real config options."""
        if str(attr_name).startswith('_'):
            return False
        if isinstance(attr_object, property):
            return False
        return True

    @property
    def all_keys(self) -> list[str]:
        """All names of real config options."""
        return self._class_attributes()

    def convert_key_to_env_key(self, key: str):
        prefix = self.env_var_prefix
        return f'{prefix}_{key}'.upper()

    def restore_key_from_env_key(self, env_key: str):
        lower = env_key.lower()
        without_prefix = (
            lower.replace(f'{self.env_var_prefix}_', ''))
        return without_prefix

    @property
    def keys_from_environment(self) -> list[str]:
        return [self.convert_key_to_env_key(_) for _ in self.all_keys]

    def __getattribute__(self, item):
        attr_value = super().__getattribute__(item)
        if not str(item).startswith('_') and item != 'meta':
            attr_name = item
            attr_class = type(getattr(type(self), item))
            self._on_get_config_option(attr_name, attr_class, attr_value)
        return attr_value

    # pylint: disable=W0613
    def _on_get_config_option(self, attr_name, attr_class, attr_value):
        pass
        # if isinstance(attr_value, Path):
        #     if ('directory' in attr_name and
        #             self._directories_should_be_created):
        #         attr_value.mkdir(exist_ok=True)

    def __setattr__(self, key, value):
        super().__setattr__(key, value)
        if not str(key).startswith('_') and key != 'meta':
            attr_class = type(getattr(type(self), key))
            attr_name = key
            value = self._normalize_attribute_value(
                attr_name, attr_class, value)
        super().__setattr__(key, value)

    def _normalize_attribute_value(
            self, attr_name, attr_class, provided_value):
        provided_value_class = type(provided_value)
        if provided_value_class is attr_class:
            return provided_value

        if provided_value is None or issubclass(attr_class, type(None)):
            return provided_value

        if provided_value_class is not str:
            raise ValueError(f'Can not normalize value with no string type: '
                             f'provided value type: {provided_value_class}, '
                             f'provided value: {provided_value}, '
                             f'option name: {attr_name}',
                             f'required class: {attr_class}',
                             )

        if issubclass(attr_class, Path):
            initiated_from_string = attr_class(provided_value)
        elif issubclass(attr_class, tzinfo.BaseTzInfo):
            initiated_from_string = timezone(provided_value)
        elif issubclass(attr_class, dict):
            initiated_from_string = json.loads(provided_value)
        else:
            raise ValueError(f'Can not normalize value from string to type: '
                              f'{attr_class}, value - {provided_value}')
        return initiated_from_string


class MicroserviceConfig(PyConfig):
    """Config class for microservice."""

    # cluster-level options (env var prefix should be 'CLUSTER_')
    rabbitmq_hostname: str = 'mb.cebb.pro'
    rabbitmq_port: str = '50001'
    rabbitmq_vhost: str = 'vhost'
    rabbitmq_username: str = 'admin'
    rabbitmq_password: str = 'rabbit-initial-password'

    _cluster_level_options = [
        'rabbitmq_hostname',
        'rabbitmq_port',
        'rabbitmq_vhost',
        'rabbitmq_username',
        'rabbitmq_password',
    ]

    def convert_key_to_env_key(self, key: str):
        if key in self._cluster_level_options:
            return f'{ENV_PREFIX_FOR_CLUSTER_LEVEL_OPTIONS}_{key}'.upper()
        else:
            return super().convert_key_to_env_key(key)

    def restore_key_from_env_key(self, env_key: str):
        default = super().restore_key_from_env_key(env_key)
        return default.replace(f'{ENV_PREFIX_FOR_CLUSTER_LEVEL_OPTIONS}_', '')
