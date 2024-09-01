"""Domain models."""
import json

from pydantic import BaseModel as PydanticBaseModel
from pydantic_settings import BaseSettings as PydanticBaseSettings

import yaml

from pyservice.mixins.mixins import IdentityMixin

class SerializationMixin:
    """Serialization."""

    def as_yaml(self) -> str:
        as_dict = self.model_dump(mode='json')
        as_yaml = yaml.dump(as_dict, sort_keys=False)
        return as_yaml

    def as_dict(self) -> dict:
        as_dict = self.model_dump(mode='json')
        return as_dict

    def as_json(self) -> str:
        as_dict = json.dumps(self.as_dict())
        return as_dict


class BaseModel(PydanticBaseModel, SerializationMixin):
    pass


class BaseEntity(PydanticBaseModel, SerializationMixin, IdentityMixin):
    def __hash__(self):
        assert self._hash_of_id
        return self._hash_of_id

    def __eq__(self, other):
        return self._eq_by_id(other)


class BaseSettings(PydanticBaseSettings, SerializationMixin):
    pass
