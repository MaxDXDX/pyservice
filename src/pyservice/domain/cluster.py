"""Domain models for app managers."""

from pyservice.domain.base import BaseModel
from pyservice.pyconfig.pyconfig import MicroserviceConfig


class Microservice(BaseModel):
    """Microservice domain model."""

    ref: str
    config: MicroserviceConfig = None
    queues: list[str] = None
    own_queue: str = None

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


class Cluster(BaseModel):
    """Cluster domain model."""

    microservices: set[Microservice]

    def add_microservice(self, microservice: Microservice):
        self.microservices.add(microservice)
