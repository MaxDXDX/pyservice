from __future__ import annotations

from typing import Any
from django.db import models
from django.db.models import Model, QuerySet
from django.utils.functional import cached_property

from pyservice.domain.base import BaseModel

from {{ app.app_name }} import manager


log = manager.get_logger_for_pyfile(__file__)


class DomainMixin:
    objects: QuerySet

    @classmethod
    def filter_by_domain(cls, domain: BaseModel) -> QuerySet | list:
        log.debug('try to find records in django model %s for domain: %s',
                  cls, domain)
        result = cls._filter_by_domain(domain)
        if result is None:
            log.debug('no record in %s for domain: %s', cls, domain)
            result = []
        return result

    @classmethod
    def _filter_by_domain(cls, domain: BaseModel) -> QuerySet | list:
        raise NotImplementedError
        # return []  # override

    @classmethod
    def get_by_domain(cls, domain: BaseModel | BaseEntity) -> Any | None:
        log.debug('trying to find django record for domain model (%s): %s',
                  type(domain), domain)
        matched = cls.filter_by_domain(domain)
        if matched:
            try:
                assert len(matched) == 1
            except AssertionError as e:
                log.critical('more than 1 record has been found '
                             'for <%s> django model', cls)
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
        log.debug(
            'creating new django record from domain (%s): %s',
            type(domain), domain
        )
        created = cls._create_from_domain(domain)
        log.debug('new django record has been created: %s', created)
        return created

    @classmethod
    def _create_from_domain(cls, domain: BaseModel) -> Any:
        raise NotImplementedError

    def update_record_from_domain(self, domain: BaseModel) -> Any:
        log.debug('updating current django record "%s" by domain (%s) "%s"',
                  self, type(domain), domain)
        self._update_record_from_domain(domain)
        log.debug('updated django record: "%s"', self)
        return self

    def _update_record_from_domain(self, domain: BaseModel):
        log.debug('no need to update me')

    @classmethod
    def update_from_domains(cls, domains: list | set) -> Any:
        results = []
        for domain in domains:
            result = cls.update_from_domain(domain)
            results.append(result)
        return results

    @classmethod
    def update_from_domain(cls, domain: Any) -> Any:
        log.debug('updating domain model (class %s) at django repo: %s',
                  type(domain), domain)
        current = cls.get_by_domain(domain)
        if not current:
            log.debug('no current record has been found, '
                      'creating the brand new ...')
            updated = cls.create_from_domain(domain)
        else:
            log.debug('current record has been found: %s', current)
            updated = current.update_record_from_domain(domain)
        log.debug('updated (or created) django record: %s', updated)
        return updated

    def to_domain(self) -> Any:
        log.debug('restoring domain model from django object: %s', self)
        restored = self._to_domain()
        log.debug('restored: %s', restored)
        return restored

    def _to_domain(self) -> BaseModel:
        raise NotImplementedError


class GenericContentTypeModel(Model, DomainMixin):
    is_generic: bool = True
    objects: QuerySet
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object: Any = GenericForeignKey(
        "content_type", "object_id")

    objects: QuerySet
    model_map: dict[BaseModel | BaseEntity, Model]

    @classmethod
    def all_end_django_models(cls) -> list[Model]:
        return list(cls.model_map.values())

    @classmethod
    def all_domain_models(cls) -> list[BaseModel | BaseEntity]:
        return list(cls.model_map.keys())

    class Meta:
        unique_together = [["content_type", "object_id"]]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]
        abstract = True


    def __str__(self):
        return f'{type(self)} for {self.content_object}'

    @classmethod
    def _filter_by_domain(
            cls,
            domain: BaseModel | BaseEntity,
    ) -> QuerySet | list:
        log.debug('try to find generic object for domain <%s> (class - %s)',
                  domain, type(domain))
        django_model: BaseDjangoModel = cls.model_map[type(domain)]
        log.debug('django model for that domain: %s', django_model)
        end_object = django_model.get_by_domain(domain)
        if not end_object:
            log.debug('no data in django model - will return empty list')
            return []
        log.debug('django record for that domain: %s', end_object)
        generic = cls._get_generic_by_end(end_object)
        if not generic:
            msg = (f'No generic record in {cls} for next record: '
                   f'{type(end_object)} | {end_object}')
            log.critical(msg)
            raise RuntimeError(msg)
        log.debug('generic record found for django record %s: %s',
                  end_object, generic)
        return [generic, ]

    @classmethod
    def _create_from_domain(
            cls,
            domain: BaseModel | BaseEntity,
    ) -> GenericContentTypeModel:
        model: type[BaseDjangoModel] = cls.model_map[type(domain)]
        end: BaseDjangoModel = model.create_from_domain(domain)
        generic = cls(content_object=end)
        generic.save()
        return generic

    def to_domain(self) -> Any:
        return self.content_object.to_domain()

    def serialize(self):
        return self.content_object.serialize()

    @classmethod
    def add_generic_by_end(cls, end) -> GenericContentTypeModel:
        generic = cls(content_object=end)
        generic.save()
        return generic

    @classmethod
    def _get_generic_by_end(cls, end: Model) -> GenericContentTypeModel | None:
        log.debug('try to find existing generic for django record: %s', end)
        matched = cls.objects.filter(
            content_type=ContentType.objects.get_for_model(end),
            object_id=end.id,
        )
        if not matched:
            log.debug('no generic record found for django record: %s', end)
            return None
        if len(matched) == 1:
            generic = matched[0]
            log.debug('generic record found for django record %s: %s',
                      end, generic)
            return generic

        log.warning(
            'more than one generic record found for django record %s '
            '(total - %s): %s',
            end, len(matched), matched)
        raise ValueError(
            'more than one generic record found for django record (see log)')

    @classmethod
    def update_generic_by_end(cls, end) -> models.Model:
        current_generic = cls.objects.get(
            content_type=ContentType.objects.get_for_model(end),
            object_id=end.id,
        )
        if not current_generic:
            generic = cls.add_generic_by_end(end)
        else:
            generic = current_generic
        return generic


class BaseDjangoModelForDomain(Model, DomainMixin):
    objects: QuerySet

    version = models.PositiveBigIntegerField(
        null=True, blank=True, unique=True)
    django_version = models.PositiveBigIntegerField(
        null=True, blank=True, unique=True)

    @classmethod
    def size(cls) -> int:
        return len(cls.all())

    @classmethod
    def all(cls) -> QuerySet:
        return cls.objects.all()

    class Meta:
        abstract = True
