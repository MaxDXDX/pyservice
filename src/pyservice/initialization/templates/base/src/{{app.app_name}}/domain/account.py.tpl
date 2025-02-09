from __future__ import annotations
import uuid
import json

from . import base


class Role(base.BaseDomainEntity):
    ref: str
    title: str = ''

    @property
    def _id(self):
        return self.ref

    @property
    def is_known(self) -> bool:
        return self in self.Predefined.all()

    class Predefined:
        @staticmethod
        def super_admin():
            return Role(
                ref='super-admin',
                title='Администратор экосистемы',
            )

        @classmethod
        def all(cls) -> set[Role]:
            return {
                cls.super_admin(),
            }

        @classmethod
        def get(cls, role: Role) -> Role | None:
            for _ in cls.all():
                if _ == role:
                    return _

        @classmethod
        def get_by_ref(cls, ref: str) -> Role | None:
            for _ in cls.all():
                if _.ref == ref:
                    return _

    @classmethod
    def build_from_ref(
            cls,
            ref: str,
            only_predefined: bool = False
    ) -> Role | None:
        role = Role(ref=ref)
        from_predefined = cls.Predefined.get(role)
        if only_predefined:
            return from_predefined
        else:
            return from_predefined if from_predefined else role


class Roles(base.SequenceOfEntities):
    items: set[Role]

    @property
    def list_of_refs(self) -> list[str]:
        return [_.ref for _ in self.items]

    @property
    def json_list_of_refs(self) -> str:
        return json.dumps(self.list_of_refs)

    @classmethod
    def build_from_list_of_refs(cls, list_of_refs) -> Roles:
        if list_of_refs is None:
            return cls.get_empty()
        role_set = {Role.build_from_ref(ref) for ref in list_of_refs}
        return Roles(items=role_set)

    @classmethod
    def build_from_json_list_of_refs(cls, json_list_of_refs) -> Roles:
        if json_list_of_refs is None:
            return cls.get_empty()
        list_of_refs = json.loads(json_list_of_refs)
        return cls.build_from_list_of_refs(list_of_refs)

    def get_only_known(self) -> Roles:
        return Roles(items={_ for _ in self.items if _.is_known})


class Account(base.BaseDomainEntity):
    id: uuid.UUID
    username: str
    last_name: str = ''
    first_name: str = ''
    roles: Roles = Roles.get_empty()

    @property
    def _id(self):
        return self.id

    class Examples:
        @staticmethod
        def get_random_without_roles():
            return Account(
                id=uuid.uuid4(),
                username='random-user',
            )

        @staticmethod
        def get_random_super_admin():
            return Account(
                id=uuid.uuid4(),
                username='random-user',
                roles=Roles(items={Role.Predefined.super_admin(), })
            )

        @classmethod
        def all(cls) -> set[Account]:
            return {
                cls.get_random_without_roles(),
                cls.get_random_super_admin(),
            }
