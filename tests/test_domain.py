"""
Tests.
"""

from typing import Any
from unittest import TestCase
from pathlib import Path

from pyservice.domain.base import BaseModel
from pyservice.domain import files as files_domain
from pyservice.files import files as files_utils

from pyservice.manager.manager import get_default_app_manager

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
            def _serialized(self, context: Any = None) -> dict:
                return self.as_dict(camel_case=True)

        car = Car(wheel_size=15, brand_country='france')

        serialized = car.as_dict(camel_case=True)
        self.assertIn('wheelSize', serialized)
        self.assertIn('brandCountry', serialized)

        serialized = car.serialized()
        self.assertIn('wheelSize', serialized)
        self.assertIn('brandCountry', serialized)

    def test_files_domain(self):
        manager = get_default_app_manager()
        number_of_files = 5

        local_files_items = set()

        for _ in range(number_of_files):
            local_path = files_utils.create_text_file_in_directory(
                directory=manager.directory_for_tmp,
                content=f'content of text file #{_}',
                filename=f'some-local-file-{_}.txt'
            )
            local_file = files_domain.LocalFile(
                fullpath=local_path
            )
            self.assertIsInstance(local_file, files_domain.LocalFile)
            local_files_items.add(local_file)

        local_files = files_domain.LocalFiles(items=local_files_items)
        self.assertEqual(local_files.size, 5)



