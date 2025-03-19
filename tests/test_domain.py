"""
Tests.
"""

import typing as t
import re
from unittest import TestCase
from pathlib import Path
from datetime import datetime as dt

from pyservice.domain.base import BaseModel
from pyservice.text_tools import text_tools

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

            # pylint: disable=W0613
            def _serialized(self, context: t.Any = None) -> dict:
                return self.as_dict(camel_case=True)

        car = Car(wheel_size=15, brand_country='france')

        serialized = car.as_dict(camel_case=True)
        self.assertIn('wheelSize', serialized)
        self.assertIn('brandCountry', serialized)

        serialized = car.serialized()
        self.assertIn('wheelSize', serialized)
        self.assertIn('brandCountry', serialized)


    def test_serialization_context(self):
        class Context:
            @property
            def is_for_frontend(self) -> bool:
                return True

        class Nested(BaseModel):
            a_of_nested: str = 'some nested value'
            b_of_nested: str = 'some nested value'
            created_at: dt = dt.now()

        class Root(BaseModel):
            a_of_root: str = 'some root value'
            b_of_root: str = 'some root value'
            nested_a: Nested = Nested()
            nested_b: Nested = Nested()

        model = Root()

        in_camel_case = model.serialize(context=Context())
        self.assertNotIn('_', str(in_camel_case))

        in_original_snake_case = model.serialize()
        self.assertNotIn('_', str(in_camel_case))
        all_keys = text_tools.get_all_keys(in_original_snake_case)

        def has_capital_letter(text: str) -> bool:
            return bool(re.search(r'[A-Z]', text))

        for key in all_keys:
            self.assertFalse(has_capital_letter(key))
