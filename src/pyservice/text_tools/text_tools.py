"""Text tools."""

import string
from re import sub
import random
from pathlib import Path

current_dir = Path(__file__).parent
RANDOM_ENGLISH_WORDS =  current_dir / 'random_english_words.txt'


def to_kebab(text: str) -> str:
    """Convert string to kebab-case form."""
    kebab_case = sub(r'(?<!^)(?=[A-Z])', '-', text).lower()
    return kebab_case


def to_snake(text: str) -> str:
    """Convert string from camelCase or PascalCase to snake_case form."""
    snake_case = sub(r'(?<!^)(?=[A-Z])', '_', text).lower()
    return snake_case


def get_random_string(length: int = None) -> str:
    if not length:
        length = random.randint(1, 10)
    random_chars = ''.join(
        [random.choice(string.ascii_letters) for i in range(length)])
    return random_chars


def get_random_english_word() -> str:
    with open(RANDOM_ENGLISH_WORDS, 'r', encoding='UTF-8') as f:
        lines = f.readlines()
    words = [_.replace('\n', '') for _ in lines]
    return random.choice(words)


def get_random_english_words(
        number: int = 3, as_list: bool = False) -> str | list:
    words = [get_random_english_word() for _ in range(number)]
    if as_list:
        return words
    return ' '.join(words)
