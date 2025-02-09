from pyservice.domain import base
from pyservice.mixins import mixins


class BaseDomainModel(base.BaseModel):
    pass


class BaseDomainEntity(BaseDomainModel, mixins.IdentityMixin):
    def __hash__(self):
        return self._hash_of_id

    def __eq__(self, other):
        return self._eq_by_id(other)


class SequenceOfEntities(BaseDomainEntity, mixins.SequenceMixin):
    items: list | set

    @classmethod
    def get_empty(cls):
        return cls(items=set())
