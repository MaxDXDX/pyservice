"""Domain models."""

from pydantic import BaseModel as PydanticBaseModel
from pydantic_settings import BaseSettings as PydanticBaseSettings

import yaml


class SerializationMixin:

    def as_yaml(self) -> str:
        as_dict = self.model_dump(mode='json')
        as_yaml = yaml.dump(as_dict, sort_keys=False)
        return as_yaml


class BaseModel(PydanticBaseModel, SerializationMixin):
    pass


class BaseSettings(PydanticBaseSettings, SerializationMixin):
    pass
