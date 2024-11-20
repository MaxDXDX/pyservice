from __future__ import annotations

from typing import Any
from django.db import models
from django.db.models import Model, QuerySet
from django.utils.functional import cached_property

from pyservice.domain.base import BaseModel

from {{ app.app_name }} import manager

log = manager.get_logger_for_pyfile(__file__)


class BaseDjangoModel(Model):
    objects: QuerySet

    version = models.PositiveBigIntegerField(
        null=True, blank=True, unique=True)
    django_version = models.PositiveBigIntegerField(
        null=True, blank=True, unique=True)

    @classmethod
    def model_name(cls):
        return cls.__name__

    @classmethod
    def filter_by_domain(cls, domain: BaseModel) -> QuerySet | list:
        result = cls._filter_by_domain(domain)
        if result is None:
            result = []
        return result

    @classmethod
    def _filter_by_domain(cls, domain: BaseModel) -> QuerySet | list:
        return []  # override

    @classmethod
    def get_by_domain(cls, domain: BaseModel) -> Any:
        log.debug('trying to find django record for domain model (%s): %s',
                  type(domain), domain)
        matched = cls.filter_by_domain(domain)
        if matched:
            try:
                assert len(matched) == 1
            except AssertionError as e:
                log.critical('more than 1 record has been found:')
                for i, _ in enumerate(matched):
                    log.critical('%s: %s', i, _)
                raise e
            else:
                found = matched[0]
                log.debug('exactly one record has been found: %s', found)
                return found
        log.debug('no django record has been found')

    @classmethod
    def create_from_domain(cls, domain: BaseModel) -> Any:
        return cls._create_from_domain(domain)

    @classmethod
    def _create_from_domain(cls, domain: BaseModel) -> Any:
        raise NotImplementedError

    def update_from_domain(self, domain: BaseModel) -> Any:
        log.debug('updating current django record "%s" by domain (%s) "%s"',
                  self, type(domain), domain)
        self._update_from_domain(domain)
        log.debug('updated django record: "%s"', self)
        return self

    def _update_from_domain(self, domain: BaseModel) -> Any:
        log.debug('no need to update me')
        return self  # implement if it is needed

    @classmethod
    def update_or_create_from_domain(cls, domain: BaseModel) -> Any:
        log.debug('updating domain model (class %s) at django repo: %s',
                  type(domain), domain)
        current = cls.get_by_domain(domain)
        if not current:
            log.debug('no current record has been found, '
                      'creating the brand new ...')
            updated = cls.create_from_domain(domain)
        else:
            log.debug('current record has been found: %s', current)
            updated = current.update_from_domain(domain)
        log.debug('updated (or created) django record: %s', updated)
        return updated

    def to_domain(self) -> Any:
        log.debug('restoring domain model from django object: %s', self)
        restored = self._to_domain()
        log.debug('restored: %s', restored)
        return restored

    def _to_domain(self) -> BaseModel:
        raise NotImplementedError

    @classmethod
    def all(cls) -> QuerySet:
        log.debug('fetching all records from django model <%s>',
                  cls.model_name())
        fetched = cls.objects.all()
        log.debug('number of fetched records: %s', len(fetched))
        return fetched

    @classmethod
    def all_domains(cls) -> list:
        log.debug('fetching all domains from django model <%s>',
                  cls.model_name())
        dj = cls.all()
        total = len(dj)
        if total == 0:
            log.debug('no one')
            return []
        log.debug('total django records: %s', total)
        log.debug('converting to domain ...')
        d = [_.to_domain() for _ in dj]
        log.debug('converted ...')
        return d

    @classmethod
    def size(cls) -> int:
        return len(cls.all())

    @cached_property
    def for_admin(self) -> str:
        custom = self._for_admin
        if custom:
            return custom

    @property
    def _for_admin(self) -> str | None:
        return None

    @cached_property
    def as_nested(self) -> str:
        custom = self._as_nested
        return custom

    @property
    def _as_nested(self) -> str | None:
        return None

    @cached_property
    def _for_str(self) -> str | None:
        return None

    def __str__(self):
        try:
            model_name = type(self).__name__
            custom = self._for_str
            if custom is not None:
                return f'dj{model_name}: {custom}'
            elif self.as_nested is not None:
                return f'dj{model_name}: {self.as_nested}'
            elif self.for_admin is not None:
                return f'dj{model_name}: {self.for_admin}'
            else:
                return f'<dj{model_name}({self.pk})>'
        except Exception as e:
            return f'ERROR_STR: {type(e)} {e}'

    class Meta:
        abstract = True

