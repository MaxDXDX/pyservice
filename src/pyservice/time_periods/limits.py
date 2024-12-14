"""Limits for count per time period."""

from __future__ import annotations

import abc
import re
from datetime import datetime as dt
from typing import Any

import pydantic
import prettytable as pt

from pyservice.domain import base
from pyservice.text_tools import russian_words
from pyservice.time_periods import periods


class CountPerCalendarPeriodLimit(base.BaseFrozenModel):
    """Limit for <Count/Period> value."""

    limit: int | None
    period_type: periods.CalendarPeriodType | None = None
    is_calendarian: bool | None = None
    unit: russian_words.Unit = russian_words.Units.ITEM

    def model_post_init(self, __context: Any) -> None:
        if self.limit is None:
            assert self.period_type is None
            assert self.is_calendarian is None
        if self.limit == 0:
            assert self.period_type is None
            assert self.is_calendarian is None

    @property
    def is_real_limit(self) -> bool:
        if isinstance(self.limit, int) and self.limit > 0:
            return True
        return False

    @property
    def is_unlimited(self) -> bool:
        return self.limit == 0

    @property
    def is_disabled(self) -> bool:
        return self.limit is None

    @pydantic.computed_field
    @property
    def ref(self) -> str:
        if self.is_unlimited:
            return 'unlimited'
        elif self.is_disabled:
            return 'disabled'
        else:
            main = f'{self.limit}{self.unit.short_ref}-{self.period_type.ref}'
            if self.is_calendarian:
                main = f'{main}-cal'
            return main

    def get_reporting_period_for_moment(
            self, moment: dt) -> periods.Period | None:
        period_type = self.period_type
        if not period_type:
            return
        if self.is_calendarian:
            return period_type.get_calendarian_period_for_moment(moment)
        else:
            return period_type.get_period_from_provided_end(moment)

    @property
    def limit_value_as_human_text(self) -> str:
        if self.is_unlimited:
            return 'Без ограничений'
        if self.is_disabled:
            return 'Не доступно'
        return str(self.limit)

    def as_plain_text(self) -> str:
        if self.is_unlimited:
            return 'Без ограничений'
        if self.is_disabled:
            return 'Не доступно'
        count = self.limit
        period_factor = self.period_type.factor
        if period_factor == 1:
            period = self.period_type.russian_title.singular.nominative
        else:
            period = (f'{period_factor} '
                      f'{self.period_type.russian_title.plural.nominative}')
        return f'{count} шт. в {period}'

    def get_state(self,
                  control_moment: dt,
                  spent_count: CountFetcher | int | None
                  ) -> StateOfCountPerCalendarPeriodLimit:
        return StateOfCountPerCalendarPeriodLimit(
            object=self,
            control_moment=control_moment,
            spent_count=spent_count
        )

    @classmethod
    def build_from_ref(cls, ref: str) -> CountPerCalendarPeriodLimit:
        ref = ref.lower()
        if ref == 'unlimited':
            return CountPerCalendarPeriodLimit(limit=0)
        if ref == 'disabled':
            return CountPerCalendarPeriodLimit(limit=None)
        is_calendarian = '-cal' in ref
        ref = ref.replace('-cal', '')
        parts = ref.partition('-')
        limit_and_unit = parts[0]
        lim = int(re.findall(r'\d+', limit_and_unit)[0])
        unit_ref = limit_and_unit.replace(str(lim), '')
        period_type_ref = parts[2]
        period_type = periods.CalendarPeriodTypes.get_by_ref(period_type_ref)
        args = {
            'limit': lim,
            'period_type': period_type,
            'is_calendarian': is_calendarian
        }
        if unit_ref:
            unit = russian_words.Units.build_from_ref(unit_ref)
            assert unit
            args['unit'] = unit
        return CountPerCalendarPeriodLimit(**args)


