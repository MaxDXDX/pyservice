"""
Tests.
"""

from unittest import TestCase

from pyservice.domain import base
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

    def test_sequence_mixin_with_list(self):
        class RoleList(base.BaseModel, mixins.SequenceMixin):
            items: list[str]

        user_roles = RoleList(items=[
            'admin',
            'moderator',
            'seller',
        ])

        another_user_roles = RoleList(items=[
            'admin',
            'moderator',
            'user',
        ])

        self.assertEqual(user_roles.size, 3)

        intersection = user_roles.intersection_with_another(another_user_roles)
        self.assertEqual(
            user_roles.has_intersection_with_another(another_user_roles), True)
        self.assertIsInstance(intersection, type(user_roles))
        self.assertEqual(intersection.size, 2)
        self.assertEqual(set(intersection.items), {'admin', 'moderator'})

    def test_sequence_mixin_with_set(self):
        class RoleList(base.BaseModel, mixins.SequenceMixin):
            items: set[str]

        user_roles = RoleList(items={
            'admin',
            'moderator',
            'seller',
        })

        another_user_roles = RoleList(items={
            'admin',
            'moderator',
            'user',
        })

        self.assertEqual(user_roles.size, 3)
        self.assertEqual(
            user_roles.has_intersection_with_another(another_user_roles), True)

        intersection = user_roles.intersection_with_another(another_user_roles)
        self.assertIsInstance(intersection, type(user_roles))
        self.assertEqual(intersection.items, {'moderator', 'admin'})

