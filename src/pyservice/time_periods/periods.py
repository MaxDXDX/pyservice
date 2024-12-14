"""Time periods."""


from __future__ import annotations
from typing import Any
import re
import abc
from datetime import datetime as dt
from datetime import timedelta as td

import pytz

from pyservice.domain import base
from pyservice.mixins import IdentityMixin
from pyservice.text_tools.russian_words import RussianWord, TimePeriods


MOSCOW_TIMEZONE = pytz.timezone('Europe/Moscow')
DEFAULT_TIMEZONE = MOSCOW_TIMEZONE


def get_moscow_now():
    return dt.now(tz=MOSCOW_TIMEZONE)


def get_localed_now(tz):
    return dt.now(tz=tz)


def get_localed_dt(original, tz):
    if isinstance(original, str):
        original = dt.fromisoformat(original)
    try:
        return original.astimezone(tz=tz)
    except AttributeError:
        return original


def get_moscow_dt(original):
    tz = MOSCOW_TIMEZONE
    if isinstance(original, str):
        original = dt.fromisoformat(original)
    try:
        return original.astimezone(tz=tz)
    except AttributeError:
        return original


def ref_for_dt(moment: dt) -> str:
    return moment.isoformat()


def dt_from_ref(
        ref: str,
        tz,
        force_end_of_implicit_dt=False,
) -> dt:
    is_no_time_provided = 'T' not in ref or ':' not in ref
    naive = dt.fromisoformat(ref)
    if tz:
        localed = get_localed_dt(naive, tz)
        if is_no_time_provided and force_end_of_implicit_dt:
            localed = localed.replace(
                hour=23, minute=59, second=59, microsecond=999999)
        return localed
    else:
        raise ValueError('Time zone must be provided!')


class Period(base.BaseModel, IdentityMixin):
    """Arbitrary time period."""

    start: dt | None = None
    end: dt | None = None

    @property
    def _id(self):
        return self.start, self.end

    def __eq__(self, other):
        return self._eq_by_id(other)

    @property
    def ref(self) -> str:
        if self.is_infinity:
            return 'infinity'
        if self.is_only_to:
            return f'to-{ref_for_dt(self.end)}'
        if self.is_only_from:
            return f'from-{ref_for_dt(self.start)}'
        if self.is_closed:
            return f'from-{ref_for_dt(self.start)}-to-{ref_for_dt(self.end)}'

    @classmethod
    def build_from_ref(cls, ref: str, tz=None) -> Period:
        if ref == 'infinity':
            return Period()
        if 'to-' in ref and 'from-' not in ref:
            end_ref = ref.replace('to-', '')
            end = dt_from_ref(end_ref, tz, force_end_of_implicit_dt=True)
            return Period(end=end)
        if 'to-' not in ref and 'from-' in ref:
            start_ref = ref.replace('from-', '')
            start = dt_from_ref(start_ref, tz)
            return Period(start=start)
        if 'to-' in ref and 'from-' in ref:
            start_ref = re.search('from-(.*?)-to-', ref).group(1)
            end_ref = re.search('-to-(.*?)$', ref).group(1)
            start = dt_from_ref(start_ref, tz)
            end = dt_from_ref(end_ref, tz, force_end_of_implicit_dt=True)
            return Period(start=start, end=end)
        raise ValueError(f'invalid ref for Period: {ref}')

    @property
    def is_future(self):
        return self.point_is_before_period(dt.now())

    @property
    def is_past(self):
        return self.point_is_after_period(dt.now())

    def point_is_before_period(self, point: dt) -> bool:
        return self.start is not None and point < self.start

    def point_is_after_period(self, point: dt) -> bool:
        return self.end is not None and point > self.end

    def point_is_in_period(self, point: dt) -> bool:
        return (not self.point_is_before_period(point) and
                not self.point_is_after_period(point))

    @property
    def is_infinity(self) -> bool:
        return self.start is None and self.end is None

    @property
    def is_closed(self) -> bool:
        return self.start is not None and self.end is not None

    @property
    def is_only_to(self) -> bool:
        return self.start is None and self.end is not None

    @property
    def is_only_from(self) -> bool:
        return self.start is not None and self.end is None

    @classmethod
    def get_infinity(cls):
        return cls()

    @staticmethod
    def get_infinity_period():
        return Period()

    def as_plain_text(
            self,
            dt_format: str = '%d.%m.%y %H:%M:%S',
            use_dash_if_closed: bool = True,
    ):
        tz_of_end_as_text = self.end.strftime('%Z') if self.end else None
        tz_of_start_as_text = self.start.strftime('%Z') if self.start else None
        if not self.start and not self.end:
            return 'бессрочно'
        if not self.start:
            end = f'{self.end.strftime(dt_format)} {tz_of_end_as_text}'
            return f'по {end}'
        if not self.end:
            start = f'{self.start.strftime(dt_format)} {tz_of_start_as_text}'
            return f'с {start}'
        start = self.start.strftime(dt_format)
        end = self.end.strftime(dt_format)
        assert tz_of_end_as_text == tz_of_start_as_text
        if use_dash_if_closed:
            result = f'{start} - {end}'
        else:
            result = f'с {start} по {end}'
        return f'{result} ({tz_of_start_as_text})'

    @property
    def as_tuple(self) -> str:
        return (self.start, self.end)

    def short_text(self):
        if not self.start and not self.end:
            return 'бессрочно'
        if not self.start:
            end = self.end.strftime('%d.%m.%Y %H:%M:%S')
            return f'по {end}'
        if not self.end:
            start = self.start.strftime('%d.%m.%Y %H:%M:%S')
            return f'с {start}'
        start = self.start.strftime('%d.%m.%Y %H:%M:%S')
        end = self.end.strftime('%d.%m.%Y %H:%M:%S')
        return f'{start} - {end}'

    # def __eq__(self, other: Period) -> bool:
    #     if self.start != other.start:
    #         return False
    #     if self.end != other.end:
    #         return False
    #     return True


