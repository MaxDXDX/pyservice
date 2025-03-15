"""Useful class mixins."""

import typing as t

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

    def __hash__(self):
        return self._hash_of_id

    # if not works - add next to your model:
    def __eq__(self, other):
        return self._eq_by_id(other)


class SequenceMixin:
    """Make a class suitable for storing list or set of items."""

    items: list | set

    @property
    def size(self) -> int:
        if not self.items:
            return 0
        return len(self.items)

    @property
    def is_empty(self) -> bool:
        return self.size == 0

    def intersection_with_another(self, another: t.Any) -> t.Self:
        if not isinstance(self, type(another)):
            raise ValueError(
                'both sequences must be of the same type to get intersection')
        common_items = set()
        for item in another.items:
            if item in self.items:
                common_items.add(item)
        if isinstance(self.items, list):
            return type(self)(items=list(common_items))
        elif isinstance(self.items, set):
            return type(self)(items=common_items)

    def has_intersection_with_another(self, another: t.Any) -> bool:
        return self.intersection_with_another(another).size > 0
