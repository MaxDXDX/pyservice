"""
Tests.
"""

import os

from unittest import TestCase
from pathlib import Path

from pyservice.pyconfig.pyconfig import AppConfig
from pyservice.pyconfig.pyconfig import default_app_config
from pyservice.pyconfig.pyconfig import default_microservice_config

current_path = Path(__file__).parent


class AppConfigTestCase(TestCase):
    """App config tests."""

    def test_simple_app_config(self) -> None:
        class SimpleConfig(AppConfig):
            service_ref: str = 'my_service'
        cfg = SimpleConfig(__file__)
        self.assertEqual(cfg.service_ref, 'my_service')

    def test_base_directories(self) -> None:
        cfg = default_app_config
        for attr in [
            'directory_for_app',
            'directory_for_place_app_directory',
            'root_module',
        ]:
            with self.subTest(attr=attr):
                path = getattr(cfg, attr)
                self.assertIsInstance(path, Path)
                self.assertTrue(path.is_dir())

        # for config in tests folder (not in src)
        # TODO: detect root module for tests configs

    def test_artefacts_directories(self) -> None:
        cfg = default_app_config
        data = cfg.directory_for_data
        tmp = cfg.directory_for_tmp
        logs = cfg.directory_for_logs
        self.assertTrue(data.is_dir())
        self.assertTrue(tmp.is_dir())
        self.assertTrue(logs.is_dir())

    def test_override_option_by_env(self) -> None:
        desired_value = 'Asia/Tokyo'
        os.environ['tz'] = desired_value

        class ConfigFromEnv(AppConfig):
            pass
        cfg = ConfigFromEnv(__file__)
        self.assertEqual(cfg.tz, desired_value)


class MicroserviceTestCase(TestCase):
    """Microservice config tests."""

    def test_microservice_config(self) -> None:
        cfg = default_microservice_config
        self.assertTrue(cfg.instance_tag)


