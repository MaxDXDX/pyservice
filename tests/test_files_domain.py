"""
Tests.
"""

from unittest import TestCase
from pathlib import Path

from pyservice.domain import files as files_domain
from pyservice.files import files as files_utils

from pyservice.manager.manager import get_default_app_manager

current_path = Path(__file__).parent


class FilesDomainTestCase(TestCase):
    """Files models tests."""

    def setUp(self):
        self.mng = get_default_app_manager()
        self.mng.erase_tmp_directory()

    def test_files_domain(self):
        number_of_files = 5

        local_files_items = set()

        for _ in range(number_of_files):
            local_path = files_utils.create_text_file_in_directory(
                directory=self.mng.directory_for_tmp,
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

    def test_move_file(self):
        file = files_domain.LocalFile.Examples.random_txt(
            directory=self.mng.directory_for_tmp
        )
        self.assertTrue(file.is_exist)
        previous_location = str(file.fullpath)

        file.move_to_directory(
            directory=self.mng.directory_for_tests,
            new_filename='file-in-new-location.txt',
            exist_ok=True
        )

        self.assertFalse(Path(previous_location).is_file())
        self.assertTrue(file.is_exist)


        file_2 = files_domain.LocalFile.Examples.random_txt(
            directory=self.mng.directory_for_tmp
        )

        with self.assertRaises(FileExistsError):
            file_2.move_to_directory(
                directory=self.mng.directory_for_tests,
                new_filename='file-in-new-location.txt',
                exist_ok=False
            )

        self.assertTrue(file_2.is_exist)

    def test_get_by_regex(self):
        # Create test files
        filenames = [
            'alpha.txt',
            'beta.txt',
            'gamma.log',
            'delta.txt',
            'epsilon.log',
        ]
        local_files_items = set()

        for name in filenames:
            path = files_utils.create_text_file_in_directory(
                directory=self.mng.directory_for_tmp,
                content='test content',
                filename=name
            )
            local_files_items.add(files_domain.LocalFile(fullpath=path))

        local_files = files_domain.LocalFiles(items=local_files_items)

        # No match
        no_match = local_files.get_by_regex(r'^zeta')
        self.assertIsNone(no_match)

        # Single match
        single_match = local_files.get_by_regex(r'^beta\.txt$')
        self.assertIsInstance(single_match, files_domain.LocalFile)
        self.assertEqual(single_match.fullpath.name, 'beta.txt')

        # Multiple matches
        multi_match = local_files.get_by_regex(r'\.log$')
        self.assertIsInstance(multi_match, list)
        self.assertEqual(len(multi_match), 2)
        self.assertTrue(all(
            isinstance(f, files_domain.LocalFile) for f in multi_match))
        self.assertSetEqual(
            set(f.fullpath.name for f in multi_match),
            {'gamma.log', 'epsilon.log'}
        )
