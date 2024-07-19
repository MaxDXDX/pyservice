"""
Tests.
"""

import json

from pytz import timezone, tzinfo
from unittest import TestCase
from pathlib import Path
import shutil

from pyservice.pyconfig.pyconfig import PyConfig

current_path = Path(__file__).parent


class PyConfigTestCase(TestCase):
    """Config tests."""

    tmp_path = current_path / 'tmp'

    @classmethod
    def remove_tmp_entities(cls):
        try:
            shutil.rmtree(cls.tmp_path)
        except FileNotFoundError:
            pass

    @classmethod
    def setUpClass(cls) -> None:
        cls.remove_tmp_entities()
        cls.tmp_path.mkdir(exist_ok=True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.remove_tmp_entities()

    def setUp(self) -> None:

        class MyConfig(PyConfig):
            service_ref = 'my_service'
            api_hostname = 'awesome-api.com'
            downloads_directory = self.tmp_path / 'my-downloads'
            readme_file = self.tmp_path / 'readme.txt'
            tz = timezone('Europe/Moscow')
            county_codes = {
                'RU': 'Russia',
                'US': 'USA',
            }
        try:
            MyConfig.downloads_directory.rmdir()
        except FileNotFoundError:
            pass
        self.cfg = MyConfig()
        self.cfg_cls = MyConfig

    def test_get_config_options(self):
        keys = self.cfg.all_keys
        self.assertIsInstance(keys, list)
        for _ in keys:
            self.assertIsInstance(_, str)
            getattr(self.cfg, _)

    def test_check_names_of_directory_and_file_attributes(self):
        class CorrectConfig(PyConfig):
            service_ref = 'rest-api'
            my_directory = self.tmp_path / 'my-directory'
            my_file = self.tmp_path / 'my-file'

        class IncorrectConfig(PyConfig):
            service_ref = 'rest-api'
            my_path = self.tmp_path / 'my-directory'
            config = self.tmp_path / 'my-config-file'

        CorrectConfig()
        with self.assertRaises(ValueError):
            IncorrectConfig()

    def test_create_path_attribute_on_first_access_only_for_dir(self):
        # path not created if read it from class (not from instance)
        self.assertIsInstance(self.cfg_cls.downloads_directory, Path)
        self.assertFalse(
            self.cfg_cls.downloads_directory.is_dir(),
            msg=str(self.cfg_cls.downloads_directory),
        )
        # path created after reading it from config:
        download_path = self.cfg.downloads_directory
        self.assertTrue(download_path.is_dir())

        file = self.cfg.readme_file
        self.assertFalse(file.is_dir())

    def test_using_env_vars(self):
        env_keys = self.cfg.keys_from_environment
        keys = self.cfg.all_keys
        self.assertIsInstance(keys, list)
        self.assertEqual(len(env_keys), len(keys))
        for key in keys:
            env_key = self.cfg.convert_key_to_env_key(key)
            restored = self.cfg.restore_key_from_env_key(env_key)
            self.assertEqual(key, restored)
            value_from_cfg = getattr(self.cfg, key)
            value_from_cfg_class = getattr(self.cfg_cls, key)
            self.assertIsInstance(value_from_cfg, type(value_from_cfg_class))
            # pylint: disable=W0212
            if key in self.cfg._cluster_level_options:
                print(env_key, key)

    def test_can_set_any_option_from_string(self):
        # Path:
        self.cfg.downloads_directory = str(self.tmp_path / 'downloaded_files')
        self.assertIsInstance(
            self.cfg.downloads_directory,
            type(self.cfg_cls.downloads_directory)
        )
        # Timezone:
        self.cfg.tz = 'America/New_York'
        self.assertIsInstance(self.cfg.tz, tzinfo.DstTzInfo)
        # Dict:
        self.cfg.county_codes = str(json.dumps(
            {'UK': 'United Kingdom', 'KZ': 'Kazakhstan'}
        ))
        self.assertIsInstance(self.cfg.county_codes, dict)

    def test_independent_options_between_configs(self):
        config_1 = self.cfg_cls()
        config_1.service_ref = 'new_service'
        config_2 = self.cfg_cls()
        self.assertNotEqual(config_2.service_ref, config_1.service_ref)
