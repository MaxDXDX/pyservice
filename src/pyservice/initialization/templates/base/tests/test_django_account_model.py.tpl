from django.test import testcases as django_test_cases

from {{ app.app_name }} import manager
from {{ app.app_name }}.django.main.models import Account as DjangoAccount


class InitialTestCase(django_test_cases.TestCase):

    def test_updating_superusers(self):
        superusers_from_config = manager.config.super_users
        superusers = DjangoAccount.update_superusers()
        self.assertEqual(len(superusers_from_config), len(superusers))