class SetOfCountPerCalendarPeriodLimits(base.BaseModel, base.IdentityMixin):
    """Group of limits."""
    items: set[CountPerCalendarPeriodLimit]

    @property
    def size(self) -> int:
        return len(self.items)

    @property
    def single_unit_for_all_limits(self) -> russian_words.Unit | None:
        stack = set()
        for item in self.items:
            unit = item.unit
            stack.add(unit)
        if len(stack) == 1:
            return list(stack)[0]

    @property
    def is_has_real_limit(self) -> bool:
        for item in self.items:
            if item.is_real_limit:
                return True
        return False

    def combined_period(self, moment: dt) -> periods.Period | None:
        stack = []
        for limit in self.items:
            reporting_period = limit.get_reporting_period_for_moment(moment)
            if reporting_period:
                stack.append(reporting_period)
        if stack:
            return periods.combine_periods(stack)

    @classmethod
    def get_one_unlimited(cls) -> SetOfCountPerCalendarPeriodLimits:
        unlimited = CountPerCalendarPeriodLimits.UNLIMITED
        return SetOfCountPerCalendarPeriodLimits(items={unlimited, })

    @property
    def ref(self) -> str:
        all_refs = sorted([_.ref for _ in self.items])
        as_str = ','.join(all_refs)
        return f'{as_str}'

    @classmethod
    def build_from_ref(cls, ref: str) -> SetOfCountPerCalendarPeriodLimits:
        refs_for_items = ref.split(',')
        stack = set()
        for item_ref in refs_for_items:
            item = CountPerCalendarPeriodLimit.build_from_ref(item_ref)
            stack.add(item)
        return cls(items=stack)

    @property
    def _id(self):
        return self.ref

    def __hash__(self):
        return self._hash_of_id

    def __eq__(self, other):
        return self._eq_by_id(other)

    def get_state(self,
                  control_moment: dt,
                  spent_count: CountFetcher | int | None,
                  ) -> StateOfSetOfCountPerCalendarPeriodLimits:
        return StateOfSetOfCountPerCalendarPeriodLimits(
            object=self,
            control_moment=control_moment,
            spent_count=spent_count
        )


class CountPerCalendarPeriodLimits:
    """Some predefined limits."""

    DENIED = CountPerCalendarPeriodLimit(
        limit=None,
    )
    UNLIMITED = CountPerCalendarPeriodLimit(
        limit=0,
    )
    DAY_10_CAL = CountPerCalendarPeriodLimit(
        limit=10,
        period_type=periods.CalendarPeriodTypes.DAY,
        is_calendarian=True,
    )
    MONTH_100_CAL = CountPerCalendarPeriodLimit(
        limit=100,
        period_type=periods.CalendarPeriodTypes.MONTH,
        is_calendarian=True,
    )
    MONTH_150_CAL = CountPerCalendarPeriodLimit(
        limit=150,
        period_type=periods.CalendarPeriodTypes.MONTH,
        is_calendarian=True,
    )


class CountFetcher(abc.ABC):
    """Should return count for provided period."""

    def get_count_for_period(self, period: periods.Period = None) -> int:
        return self._get_count_for_period(period)

    @abc.abstractmethod
    def _get_count_for_period(self, period: periods.Period) -> int:
        raise NotImplementedError


