"""Case conversation tools."""


from re import sub


def to_kebab(text: str) -> str:
    """Convert string to kebab-case form."""
    kebab_case = sub(r'(?<!^)(?=[A-Z])', '-', text).lower()
    return kebab_case
