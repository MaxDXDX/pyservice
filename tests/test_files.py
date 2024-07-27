"""
Tests.
"""

from unittest import TestCase
from pathlib import Path

from pyservice.files import files
from pyservice import pyconfig
from pyservice.manager.manager import AppManager

current_path = Path(__file__).parent


class FilesTestCase(TestCase):
    """Files tests."""

    def setUp(self) -> None:

        self.cfg = pyconfig.AppConfig()
        self.mng = AppManager(self.cfg, __file__)
        self.mng.erase_tmp_directory()

    def tearDown(self) -> None:
        self.mng.erase_tmp_directory()

    def test_detailed_directory(self):
        project_directory = Path(__file__).parent.parent
        detailed_directory = files.DetailedDirectory(project_directory)
        self.assertTrue(detailed_directory.entities.total_entities)
        total_size = detailed_directory.entities.total_size_in_bytes
        self.assertIsInstance(total_size, int)
        self.assertGreater(total_size, 0)
        without_nested = files.DetailedDirectory(project_directory, mask='*')
        self.assertTrue(
            detailed_directory.entities.total_entities >
            without_nested.entities.total_entities
        )
        empty_dir = self.mng.directory_for_tmp / 'empty-dir'
        empty_dir.mkdir()
        detailed = files.DetailedDirectory(empty_dir)
        self.assertEqual(detailed.entities.total_entities, 0)
        file_in_dir = empty_dir / 'my-file'
        file_in_dir.touch()
        detailed.parse()
        self.assertEqual(detailed.entities.total_size_in_bytes, 0)
        self.assertEqual(detailed.entities.total_entities, 1)

    def test_tar(self):
        test_file = self.mng.create_text_file_in_tmp_directory(
            content='my-content'
        )
        tar_file = files.compress_file_or_directory_by_tar(
            self.mng.directory_for_tmp,
            output_dir_or_file=self.mng.directory_for_tmp)
        test_file.unlink()
        self.assertFalse(test_file.is_file())
        files.extract_data_from_tar_archive(
            tar_archive=tar_file,
            ignore_single_root_dir=True,
        )
        self.assertTrue(test_file.is_file())

