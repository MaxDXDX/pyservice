"""Settings."""

from pyservice.pyconfig.pyconfig import MicroserviceConfig


class Config(MicroserviceConfig):
    instance_tag: str = 'local'

    round_to: int = 2


config = Config()
