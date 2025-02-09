from django.test import testcases as django_test_cases

from {{ app.app_name }} import manager
from {{ app.app_name }}.django.main import models as django_models
from {{ app.app_name }}.django.main import model_base as django_base_models
from {{ app.app_name }}.domain import account as account_domain
from {{ app.app_name }}.domain import base as domain_base


class DjangoOrmTestCase(django_test_cases.TestCase):

    def check_orm(self,
            domain_object: domain_base.BaseDomainModel,
            django_model: type[django_base_models.BaseModelForDomain | django_base_models.BaseAccountModel],
            check_unique: bool = True
    ) -> tuple[
             django_base_models.BaseModelForDomain,
             domain_base.BaseDomainModel,
    ]:
        if check_unique:
            django_model.objects.all().delete()
        if hasattr(django_model, 'is_generic'):
            assert django_model.is_generic
            if django_model.is_generic:
                for _ in django_model.all_end_django_models():
                    _.objects.all().delete()
        from_django = django_model.update_from_domain(domain_object)
        fetched = from_django.to_domain()
        self.assertIsInstance(from_django, django_model)
        self.assertIsInstance(fetched, type(domain_object))
        self.assertEqual(fetched, domain_object)

        if check_unique:
            again_from_django = django_model.update_from_domain(domain_object)
            # should not create a clone
            all_from_django = django_model.objects.all()
            self.assertEqual(len(all_from_django), 1)
            self.assertEqual(from_django, again_from_django)

        return from_django, fetched

    def test_account_orm(self):
        for _ in account_domain.Account.Examples.all():
            self.check_orm(
                domain_object=_,
                django_model=django_models.Account,
            )
