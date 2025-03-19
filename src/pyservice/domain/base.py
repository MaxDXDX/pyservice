"""Domain models."""
import json
import toml
from typing import Any

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict
from pydantic import alias_generators, AliasGenerator
from pydantic_settings import BaseSettings as PydanticBaseSettings

import yaml

from pyservice.mixins.mixins import IdentityMixin


camel_case_alias_generator = AliasGenerator(
    serialization_alias=alias_generators.to_camel,
)


class SerializationMixin:
    """Serialization."""

    def as_yaml(self) -> str:
        as_dict = self.model_dump(mode='json')
        as_yaml = yaml.dump(as_dict, sort_keys=False)
        return as_yaml

    def as_dict(self, camel_case=False) -> dict:
        as_dict = self.model_dump(mode='json', by_alias=camel_case)
        return as_dict

    def as_json(self) -> str:
        as_dict = json.dumps(self.as_dict())
        return as_dict

    def as_toml(self) -> str:
        return toml.dumps(self.as_dict())

    def serialized(self, context: Any = None) -> dict | list:
        return self._serialized(context)

    def serialize(self, context: Any = None) -> dict | list:
        return self.model_dump(mode='json', context=context)

    # pylint: disable=W0613
    def _serialized(self, context: Any = None) -> dict | list:
        return self.as_dict()

    @classmethod
    def build_from_serialized(cls, serialized) -> Any:
        return cls(**serialized)


class BaseModel(PydanticBaseModel, SerializationMixin):
    """Base model for Domain models."""

    model_config = ConfigDict(
        alias_generator=camel_case_alias_generator
    )

    def model_dump(self, *args, **kwargs) -> dict[str, Any]:
        context = kwargs.get('context')
        if context:
            try:
                is_for_frontend = context.is_for_frontend
            except AttributeError:
                is_for_frontend = False
            kwargs['by_alias'] = is_for_frontend
        return super().model_dump(*args, **kwargs)

    # @field_serializer('*', mode='wrap')
    # def context_propagation(
    #         self, v: t.Any, nxt: SerializerFunctionWrapHandler, info):
    #     if isinstance(v, pydantic.BaseModel):
    #         return v.model_dump(context=info.context)
    #     return nxt(v)


class BaseFrozenModel(PydanticBaseModel, SerializationMixin):
    model_config = ConfigDict(
        frozen=True,
        alias_generator=camel_case_alias_generator,
    )


class BaseModelWithArbitraryFields(BaseModel):
    model_config = ConfigDict(
        alias_generator=camel_case_alias_generator,
        arbitrary_types_allowed=True
    )


class BaseEntity(PydanticBaseModel, SerializationMixin, IdentityMixin):
    def __hash__(self):
        assert self._hash_of_id
        return self._hash_of_id

    def __eq__(self, other):
        return self._eq_by_id(other)


class BaseSettings(PydanticBaseSettings, SerializationMixin):
    pass