class StateOfCountPerCalendarPeriodLimit(base.BaseModelWithArbitraryFields):
    """Summary about limit state."""

    object: CountPerCalendarPeriodLimit
    control_moment: dt
    spent_count: CountFetcher | int | None = pydantic.Field(
        default=None, exclude=True)


    @pydantic.computed_field
    @property
    def spent(self) -> int | None:
        if isinstance(self.spent_count, int):
            return self.spent_count
        else:
            if self.object.is_unlimited:
                return
            period = self.reporting_period
            if not period:
                return None
            return self.spent_count.get_count_for_period(period)

    @pydantic.computed_field
    @property
    def balance(self) -> int | None:
        if self.object.limit == 0:  # unlimited
            return None
        if self.object.limit is None:  # denied
            return 0
        else:
            return self.object.limit - self.spent

    @pydantic.computed_field
    @property
    def balance_as_percentage(self) -> int | None:
        if self.object.limit:
            v = self.balance / self.object.limit
            return round(v * 100)

    @pydantic.computed_field
    @property
    def spent_as_percentage(self) -> int | None:
        if self.object.limit:
            v = self.spent / self.object.limit
            return round(v * 100)

    @pydantic.computed_field
    @property
    def period(self) -> periods.CalendarPeriod | None:
        return self.object.get_reporting_period_for_moment(self.control_moment)

    @pydantic.computed_field
    @property
    def reporting_period(self) -> periods.Period | None:
        if self.object in [
            CountPerCalendarPeriodLimits.UNLIMITED,
            CountPerCalendarPeriodLimits.DENIED,
        ]:
            return None
        limit_period_type = self.object.period_type
        if self.object.is_calendarian:
            period = limit_period_type.get_calendarian_period_for_moment(
                self.control_moment)
        else:
            period = limit_period_type.get_period_from_provided_end(
                self.control_moment)
        return period

    def as_plain_text(self, dt_format: str = '%d.%m.%y %H:%M:%S (%Z)',
                      indent: int = 0):
        dt_as_text = self.control_moment.strftime(dt_format)
        rows = [f'Лимит: {self.object.as_plain_text()}']
        reporting_period = self.reporting_period
        if self.reporting_period:
            rows.append(f'Отчётный период: '
                        f'{reporting_period.as_plain_text(dt_format)}')
        rows.append(f'Состояние на: {dt_as_text}')
        if self.spent:
            rows.append(f'Израсходовано: {self.spent}')
        if isinstance(self.balance, int):
            if self.balance >= 0:
                rows.append(f'Доступно: {self.balance}')
            else:
                rows.append(f'Перерасход: {-1 * self.balance}')
        is_positive_balance = 'да' if self.is_positive_balance else 'нет'
        rows.append(f'Имеется доступный остаток (да/нет): '
                    f'{is_positive_balance}')
        if indent:
            # pylint: disable=W1405
            rows = [f'{" " * indent}{_}' for _ in rows]
        return '\n'.join(rows)

    def as_pretty_table(self) -> pt.PrettyTable:
        table = pt.PrettyTable(
            field_names=[
                'Лимит',
                'Единица измерения',
                'Период',
                'Отчётный период',
                'Учтено',
                'Остаток',
            ]
        )
        row = []
        row.append(self.object.limit_value_as_human_text)
        if self.object.is_real_limit:
            row.append(self.object.unit.singular.nominative)
            row.append(
                self.object.period_type.russian_title.singular.nominative)
            row.append(self.reporting_period.as_plain_text())
            row.append(f'{self.spent} ({self.spent_as_percentage}%)')
            row.append(f'{self.balance} ({self.balance_as_percentage}%)')
        else:
            row.extend(['', '', '', '' , ''])
        table.add_row(row)
        return table

    @pydantic.computed_field
    @property
    def is_positive_balance(self) -> bool:
        return self.object.is_unlimited or self.balance > 0


class StateOfSetOfCountPerCalendarPeriodLimits(
    base.BaseModelWithArbitraryFields):
    """State of the group of limits."""

    object: SetOfCountPerCalendarPeriodLimits
    control_moment: dt
    spent_count: CountFetcher | int | None = pydantic.Field(
        default=None, exclude=True)

    @pydantic.computed_field
    @property
    def state_of_limits(self) -> list[StateOfCountPerCalendarPeriodLimit]:
        stack = []
        for _ in self.object.items:
            state = _.get_state(self.control_moment, self.spent_count)
            stack.append(state)
        return stack

    @pydantic.computed_field
    @property
    def is_some_limit_has_expired(self) -> bool:
        for _ in self.state_of_limits:
            if not _.is_positive_balance:
                return True
        return False

    def as_plain_text(self, dt_format: str = '%d.%m.%y %H:%M:%S (%Z)'):
        rows = ['Состояние лимитов:']
        for _ in self.state_of_limits:
            rows.append(_.as_plain_text(dt_format, indent=2))
        return '\n'.join(rows)

    def as_pretty_table(self) -> pt.PrettyTable:
        all_states = self.state_of_limits
        assert len(all_states) > 0
        first_state = all_states[0]
        table = first_state.as_pretty_table()
        if len(all_states) > 1:
            for _ in all_states[1:]:
                t = _.as_pretty_table()
                table.add_rows(t.rows)
        return table
