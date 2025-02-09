from __future__ import annotations
import typing as t
import uuid

from django.db import models
from django.contrib.auth import models as auth_models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist


from {{ app.app_name }}.domain.base import BaseDomainModel

from {{ app.app_name }} import manager


log = manager.get_logger_for_pyfile(__file__)


class VersionsMixin:
    objects: models.QuerySet

    version = models.PositiveBigIntegerField(
        null=True, blank=True, unique=True)
    django_version = models.PositiveBigIntegerField(
        null=True, blank=True, unique=True)


class DomainMixin:
    objects: models.QuerySet

    @classmethod
    def filter_by_domain(
            cls, domain: BaseModelForDomain) -> models.QuerySet | list:
        log.debug('try to find records in django model %s for domain: %s',
                  cls, domain)
        result = cls._filter_by_domain(domain)
        if result is None:
            log.debug('no record in %s for domain: %s', cls, domain)
            result = []
        return result

    @classmethod
    def _filter_by_domain(
            cls, domain: BaseModelForDomain) -> models.QuerySet | list:
        raise NotImplementedError
        # return []  # override

    @classmethod
    def get_by_domain(cls, domain: BaseModelForDomain) -> t.Any | None:
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
    def create_from_domain(cls, domain: BaseModelForDomain) -> t.Any:
        log.debug(
            'creating new django record from domain (%s): %s',
            type(domain), domain
        )
        created = cls._create_from_domain(domain)
        log.debug('new django record has been created: %s', created)
        return created

    @classmethod
    def _create_from_domain(cls, domain: BaseModelForDomain) -> t.Any:
        raise NotImplementedError

    def update_record_from_domain(self, domain: BaseDomainModel) -> t.Any:
        log.debug('updating current django record "%s" by domain (%s) "%s"',
                  self, type(domain), domain)
        self._update_record_from_domain(domain)
        log.debug('updated django record: "%s"', self)
        return self

    def _update_record_from_domain(self, domain: BaseDomainModel):
        log.debug('no need to update me')

    @classmethod
    def update_from_domains(cls, domains: list | set) -> t.Any:
        results = []
        for domain in domains:
            result = cls.update_from_domain(domain)
            results.append(result)
        return results

    @classmethod
    def update_from_domain(cls, domain: t.Any) -> t.Any:
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

    def to_domain(self) -> t.Any:
        log.debug('restoring domain model from django object: %s', self)
        restored = self._to_domain()
        log.debug('restored: %s', restored)
        return restored

    def _to_domain(self) -> BaseModelForDomain:
        raise NotImplementedError


class GenericContentTypeModel(models.Model, DomainMixin):
    is_generic: bool = True
    objects: models.QuerySet

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object: t.Any = GenericForeignKey(
        "content_type", "object_id")

    model_map: dict[BaseModelForDomain, models.Model]

    @classmethod
    def all_end_django_models(cls) -> list[models.Model]:
        return list(cls.model_map.values())

    @classmethod
    def all_domain_models(cls) -> list[BaseModelForDomain]:
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
            domain: BaseModelForDomain,
    ) -> models.QuerySet | list:
        log.debug('try to find generic object for domain <%s> (class - %s)',
                  domain, type(domain))
        django_model: BaseModelForDomain = cls.model_map[type(domain)]
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
            domain: BaseModelForDomain,
    ) -> GenericContentTypeModel:
        model: type[models.BaseDjangoModel] = cls.model_map[type(domain)]
        end: models.BaseDjangoModel = model.create_from_domain(domain)
        generic = cls(content_object=end)
        generic.save()
        return generic

    def to_domain(self) -> t.Any:
        return self.content_object.to_domain()

    def serialize(self):
        return self.content_object.serialize()

    @classmethod
    def add_generic_by_end(cls, end) -> GenericContentTypeModel:
        generic = cls(content_object=end)
        generic.save()
        return generic

    @classmethod
    def _get_generic_by_end(cls, end: models.Model) -> GenericContentTypeModel | None:
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


class BaseModel(models.Model):
    objects: models.QuerySet

    @classmethod
    def size(cls) -> int:
        return len(cls.all())

    @classmethod
    def all(cls) -> models.QuerySet:
        return cls.objects.all()

    class Meta:
        abstract = True


class BaseModelForDomain(BaseModel, DomainMixin):
    objects: models.QuerySet

    class Meta:
        abstract = True


class BaseAccountModel(auth_models.AbstractUser, DomainMixin):
    objects: auth_models.UserManager

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    global_uuid = models.UUIDField(
        editable=True, unique=True, null=True, blank=True)
    roles = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        abstract = True

    @classmethod
    def update_superusers(cls) -> list[t.Self]:
        log.debug('updating superusers:')
        actual_superusers = manager.config.super_users
        log.debug('- actual superusers from config: %s', actual_superusers)
        for user in actual_superusers:
            username, password, e_mail = user
            log.debug('updating user: %s', username)
            try:
                existing_user = cls.objects.all().get(username=username)
            except ObjectDoesNotExist:
                log.debug('user "%s" does not exist, '
                          'creating the new one ...', username)
                new_superuser = cls.objects.create_superuser(
                    username,
                    e_mail,
                    password,
                )
                log.debug('new superuser has been created: %s', new_superuser)
            else:
                log.debug('superuser already exists (%s), updating data ...',
                          existing_user)
                existing_user.set_password(password)
                existing_user.email = e_mail
                existing_user.save()
                log.debug('already present superuser has been updated: %s',
                          existing_user)
        actual_usernames = [_[0] for _ in actual_superusers]
        orphans = (cls.objects.exclude(is_superuser=False)
                   .exclude(username__in=actual_usernames))
        if orphans:
            log.debug('orphans: %s', orphans)
            for orphan in orphans:
                log.debug('deleting orphan superuser %s ...', orphan)
                assert orphan.is_superuser
                orphan.delete()
        else:
            log.debug('no orphans detected')
        super_users_after_updating = cls.objects.exclude(is_superuser=False)
        return [_ for _ in super_users_after_updating]