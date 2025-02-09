"""Class for dealing with time duration."""


from datetime import timedelta
from datetime import datetime as dt

from pyservice.domain.base import BaseModel


class Duration(BaseModel):
    """Time duration with pretty text presentation."""
    start: dt
    end: dt

    @property
    def delta(self) -> timedelta:
        return self.end - self.start

    @property
    def pretty_seconds(self) -> str:
        seconds = self.delta.total_seconds()
        return f'{seconds} sec.'

    @property
    def as_pretty_string(self) -> str:
        # TODO: refactor for microseconds, milliseconds and others units ...
        return self.pretty_seconds
