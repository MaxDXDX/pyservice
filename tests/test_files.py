"""
Tests.
"""

from unittest import TestCase
from pathlib import Path

from pyservice.files import files
from pyservice import pyconfig

current_path = Path(__file__).parent


class PyConfigTestCase(TestCase):
    """Config tests."""

    def setUp(self) -> None:
        class MyConfig(pyconfig.PyConfig):
            service_ref = 'test-service'
            downloads_directory = Path('/tmp')

        self.cfg = MyConfig(__file__)
        self.cfg_cls = MyConfig
        self.cfg.erase_tmp_directory()

    def tearDown(self) -> None:
        self.cfg.erase_tmp_directory()

    def test_tar(self):
        test_file = self.cfg.create_text_file_in_tmp_directory(
            content='my-content'
        )
        tar_file = files.compress_file_or_directory_by_tar(
            self.cfg.directory_for_tmp,
            output_dir_or_file=self.cfg.directory_for_tmp)
        test_file.unlink()
        self.assertFalse(test_file.is_file())
        files.extract_data_from_tar_archive(
            tar_archive=tar_file,
            ignore_single_root_dir=True,
        )
        self.assertTrue(test_file.is_file())

