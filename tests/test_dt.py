"""
Tests.
"""
from typing import Any
from unittest import TestCase
from dataclasses import dataclass
from datetime import datetime as dt
from datetime import timedelta as td

from prettytable import PrettyTable

from pyservice.time_periods import periods, limits
from pyservice.text_tools.russian_words import Unit, Units


class DateAndTimeTestCase(TestCase):
    """Date and Time tools tests."""

    def test_get_widest_period_from_several(self):
        oldest = dt.fromisoformat('2024-01-23T12:00:00+03:00')
        youngest = dt.fromisoformat('2024-01-28T08:00:00+03:00')
        p1 = periods.Period(
            start=dt.fromisoformat('2024-01-25T10:00:00+03:00'),
            end=dt.fromisoformat('2024-01-25T23:00:00+03:00'),
        )
        p2 = periods.Period(
            start=oldest,  # oldest
            end=dt.fromisoformat('2024-01-25T21:00:00+03:00'),
        )
        p3 = periods.Period(
            start=dt.fromisoformat('2024-01-25T22:00:00+03:00'),
            end=youngest,  # the most yang
        )
        widest = periods.combine_periods([p1, p2, p3])
        self.assertEqual(widest, periods.Period(start=oldest, end=youngest))

    def test_each_period_type_can_return_current_calendarian_period(self):
        @dataclass
        class Case:
            ref: str
            calendarian_start: str
            calendarian_end: str
            test_now: str = '2024-01-25T12:30:12.987654+03:00'

        cases = [
            Case('day',
                 '2024-01-25T00:00:00+03:00',
                 '2024-01-25T23:59:59.999999+03:00'
                 ),
            Case('week',
                 '2024-01-22T00:00:00+03:00',
                 '2024-01-28T23:59:59.999999+03:00'
                 ),
            Case('month',
                 '2024-01-01T00:00:00+03:00',
                 '2024-01-31T23:59:59.999999+03:00'
                 ),
            Case('year',
                 '2024-01-01T00:00:00+03:00',
                 '2024-12-31T23:59:59.999999+03:00'
                 ),
        ]
        for case in cases:
            now = periods.get_moscow_dt(case.test_now)
            period_type = periods.CalendarPeriodTypes.get_by_ref(case.ref)
            start = period_type.get_start_of_current_calendarian_period(now)
            end = period_type.get_end_of_current_calendarian_period(now)
            self.assertEqual(start.isoformat(), case.calendarian_start)
            self.assertEqual(end.isoformat(), case.calendarian_end)
            period = period_type.get_current_calendarian_period()
            self.assertIsInstance(period, periods.CalendarPeriod)

    def test_each_period_type_can_return_start_and_end_from_provided_dt(self):

        @dataclass
        class Case:
            ref: str
            start: str
            end: str
            moment: str = '2024-02-27T12:00:00.000000+03:00'

        cases = [
            Case('day',
                 '2024-02-26T12:00:00.000001+03:00',
                 '2024-02-28T11:59:59.999999+03:00'
                 ),
            Case('week',
                 '2024-02-20T12:00:00.000001+03:00',
                 '2024-03-05T11:59:59.999999+03:00'
                 ),
            Case('month',
                 '2024-01-27T12:00:00.000001+03:00',
                 '2024-03-27T11:59:59.999999+03:00'
                 ),
            Case('year',
                 '2023-02-27T12:00:00.000001+03:00',
                 '2025-02-27T11:59:59.999999+03:00',
                 ),
            Case('year',
                 '2023-02-28T12:00:00.000001+03:00',
                 '2025-02-28T11:59:59.999999+03:00',
                 '2024-02-29T12:00:00.000000+03:00',
                 ),
        ]

        for case in cases:
            moment = periods.get_moscow_dt(case.moment)
            period_type = periods.CalendarPeriodTypes.get_by_ref(case.ref)
            start = period_type.get_start_of_period_from_end(moment)
            end = period_type.get_end_of_period_from_start(moment)
            self.assertEqual(start.isoformat(), case.start)
            self.assertEqual(end.isoformat(), case.end)

    def test_each_period_type_can_return_current_period_from_global_start(self):
        @dataclass
        class Case:
            ref: str
            start: str
            end: str
            global_start: str = '2022-08-19T12:00:00.000000+03:00'
            test_now: str = '2024-11-29T20:36:20.123456+03:00'

        cases = [
            Case('day',
                 '2024-11-29T12:00:00+03:00',
                 '2024-11-30T11:59:59.999999+03:00'
                 ),
            Case('month',
                 '2024-11-19T12:00:00+03:00',
                 '2024-12-19T11:59:59.999999+03:00'
                 ),
        ]

        for case in cases:
            period_type = periods.CalendarPeriodTypes.get_by_ref(case.ref)
            global_start = periods.get_moscow_dt(case.global_start)
            test_now = periods.get_moscow_dt(case.test_now)
            period = period_type.get_current_period_from_global_start(
                global_start=global_start, test_now=test_now
            )
            self.assertEqual(period.start.isoformat(), case.start)
            self.assertEqual(period.end.isoformat(), case.end)

    def test_each_calendar_period_can_be_found_by_ref(self):
        for calendar_period in periods.CalendarPeriodTypes.all():
            ref = calendar_period.ref
            self.assertEqual(
                periods.CalendarPeriodTypes.get_by_ref(ref).ref, ref)

    def test_each_calendar_period_has_text_form(self):
        for calendar_period in periods.CalendarPeriodTypes.all():
            p = calendar_period
            self.assertIsInstance(p.for_user_text(), dict)
            self.assertIsInstance(p.for_user_text().get('nominative'), str)
            self.assertIsInstance(p.for_user_text().get('accusative'), str)

    def test_period_identity(self):
        start = dt.fromisoformat('2021-02-01')
        end = dt.fromisoformat('2021-02-28 23:59:59.999999')
        start = periods.get_localed_dt(start, tz=periods.MOSCOW_TIMEZONE)
        end = periods.get_localed_dt(end, tz=periods.MOSCOW_TIMEZONE)
        # end = periods.get_moscow_dt('2021-02-28T23:59:59.999999')
        print('start:', start)
        print('end:', end)
        p1 = periods.Period(start=start, end=end)
        p1_clone = periods.Period(start=start, end=end)
        p2 = periods.Period(start=start.replace(second=2), end=end)
        self.assertEqual(p1, p1_clone)
        self.assertNotEqual(p2, p1)
        # pylint: disable=C0301
        as_calendarian = (periods.CalendarPeriodTypes.MONTH.get_calendarian_period_for_moment(
            start + td(days=10)
        ))
        print('as-c', as_calendarian.start, as_calendarian.end)
        print('p1', p1.start, p1.end)
        print('p1c-c', p1_clone.start, p1_clone.end)
        self.assertEqual(as_calendarian, p1_clone)


