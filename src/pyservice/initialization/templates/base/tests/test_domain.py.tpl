from django.test import testcases as django_test_cases

from {{ app.app_name }} import manager
from {{ app.app_name }}.django.main import models as django_models
from {{ app.app_name }}.domain import account as account_domain


class DomainModelsTestCase(django_test_cases.TestCase):

    def test_account_domain_model(self):
        user = account_domain.Account.Examples.get_random_without_roles()
        clone = account_domain.Account.Examples.get_random_without_roles()
        clone.id = user.id
        self.assertEqual(user, clone)
