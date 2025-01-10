"""
Tests.
"""
import time
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
        # self.mng.erase_tmp_directory()
        pass

    def test_get_list_of_files_in_directories(self):
        directory = self.mng.directory_for_tmp
        self.mng.create_text_file_in_tmp_directory()
        file_list = files.get_list_of_files_in_directory(directory=directory)
        self.assertIsInstance(file_list, (list, set))

    def test_detailed_directory(self):
        project_directory = Path(__file__).parent.parent
        detailed_directory = files.DetailedDirectory(
            directory=project_directory)
        self.assertTrue(detailed_directory.entities.total_entities)
        total_size = detailed_directory.entities.total_size_in_bytes
        self.assertIsInstance(total_size, int)
        self.assertGreater(total_size, 0)
        without_nested = files.DetailedDirectory(
            directory=project_directory, mask='*')
        self.assertTrue(
            detailed_directory.entities.total_entities >
            without_nested.entities.total_entities
        )
        empty_dir = self.mng.directory_for_tmp / 'empty-dir'
        empty_dir.mkdir()
        detailed = files.DetailedDirectory(directory=empty_dir)
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

    def test_md5(self):
        test_file = self.mng.create_text_file_in_tmp_directory(
            content='some-content', filename='md5check.txt'
        )
        md5 = files.md5(test_file)
        self.assertEqual(md5, 'ad60407c083b4ecc372614b8fcd9f305')

        differ = self.mng.create_text_file_in_tmp_directory(
            content='some-contenT', filename='md5check2.txt'
        )
        md5_of_differ = files.md5(differ)
        self.assertNotEqual(md5_of_differ, 'ad60407c083b4ecc372614b8fcd9f305')

    def test_remove_old_files(self):
        self.mng.erase_tmp_directory()
        tmp_dir = self.mng.directory_for_tmp
        self.assertEqual(files.get_number_of_files_in_directory(tmp_dir), 0)
        creating_order = [
            3,
            5,
            1,
            4,
            2,
        ]
        number_of_files = len(creating_order)

        created_files = []
        for i in creating_order:
            time.sleep(0.1)
            f = self.mng.create_text_file_in_tmp_directory(
                content=f'this is content of file #{i}',
                filename=f'file-{i}.txt',
            )
            created_files.append(f)
        sorted_by_dt = list(reversed(created_files))

        self.assertEqual(
            files.get_number_of_files_in_directory(tmp_dir), number_of_files)

        with self.assertRaises(ValueError):
            files.delete_old_files_from_directory(
                directory=tmp_dir)
        count_limit = 2
        deleted_files = files.delete_old_files_from_directory(
            directory=tmp_dir, count_limit=count_limit,
        )
        expected = sorted_by_dt[count_limit:]
        self.assertEqual(len(deleted_files), number_of_files - count_limit)
        self.assertListEqual(expected, deleted_files)



