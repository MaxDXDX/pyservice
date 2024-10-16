"""
Tests.
"""

import os
import json

from unittest import TestCase
from pathlib import Path

from pyservice.pyconfig.pyconfig import AppConfig
from pyservice.pyconfig.pyconfig import default_app_config
from pyservice.pyconfig.pyconfig import default_microservice_config

current_path = Path(__file__).parent


class AppConfigTestCase(TestCase):
    """App config tests."""

    def test_set_setting_from_string(self) -> None:
        class SimpleConfig(AppConfig):
            my_setting: bool = True
        cfg = SimpleConfig()
        self.assertEqual(cfg.my_setting, True)
        cfg.my_setting = json.loads('false')
        self.assertEqual(cfg.my_setting, False)

    def test_simple_app_config(self) -> None:
        class SimpleConfig(AppConfig):
            service_ref: str = 'my_service'
        cfg = SimpleConfig(__file__)
        self.assertEqual(cfg.service_ref, 'my_service')

    def test_override_option_by_env(self) -> None:
        desired_value = 'Asia/Tokyo'
        os.environ['tz'] = desired_value

        class ConfigFromEnv(AppConfig):
            pass
        cfg = ConfigFromEnv(__file__)
        self.assertEqual(cfg.tz, desired_value)

    def test_convert_to_yaml(self):
        cfg = default_app_config
        as_yaml = cfg.as_yaml()
        self.assertIsInstance(as_yaml, str)

    def test_serialization(self):
        cfg = default_app_config
        as_dict = cfg.as_dict()
        restored = AppConfig(**as_dict)
        self.assertEqual(cfg, restored)


class MicroserviceTestCase(TestCase):
    """Microservice config tests."""

    def test_microservice_config(self) -> None:
        cfg = default_microservice_config
        self.assertTrue(cfg.instance_tag)

    def test_convert_to_yaml(self):
        cfg = default_microservice_config
        as_yaml = cfg.as_yaml()
        self.assertIsInstance(as_yaml, str)

