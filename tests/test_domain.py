"""
Tests.
"""

from unittest import TestCase
from pathlib import Path

from pyservice.domain.base import BaseModel

current_path = Path(__file__).parent


class DomainModelsTestCase(TestCase):
    """DDD tests."""

    def test_serialization(self):
        class User(BaseModel):
            firstname: str = 'Paul'
            lastname: str = 'McCartney'
        user = User()
        self.assertIsInstance(user.as_json(), str)
        self.assertIsInstance(user.as_dict(), dict)
