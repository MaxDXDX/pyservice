"""
PyConfig class for building service`s config.
"""


import inspect
import json
import os
from pathlib import Path
from pytz import tzinfo, timezone


ENV_PREFIX_FOR_CLUSTER_LEVEL_OPTIONS = 'cluster'


class PyConfig:
    """Config class."""

    service_ref: str = ''
    env_var_prefix: str = ''

    # cluster-level options (env var prefix should be 'CLUSTER_')
    rabbitmq_hostname: str = 'mb.cebb.pro'
    rabbitmq_port: str = '50001'
    rabbitmq_vhost: str = 'vhost'
    rabbitmq_username: str = 'admin'
    rabbitmq_password: str = 'rabbit-initial-password'

    _directories_should_be_created: bool = True

    _secret_options = [

    ]

    _cluster_level_options = [
        'rabbitmq_hostname',
        'rabbitmq_port',
        'rabbitmq_vhost',
        'rabbitmq_username',
        'rabbitmq_password',
    ]

    def disable_auto_creating_directories(self):
        self._directories_should_be_created = False

    def enable_auto_creating_directories(self):
        self._directories_should_be_created = True

    def __init__(self):
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
            if value is None:
                raise ValueError(f'config option can not be None: '
                                 f'{option_name}')
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
            if 'password' in key or 'token' in key:
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
        if key in self._cluster_level_options:
            prefix = ENV_PREFIX_FOR_CLUSTER_LEVEL_OPTIONS
        else:
            prefix = self.env_var_prefix
        return f'{prefix}_{key}'.upper()

    def restore_key_from_env_key(self, env_key: str):
        lower = env_key.lower()
        without_prefix = (
            lower.replace(f'{self.env_var_prefix}_', '')
            .replace(f'{ENV_PREFIX_FOR_CLUSTER_LEVEL_OPTIONS}_', ''))
        return without_prefix

    @property
    def keys_from_environment(self) -> list[str]:
        return [self.convert_key_to_env_key(_) for _ in self.all_keys]

    def __getattribute__(self, item):
        attr_value = super().__getattribute__(item)
        if not str(item).startswith('_'):
            attr_name = item
            attr_class = type(getattr(type(self), item))
            self._on_get_attribute(attr_name, attr_class, attr_value)
        return attr_value

    # pylint: disable=W0613
    def _on_get_attribute(self, attr_name, attr_class, attr_value):
        if isinstance(attr_value, Path):
            if ('directory' in attr_name and
                    self._directories_should_be_created):
                attr_value.mkdir(exist_ok=True)

    def __setattr__(self, key, value):
        super().__setattr__(key, value)
        if not str(key).startswith('_'):
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

        if provided_value is None:
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
