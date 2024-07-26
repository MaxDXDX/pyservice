"""
Tests.
"""
import unittest
from unittest import TestCase
from pyservice import log_tools
from pyservice.manager.manager import default_app_manager

log = default_app_manager.get_logger_for_pyfile(__file__)


class Calculator:
    @log_tools.logged_method(logger=log)
    def multiply(self, a: int, b: int) -> int:
        return a * b


@unittest.skip('TODO: works only isolated from other tests?')
class LoggingTestCase(TestCase):
    """Logging tests."""

    def setUp(self) -> None:
        log.debug('LoggingTestCase test started...')

    def tearDown(self) -> None:
        log.debug('LoggingTestCase test done!')

    def test_logging_function(self):
        log_tools.clean_file_for_logger(log)
        self.assertFalse(log_tools.get_content_of_log_file_of_logger(log))

        @log_tools.logged(logger=log)
        def summa(a, b):
            return a + b

        summa(2, 3)
        log_content = log_tools.get_content_of_log_file_of_logger(log)
        self.assertIn('summa', log_content)

    def test_logging_method(self):
        log_tools.clean_file_for_logger(log)
        self.assertFalse(log_tools.get_content_of_log_file_of_logger(log))

        calc = Calculator()

        calc.multiply(5, 6)
