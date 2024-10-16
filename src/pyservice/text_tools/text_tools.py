"""Case conversation tools."""


from re import sub


def to_kebab(text: str) -> str:
    """Convert string to kebab-case form."""
    kebab_case = sub(r'(?<!^)(?=[A-Z])', '-', text).lower()
    return kebab_case


def to_snake(text: str) -> str:
    """Convert string from camelCase or PascalCase to snake_case form."""
    snake_case = sub(r'(?<!^)(?=[A-Z])', '_', text).lower()
    return snake_case
