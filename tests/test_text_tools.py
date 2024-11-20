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

    def test_convert_to_kebab_2(self):
        original = 'back_to_the_future'
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

    def test_shrink_1(self):
        long_text = \
            '|123456_10|123456_20|123456_30|123456_40|123456_50|123456_60'
        limit = 30
        shrunk = text_tools.shrunk_text(long_text, limit)
        self.assertEqual(len(shrunk), limit)

    def test_shrink_2(self):
        long_text = \
            '|123456_10|123456_20|123456_30|123456_40|123456_50|123456_60'
        limit = 20
        shrunk = text_tools.shrunk_text(long_text, limit)
        self.assertEqual(len(shrunk), limit)

    def test_shrink_3(self):
        long_text = \
            '|123456_10|123456_20|123456_30|123456_40|123456_50|123456_60'
        limit = 4
        shrunk = text_tools.shrunk_text(long_text, limit)
        self.assertEqual(len(shrunk), limit)

    def test_shrink_4(self):
        long_text = \
            '|123456_10|123456_20|123456_30|123456_40|123456_50|123456_60'
        limit = 2
        shrunk = text_tools.shrunk_text(long_text, limit)
        self.assertEqual(len(shrunk), limit)

    def test_shrink_5(self):
        long_text = \
            '|123456_10|123456_20|123456_30|123456_40|123456_50|123456_60'
        limit = 1
        shrunk = text_tools.shrunk_text(long_text, limit)
        self.assertEqual(len(shrunk), limit)

    def test_shrink_6(self):
        long_text = \
            '|123456_10|123456_20|123456_30|123456_40|123456_50|123456_60'
        limit = 50
        shrunk = text_tools.shrunk_text(long_text, limit)
        self.assertEqual(len(shrunk), limit)