class CalendarPeriod(Period):
    """Period with calendarian duration (like hour, day, week etc.)"""

    period_type: CalendarPeriodType


class CalendarianCalendarPeriod(CalendarPeriod):
    pass


class NonCalendarianCalendarPeriod(CalendarPeriod):
    pass


class CalendarPeriodType(base.BaseModel, base.IdentityMixin):
    """Arbitrary time period."""

    ref_base: str
    russian_title: RussianWord
    factor: int = 1

    @property
    def _id(self):
        return self.ref, self.factor

    def __hash__(self):
        return self._hash_of_id

    def __eq__(self, other):
        return self._eq_by_id(other)

    @property
    def ref(self) -> str:
        if self.factor == 1:
            return self.ref_base
        else:
            return f'{self.ref_base}_x{self.factor}'

    @abc.abstractmethod
    def for_user_text(self, is_calendar=True):
        raise NotImplementedError

    def get_start_of_current_calendarian_period(
            self, test_now: dt = None, tz: Any = None) -> dt:
        now = test_now if test_now else dt.now(
            tz=tz if tz else DEFAULT_TIMEZONE)
        return self.get_start_of_calendarian_period_by_inner_dt_point(now)

    def get_end_of_current_calendarian_period(
            self, test_now: dt = None, tz: Any = None) -> dt:
        now = test_now if test_now else dt.now(
            tz=tz if tz else DEFAULT_TIMEZONE)
        return self.get_end_of_calendarian_period_by_inner_dt_point(now)

    def get_calendarian_period_for_moment(
            self, moment: dt) -> CalendarianCalendarPeriod:
        return CalendarianCalendarPeriod(
            start=self.get_start_of_calendarian_period_by_inner_dt_point(
                moment),
            end=self.get_end_of_current_calendarian_period(moment),
            period_type=self
        )

    def get_current_calendarian_period(self) -> CalendarianCalendarPeriod:
        return CalendarianCalendarPeriod(
            start=self.get_start_of_current_calendarian_period(),
            end=self.get_end_of_current_calendarian_period(),
            period_type=self
        )

    def get_period_from_provided_start(self, start: dt) -> CalendarPeriod:
        end = self.get_end_of_period_from_start(start)
        return CalendarPeriod(
            start=start,
            end=end,
            period_type=self,
        )

    def get_period_from_provided_end(self, end: dt) -> CalendarPeriod:
        start = self.get_start_of_period_from_end(end)
        return CalendarPeriod(
            start=start,
            end=end,
            period_type=self,
        )

    @abc.abstractmethod
    def get_start_of_calendarian_period_by_inner_dt_point(self, point: dt):
        raise NotImplementedError

    @abc.abstractmethod
    def get_end_of_calendarian_period_by_inner_dt_point(self, point: dt):
        raise NotImplementedError

    @abc.abstractmethod
    def get_end_of_period_from_start(self, start: dt):
        """Return end of period if that period starts at provided point."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_start_of_period_from_end(self, end: dt):
        """Return start of period if that period ends at provided point."""
        raise NotImplementedError

    def get_next_start_from_current_start(self, start: dt):
        """Return next start if provided datetime is start."""
        end = self.get_end_of_period_from_start(start)
        return end + td(microseconds=1)

    def get_current_period_from_global_start(
            self, global_start: dt, test_now: dt = None, tz: Any = None,
    ) -> CalendarPeriod:
        now = test_now if test_now else dt.now(
            tz=tz if tz else DEFAULT_TIMEZONE)
        if global_start > now:
            raise ValueError('Provided start point is in future')
        start = global_start
        while True:
            next_start = self.get_next_start_from_current_start(start)
            if next_start > now:
                end = self.get_end_of_period_from_start(start)
                period = CalendarPeriod(
                    start=start,
                    end=end,
                    period_type=self,
                )
                return period
            else:
                start = next_start


class Year(CalendarPeriodType):
    """The year."""

    ref_base: str = 'year'
    russian_title: RussianWord = TimePeriods.YEAR

    def get_start_of_calendarian_period_by_inner_dt_point(self, point: dt):
        return point.replace(month=1, day=1, hour=0, minute=0, second=0,
                             microsecond=0)

    def get_end_of_calendarian_period_by_inner_dt_point(self, point: dt):
        return point.replace(month=12, day=31, hour=23, minute=59, second=59,
                             microsecond=999999)

    def get_end_of_period_from_start(self, start: dt):
        if start.month == 2 and start.day == 29:
            same_moment_in_next_year = start.replace(
                year=start.year + 1,
                day=28,
            )
        else:
            same_moment_in_next_year = start.replace(
                year=start.year + 1,
            )
        return same_moment_in_next_year - td(microseconds=1)

    def get_start_of_period_from_end(self, end: dt):
        if end.month == 2 and end.day == 29:
            same_moment_in_previous_year = end.replace(
                year=end.year - 1,
                day=28,
            )
        else:
            same_moment_in_previous_year = end.replace(
                year=end.year - 1
            )
        return same_moment_in_previous_year + td(microseconds=1)

    def for_user_text(self, is_calendar=True):
        return {
            'nominative': 'календарный год' if is_calendar else 'год',
            'accusative': 'в календарный год' if is_calendar else 'в год',
        }


class Month(CalendarPeriodType):
    """The month."""

    ref_base: str = 'month'
    russian_title: RussianWord = TimePeriods.MONTH

    def get_start_of_calendarian_period_by_inner_dt_point(self, point: dt):
        return point.replace(day=1, hour=0, minute=0, second=0,
                             microsecond=0)

    def get_end_of_calendarian_period_by_inner_dt_point(self, point: dt):
        day_in_next_month = point.replace(day=28) + td(days=4)
        first_day_in_next_month = day_in_next_month.replace(day=1)
        last_day = first_day_in_next_month - td(days=1)
        return last_day.replace(hour=23, minute=59, second=59,
                                microsecond=999999)

    def get_end_of_period_from_start(self, start: dt):
        some_day_in_next_month = start.replace(day=28) + td(days=4)
        same_moment_in_next_month = some_day_in_next_month.replace(
            day=start.day,
            hour=start.hour,
            minute=start.minute,
            second=start.second,
            microsecond=start.microsecond,
        )
        return same_moment_in_next_month - td(microseconds=1)

    def get_start_of_period_from_end(self, end: dt):
        first_day_of_current_month = end.replace(day=1)
        last_day_of_previous_month = first_day_of_current_month - td(days=1)
        same_moment_in_previous_month = last_day_of_previous_month.replace(
            day=end.day,
            hour=end.hour,
            minute=end.minute,
            second=end.second,
            microsecond=end.microsecond,
        )
        return same_moment_in_previous_month + td(microseconds=1)

    def for_user_text(self, is_calendar=True):
        return {
            'nominative': 'календарный месяц' if is_calendar else 'месяц',
            'accusative': 'в календарный месяц' if is_calendar else 'в месяц',
        }


class Week(CalendarPeriodType):
    """The week."""

    ref_base: str = 'week'
    russian_title: RussianWord = TimePeriods.WEEK

    def get_start_of_calendarian_period_by_inner_dt_point(self, point: dt):
        weekday = point.weekday()
        start = point - td(days=weekday)
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        return start

    def get_end_of_calendarian_period_by_inner_dt_point(self, point: dt):
        weekday = point.weekday()
        end = point + td(days=6 - weekday)
        end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
        return end

    def get_end_of_period_from_start(self, start: dt) -> dt:
        return start + td(days=7) - td(microseconds=1)

    def get_start_of_period_from_end(self, end: dt) -> dt:
        return end - td(days=7) + td(microseconds=1)

    def for_user_text(self, is_calendar=True):
        return {
            'nominative':
                'календарная неделя' if is_calendar else 'неделя',
            'accusative':
                'в календарную неделю' if is_calendar else 'в неделю',
        }


class Day(CalendarPeriodType):
    """Day (24 hours)."""

    ref_base: str = 'day'
    russian_title: RussianWord = TimePeriods.DAY24

    def get_start_of_calendarian_period_by_inner_dt_point(self, point: dt):
        return point.replace(hour=0, minute=0, second=0, microsecond=0)

    def get_end_of_calendarian_period_by_inner_dt_point(self, point: dt):
        return point.replace(hour=23, minute=59, second=59, microsecond=999999)

    def get_end_of_period_from_start(self, start: dt):
        return start + td(days=1) - td(microseconds=1)

    def get_start_of_period_from_end(self, end: dt):
        return end - td(days=1) + td(microseconds=1)

    def for_user_text(self, is_calendar=True):
        return {
            'nominative': 'календарные сутки' if is_calendar else 'сутки',
            'accusative': 'в календарные сутки' if is_calendar else 'в сутки',
        }


class CalendarPeriodTypes:
    """Predefined periods."""

    YEAR = Year()
    MONTH = Month()
    WEEK = Week()
    DAY = Day()
    DAY_X2 = Day(factor=2)
    DAY_X10 = Day(factor=10)

    @classmethod
    def all(cls) -> list[CalendarPeriodType]:
        return [
            cls.YEAR,
            cls.MONTH,
            cls.WEEK,
            cls.DAY
        ]

    @classmethod
    def get_by_ref(cls, ref) -> CalendarPeriodType:
        found = [_ for _ in cls.all() if _.ref == ref]
        if found:
            return found[0]


infinity_period = Period.get_infinity_period()


def combine_periods(periods: set[Period] | list[Period]) -> Period:
    all_starts = sorted(list({_.start for _ in periods}))
    all_ends = sorted(list({_.end for _ in periods}))
    return Period(
        start=all_starts[0],
        end=all_ends[-1],
    )
