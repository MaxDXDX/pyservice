"""
Tests.
"""

from unittest import TestCase
from pyservice.text_tools import text_tools


class TextToolsTestCase(TestCase):
    """Text tools tests."""

    def test_convert_to_kebab(self):
        original = 'BackToTheFuture'
        expected = 'back-to-the-future'
        self.assertEqual(text_tools.to_kebab(original), expected)

    def test_convert_to_snake(self):
        original = 'BackToTheFuture'
        expected = 'back_to_the_future'
        self.assertEqual(
            text_tools.to_snake(original),
            expected
        )

        already_in_snake = 'back_to_the_future'
        self.assertEqual(
            text_tools.to_snake(already_in_snake),
            expected
        )
