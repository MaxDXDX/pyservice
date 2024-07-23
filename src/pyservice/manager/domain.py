"""Domain models for app managers."""

from pyservice.ddd.model import BaseModel
from pyservice.pyconfig.pyconfig import MicroserviceConfig


class Microservice(BaseModel):

    config: MicroserviceConfig
    ref: str
    queues: list[str]
