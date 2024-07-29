"""Domain models for app managers."""

from pyservice.domain.base import BaseModel
from pyservice.pyconfig.pyconfig import MicroserviceConfig, BackuperConfig
from pydantic_core._pydantic_core import ValidationError


class Microservice(BaseModel):
    """Microservice domain model."""

    ref: str
    config: MicroserviceConfig = None
    queues: list[str] = []
    own_queue: str = 'own-queue'

    @property
    def app_ref(self):
        return self.ref.partition(':')[0]

    def __str__(self):
        return f'Microservice "{self.ref}"'

    def __eq__(self, other):
        try:
            return self.ref == other.ref
        except AttributeError:
            return False

    def __hash__(self):
        return hash(self.ref)


class Backuper(Microservice):
    """Backuper domain model."""

    config: BackuperConfig = None

    def __str__(self):
        return f'Backuper "{self.ref}"'


class Cluster(BaseModel):
    """Cluster domain model."""

    microservices: set[Microservice]

    def add_microservice(self, microservice: Microservice):
        self.microservices.add(microservice)


def deserialize_microservice(serialized) -> Microservice | Backuper:
    try:
        m = Microservice(**serialized)
    except ValidationError:
        m = Backuper(**serialized)
    return m
