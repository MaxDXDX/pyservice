# you might import pydantic models to use it in your config:
# from pydantic import ()

from pyservice.pyconfig.pyconfig import DjangoBasedMicroserviceConfig


class Config(DjangoBasedMicroserviceConfig):
    # base level
    instance_tag: str = 'local'
    instance_human_name: str = '{{ app.description }}'

    # django_level
    django_db_port: str = '8433'
    is_keycloak_auth_enabled: bool = False
    url_prefix: str | None = '{{ app.url_prefix }}'

    # business rules specific
    # any other attributes


config = Config()