#
# class OldPyConfigTestCase(TestCase):
#     """Config tests."""
#
#     tmp_path = current_path / 'tmp'
#
#     @classmethod
#     def remove_tmp_entities(cls):
#         try:
#             shutil.rmtree(cls.tmp_path)
#         except FileNotFoundError:
#             pass
#
#     @classmethod
#     def setUpClass(cls) -> None:
#         cls.remove_tmp_entities()
#         cls.tmp_path.mkdir(exist_ok=True)
#
#     @classmethod
#     def tearDownClass(cls) -> None:
#         cls.remove_tmp_entities()
#
#     def setUp(self) -> None:
#
#         class MyConfig(PyConfig):
#             service_ref = 'my_service'
#             api_hostname = 'awesome-api.com'
#             # parent_for_service_directory = '/tmp'
#
#             downloads_directory = self.tmp_path / 'my-downloads'
#             readme_file = self.tmp_path / 'readme.txt'
#             tz = timezone('Europe/Moscow')
#             county_codes = {
#                 'RU': 'Russia',
#                 'US': 'USA',
#             }
#         try:
#             MyConfig.downloads_directory.rmdir()
#         except FileNotFoundError:
#             pass
#         self.cfg = MyConfig(config_file=__file__)
#         self.cfg_cls = MyConfig
#         self.cfg.erase_tmp_directory()
#
#     def tearDown(self) -> None:
#         self.cfg.erase_tmp_directory()
#
#     # pylint: disable=C0301
#     def test_if_parent_for_artefact_not_provided_artefacts_is_in_project(self):
#         class MyConfig(PyConfig):
#             service_ref = 'test-service'
#
#         config = MyConfig(__file__)
#         artefacts = config.artefacts_directory
#         artefacts.is_dir()
#         project_dir = config.project_directory
#         self.assertEqual(artefacts.parent, project_dir)
#
#     def test_detect_project_root_and_its_parent(self):
#         # pylint: disable=W0612
#         project_dir_parent, project_dir, root_module = (
#             self.cfg.base_project_directories)
#         self.assertIsInstance(project_dir_parent, Path)
#         self.assertIsInstance(project_dir, Path)
#         dirs_of_project = files.get_list_of_directories_in_directory(
#             project_dir, mask='*'
#         )
#         dirs_of_project_names = [_.name for _ in dirs_of_project]
#         self.assertIn('src', dirs_of_project_names)
#         self.assertIn('tests', dirs_of_project_names)
#         dirs_of_project_parent = files.get_list_of_directories_in_directory(
#             project_dir_parent, mask='*'
#         )
#         self.assertIn(project_dir, dirs_of_project_parent)
#
#     def test_get_config_options(self):
#         keys = self.cfg.all_keys
#         self.assertIsInstance(keys, list)
#         for _ in keys:
#             self.assertIsInstance(_, str)
#             getattr(self.cfg, _)
#
#     def test_check_names_of_directory_and_file_attributes(self):
#         class CorrectConfig(PyConfig):
#             service_ref = 'rest-api'
#             my_directory = self.tmp_path / 'my-directory'
#             my_file = self.tmp_path / 'my-file'
#
#         class IncorrectConfig(PyConfig):
#             service_ref = 'rest-api'
#             my_path = self.tmp_path / 'my-directory'
#             config = self.tmp_path / 'my-config-file'
#
#         CorrectConfig()
#         with self.assertRaises(ValueError):
#             IncorrectConfig()
#
#     # def test_create_path_attribute_on_first_access_only_for_dir(self):
#     #     # path not created if read it from class (not from instance)
#     #     self.assertIsInstance(self.cfg_cls.downloads_directory, Path)
#     #     self.assertFalse(
#     #         self.cfg_cls.downloads_directory.is_dir(),
#     #         msg=str(self.cfg_cls.downloads_directory),
#     #     )
#     #     # path created after reading it from config:
#     #     download_path = self.cfg.downloads_directory
#     #     self.assertTrue(download_path.is_dir())
#     #
#     #     file = self.cfg.readme_file
#     #     self.assertFalse(file.is_dir())
#
#     def test_using_env_vars(self):
#         env_keys = self.cfg.keys_from_environment
#         keys = self.cfg.all_keys
#         self.assertIsInstance(keys, list)
#         self.assertEqual(len(env_keys), len(keys))
#         for key in keys:
#             env_key = self.cfg.convert_key_to_env_key(key)
#             restored = self.cfg.restore_key_from_env_key(env_key)
#             self.assertEqual(key, restored)
#             value_from_cfg = getattr(self.cfg, key)
#             value_from_cfg_class = getattr(self.cfg_cls, key)
#             if key != 'parent_for_service_directory':
#                 self.assertIsInstance(
#                     value_from_cfg,
#                     type(value_from_cfg_class),
#                     msg=f'error for: {key}'
#                 )
#
#     def test_can_set_any_option_from_string(self):
#         # Path:
#         self.cfg.downloads_directory = str(self.tmp_path / 'downloaded_files')
#         self.assertIsInstance(
#             self.cfg.downloads_directory,
#             type(self.cfg_cls.downloads_directory)
#         )
#         # Timezone:
#         self.cfg.tz = 'America/New_York'
#         self.assertIsInstance(self.cfg.tz, tzinfo.DstTzInfo)
#         # Dict:
#         self.cfg.county_codes = str(json.dumps(
#             {'UK': 'United Kingdom', 'KZ': 'Kazakhstan'}
#         ))
#         self.assertIsInstance(self.cfg.county_codes, dict)
#
#     def test_independent_options_between_configs(self):
#         config_1 = self.cfg_cls()
#         config_1.service_ref = 'new_service'
#         config_2 = self.cfg_cls()
#         self.assertNotEqual(config_2.service_ref, config_1.service_ref)
#
#     def test_creating_artefacts_directories(self):
#         artefacts = self.cfg.artefacts_directory
#         self.assertTrue(artefacts.is_dir())
#
#     def test_string_representation(self):
#         as_str = str(self.cfg)
#         print(as_str)
