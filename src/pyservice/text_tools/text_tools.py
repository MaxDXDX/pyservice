"""Text tools."""

import typing as t
import string
from re import sub
import random
from pathlib import Path
from uuid import UUID


current_dir = Path(__file__).parent
RANDOM_ENGLISH_WORDS = current_dir / 'random_english_words.txt'


def to_kebab(text: str) -> str:
    """Convert string to kebab-case form."""
    kebab_case = sub(r'(?<!^)(?=[A-Z])', '-', text).lower()
    kebab_case = sub(r'_', '-', kebab_case).lower()
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


def shrunk_text(text: str, limit: int, with_comment: bool = True,
                symblos: str = ' ...') -> str:
    """Shrink long strings and add dots."""
    assert limit > 0
    if not isinstance(text, str):
        return text
    text_length = len(text)

    if text_length <= 1:
        return text

    if limit == 1:
        return text[0]

    if text_length <= limit:
        return text

    while True:
        showed = text[:limit]
        hidden = text[limit:]
        slug = f'{symblos} and more {len(hidden)} chars' \
            if with_comment else symblos
        slug_size = len(slug)
        if slug_size < len(showed):
            text_showed = showed[:-1*slug_size]
            result = f'{text_showed}{slug}'
            return result
        elif len(slug) <= len(hidden):
            if with_comment:
                without_comment = shrunk_text(text, limit, with_comment=False)
                return without_comment
            else:
                with_arrow = shrunk_text(text, limit, with_comment=False,
                                         symblos='→')
                return with_arrow
            # limit -= 1
            # if limit == 0:
            #     return showed
        # else:
        #     result = f'{showed}{slug}'
        #     return result


def normalized_uuid(uuid: str | UUID) -> UUID:
    if isinstance(uuid, str):
        uuid = UUID(uuid)
        return uuid
    elif isinstance(uuid, UUID):
        return uuid
    else:
        raise ValueError


def get_all_keys(
        data: t.Dict[str, t.Any],
        parent_key: str = ''
) -> t.List[str]:
    keys = []

    for key, value in data.items():
        full_key = f'{parent_key}.{key}' if parent_key else key
        keys.append(full_key)

        if isinstance(value, dict):  # Recursively process nested dictionaries
            keys.extend(get_all_keys(value, full_key))
        elif isinstance(
            value, list):  # If value is a list, check for nested dictionaries
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    keys.extend(get_all_keys(item, f'{full_key}[{i}]'))

    return keys
