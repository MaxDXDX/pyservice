"""
Tests.
"""
from typing import Any
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
        self.assertIsInstance(user.as_toml(), str)

    def test_camel_cased_serialization(self):
        class Car(BaseModel):
            wheel_size: int
            brand_country: str

            def _serialized(self, context: Any = None) -> dict:
                return self.as_dict(camel_case=True)

        car = Car(wheel_size=15, brand_country='france')

        serialized = car.as_dict(camel_case=True)
        self.assertIn('wheelSize', serialized)
        self.assertIn('brandCountry', serialized)

        serialized = car.serialized()
        self.assertIn('wheelSize', serialized)
        self.assertIn('brandCountry', serialized)


