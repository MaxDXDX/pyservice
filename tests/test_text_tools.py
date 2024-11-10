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

    def test_get_random_english_word(self):
        word = text_tools.get_random_english_word()
        self.assertIsInstance(word, str)
        self.assertTrue(len(word) > 0)

    def test_get_random_english_words(self):
        as_one_string = text_tools.get_random_english_words(number=10)
        self.assertEqual(len(as_one_string.split(' ')), 10)
