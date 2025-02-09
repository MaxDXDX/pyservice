from __future__ import annotations

import typing as t

from django.db import models

from {{ app.app_name }} import manager
from . import model_base as base_django_models
from .model_base import BaseModelForDomain

from {{ app.app_name }}.domain import account as domain_account
from ...domain.base import BaseDomainModel

log = manager.get_logger_for_pyfile(__file__, with_path=True)


class Account(base_django_models.BaseAccountModel):

    @classmethod
    def _filter_by_domain(
            cls,
            domain: domain_account.Account
    ) -> models.QuerySet | list:
        return cls.objects.filter(global_uuid=domain.id)

    @classmethod
    def _create_from_domain(
            cls,
            domain: domain_account.Account
    ) -> t.Self:
        args_for_new_object = {
            'global_uuid': domain.id,
            'username': domain.username,
            'last_name': domain.last_name,
            'first_name': domain.first_name,
            'roles': domain.roles.json_list_of_refs,
        }
        new = cls(**args_for_new_object)
        new.save()
        return new

    def _update_record_from_domain(self, domain: domain_account.Account):
        self.username = domain.username
        self.last_name = domain.last_name
        self.first_name = domain.first_name
        self.roles = domain.roles.json_list_of_refs
        self.save()

    def _to_domain(self) -> domain_account.Account:
        domain = domain_account.Account(
            id=self.global_uuid,
            username=self.username,
            last_name=self.last_name,
            first_name=self.first_name,
            roles=domain_account.Roles.build_from_json_list_of_refs(self.roles)
        )
        return domain