class LimitsTestCase(TestCase):
    """Test for Count/Period limits."""

    def test_limit_identity(self):
        limit = limits.CountPerCalendarPeriodLimit(
            limit=10,
            period_type=periods.CalendarPeriodTypes.DAY,
            is_calendarian=True,
        )
        clone = limits.CountPerCalendarPeriodLimit(
            limit=10,
            period_type=periods.CalendarPeriodTypes.DAY,
            is_calendarian=True,
        )
        self.assertEqual(limit, clone)
        self.assertEqual(len({limit, clone}), 1)

        other = limits.CountPerCalendarPeriodLimit(
            limit=11,
            period_type=periods.CalendarPeriodTypes.DAY,
            is_calendarian=True,
        )
        self.assertNotEqual(limit, other)
        self.assertEqual(len({limit, other}), 2)

    def test_build_limit_from_ref(self):
        period_types = periods.CalendarPeriodTypes

        @dataclass
        class Case:
            ref: str
            limit: int
            unit: Unit
            period_type: periods.CalendarPeriodType | None
            is_calendarian: bool | None

        cases = [
            Case('10-day-cal', 10, Units.ITEM, period_types.DAY, True),
            Case('10i-day-cal', 10, Units.ITEM, period_types.DAY, True),
            Case('100-month', 100, Units.ITEM, period_types.MONTH, False),
            Case('100r-month', 100, Units.REPORT, period_types.MONTH, False),
            Case('unlimited', 0, Units.ITEM, None, None),
        ]
        for case in cases:
            lim = limits.CountPerCalendarPeriodLimit.build_from_ref(case.ref)
            self.assertEqual(lim.limit, case.limit)
            self.assertEqual(lim.unit, case.unit)
            self.assertEqual(lim.period_type, case.period_type)
            self.assertEqual(lim.is_calendarian, case.is_calendarian)

    def test_get_widest_period_for_set_of_limits(self):
        set_of_limits = limits.SetOfCountPerCalendarPeriodLimits(
            items={
                limits.CountPerCalendarPeriodLimits.DAY_10_CAL,
                limits.CountPerCalendarPeriodLimits.MONTH_100_CAL,
            }
        )
        now = periods.get_moscow_now()
        widest = set_of_limits.combined_period(now)
        self.assertIsInstance(widest, periods.Period)

    def test_detect_if_set_of_limits_has_real_limits(self):
        with_real_limits = limits.SetOfCountPerCalendarPeriodLimits(
            items={
                limits.CountPerCalendarPeriodLimits.DAY_10_CAL,
                limits.CountPerCalendarPeriodLimits.MONTH_100_CAL,
            }
        )
        self.assertTrue(with_real_limits.is_has_real_limit is True)
        without_real_limits = limits.SetOfCountPerCalendarPeriodLimits(
            items={
                limits.CountPerCalendarPeriodLimits.UNLIMITED,
                limits.CountPerCalendarPeriodLimits.DENIED,
            }
        )
        self.assertTrue(without_real_limits.is_has_real_limit is False)

    def test_get_state_of_limit(self):
        class FakeFetcher(limits.CountFetcher):
            # pylint: disable=W0613
            def _get_count_for_period(self, period: periods.Period) -> int:
                return 4

        @dataclass
        class Case:
            limit: limits.CountPerCalendarPeriodLimit
            expected_spent: int | None
            expected_spent_percentage: int | None
            expected_balance: int | None
            expected_balance_percentage: int | None
            expected_period: tuple[str, str] | None
            test_moment: str = '2024-11-29T20:36:20.123456+03:00'
            tz: Any = periods.MOSCOW_TIMEZONE
            fetcher: limits.CountFetcher = FakeFetcher()

        cases = [
            Case(
                limit=limits.CountPerCalendarPeriodLimits.DAY_10_CAL,
                expected_spent=4,
                expected_spent_percentage=40,
                expected_balance=6,
                expected_balance_percentage=60,
                expected_period=('2024-11-29T00:00:00+03:00',
                                 '2024-11-29T23:59:59.999999+03:00'),
            ),
            Case(
                limit=limits.CountPerCalendarPeriodLimits.UNLIMITED,
                expected_spent=None,
                expected_spent_percentage=None,
                expected_balance=None,
                expected_balance_percentage=None,
                expected_period=None,
            ),
        ]

        for case in cases:
            state = case.limit.get_state(
                control_moment=periods.get_moscow_dt(case.test_moment),
                spent_count=case.fetcher,
            )
            self.assertEqual(state.spent, case.expected_spent)
            self.assertEqual(state.spent_as_percentage,
                             case.expected_spent_percentage)
            self.assertEqual(state.balance, case.expected_balance)
            self.assertEqual(state.balance_as_percentage,
                             case.expected_balance_percentage)
            self.assertEqual(state.object, case.limit)
            if case.expected_period is not None:
                self.assertEqual(state.reporting_period.start.isoformat(),
                                 case.expected_period[0])
                self.assertEqual(state.reporting_period.end.isoformat(),
                                 case.expected_period[1])
            else:
                self.assertEqual(state.reporting_period, case.expected_period)
            self.assertIsInstance(state.as_plain_text(), str)
            self.assertIsInstance(state.as_pretty_table(), PrettyTable)
            self.assertIsInstance(state.serialized(), dict)

    def test_get_state_for_set_of_limits(self):
        set_of_limits = limits.SetOfCountPerCalendarPeriodLimits(
            items={
                limits.CountPerCalendarPeriodLimits.DAY_10_CAL,
                limits.CountPerCalendarPeriodLimits.MONTH_100_CAL,
            }
        )
        control_moment = periods.get_moscow_now()

        good_state = set_of_limits.get_state(
            control_moment=control_moment,
            spent_count=4,
        )
        self.assertTrue(good_state.is_some_limit_has_expired is False)
        self.assertIsInstance(good_state.serialized(), dict)
        # print(good_state.as_plain_text())

        bad_state = set_of_limits.get_state(
            control_moment=control_moment,
            spent_count=12,
        )
        self.assertTrue(bad_state.is_some_limit_has_expired is True)
        # print(bad_state.as_plain_text())
        self.assertIsInstance(bad_state.serialized(), dict)
        # print(bad_state.serialized())

        # with count fetcher (ignored in serialization):
        class FakeFetcher(limits.CountFetcher):
            # pylint: disable=W0613
            def _get_count_for_period(self, period: periods.Period) -> int:
                return 4
        fetcher = FakeFetcher()
        state_by_fetcher = set_of_limits.get_state(
            control_moment=control_moment,
            spent_count=fetcher,
        )
        self.assertIsInstance(state_by_fetcher.serialized(), dict)
        all_states = [good_state, bad_state, state_by_fetcher]
        for _ in all_states:
            table = _.as_pretty_table()
            self.assertIsInstance(table, PrettyTable)


