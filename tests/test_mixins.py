"""
Tests.
"""

from unittest import TestCase

from pyservice.mixins import mixins


class MixinsTestCase(TestCase):
    """Mixins tests."""

    def test_mixins(self):

        class User:
            firstname: str
            lastname: str
            phone: str

            def __init__(self, *args):
                self.firstname, self.lastname, self.phone = args

        human = User('Jim', 'Carrey', '+7123456789')
        clone = User('Jim', 'Carrey', '+7123456789')
        self.assertNotEqual(human, clone)

        class UserWithIdentityWithoutId(User, mixins.IdentityMixin):
            pass

        human = UserWithIdentityWithoutId('Jim', 'Carrey', '+7123456789')
        clone = UserWithIdentityWithoutId('Jim', 'Carrey', '+7123456789')
        with self.assertRaises(NotImplementedError):
            self.assertEqual(human, clone)

        class UserWithIdentity(User, mixins.IdentityMixin):

            @property
            def _id(self):
                return self.lastname, self.firstname

        human = UserWithIdentity('Jim', 'Carrey', '+7123456789')
        clone = UserWithIdentity('Jim', 'Carrey', '+7123456789')
        self.assertEqual(human, clone)




