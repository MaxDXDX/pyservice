from pathlib import Path
from unittest import TestCase

from {{ app.app_name }} import manager


class InitialTestCase(TestCase):

    def test_manager_in_test_mode(self):
        is_in_test_mode = manager.test_mode
        self.assertTrue(is_in_test_mode is True)

    def test_manager_detect_dirs(self):
        parent_for_app_dir, app_dir, app_root_module = (
            manager.base_project_directories)
        self.assertIsInstance(parent_for_app_dir, Path)
        self.assertIsInstance(app_dir, Path)
        self.assertIsInstance(app_root_module, Path)