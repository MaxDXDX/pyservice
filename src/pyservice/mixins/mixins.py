"""Useful class mixins."""

from pyservice.text_tools.text_tools import to_kebab


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


class IdentityMixin:
    """Identity functionality."""

    @property
    def _hash_of_id(self):
        return hash(self._id)

    def _eq_by_id(self, other) -> bool:
        try:
            # pylint: disable=W0212
            return self._id == other._id
        except AttributeError:
            return False

    @property
    def _id(self):
        raise NotImplementedError

    # if not works - add next two methods to your model:
    def __hash__(self):
        return self._hash_of_id
    def __eq__(self, other):
        return self._eq_by_id(other)
