"""Useful class mixins."""

from pyservice.text_tools import to_kebab


class KebabRefMixin:
    """Make auto ref property."""

    @property
    def ref(self) -> str:
        return to_kebab(str(type(self).__name__))

    def __eq__(self, other):
        try:
            return self.ref == other.ref
        except AttributeError:
            return False

    def __hash__(self):
        return hash(self.ref)

