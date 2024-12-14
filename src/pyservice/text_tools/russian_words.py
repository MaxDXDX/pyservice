"""Russian words."""

from __future__ import annotations
from pyservice.domain.base import BaseFrozenModel


class RussianCases:
    nominative: str = 'nominative'
    genitive: str = 'genitive'
    dative: str = 'dative'
    accusative: str = 'accusative'
    instrumental: str = 'instrumental'
    prepositional: str = 'prepositional'


class Numbers:
    singular: str = 'singular'
    plural: str = 'plural'


class WordCases(BaseFrozenModel):
    """Russian cases for words.

    nominative - Именительный (кто, что)
    genitive - Родительный (нет кого, чего)
    dative - Дательный (дам кому, чему)
    accusative - Винительный (вижу кого, что)
    instrumental - Творительный (доволен кем, чем)
    prepositional - Предложный (думаю о ком, о чём)
    """

    nominative: str
    genitive: str = None
    dative: str = None
    accusative: str = None
    instrumental: str = None
    prepositional: str = None

    def __str__(self):
        return self.nominative


class RussianWord(BaseFrozenModel):
    singular: WordCases
    plural: WordCases

    def form(self,
             case: str = RussianCases.nominative,
             number: str = Numbers.singular) -> str:
        cases: WordCases = getattr(self, number)
        case: str = getattr(cases, case)
        return case

class Unit(RussianWord):
    ref: str
    short_ref: str
    abbreviation: str = None
    short_abbreviation: str = None


class TimePeriods:
    """Basic calendar periods."""

    HOUR = RussianWord(
        singular=WordCases(
            nominative='час',
            genitive='часа',
            dative='часу',
            accusative='час',
            instrumental='часом',
            prepositional='часе ',
        ),
        plural=WordCases(
            nominative='часы',
            genitive='часов',
            dative='часам',
            accusative='часы',
            instrumental='часами',
            prepositional='часах',
        )
    )
    DAY = RussianWord(
        singular=WordCases(
            nominative='день',
            genitive='дня',
            dative='дню',
            accusative='день',
            instrumental='днём',
            prepositional='дне',
        ),
        plural=WordCases(
            nominative='дни',
            genitive='дней',
            dative='дням',
            accusative='дни',
            instrumental='днями',
            prepositional='днях',
        )
    )
    DAY24 = RussianWord(
        singular=WordCases(
            nominative='сутки',
            genitive='суток',
            dative='суткам',
            accusative='сутки',
            instrumental='сутками',
            prepositional='сутках',
        ),
        plural=WordCases(
            nominative='сутки',
            genitive='суток',
            dative='суткам',
            accusative='сутки',
            instrumental='сутками',
            prepositional='сутках',
        )
    )
    WEEK = RussianWord(
        singular=WordCases(
            nominative='неделя',
            genitive='недели',
            dative='неделе',
            accusative='неделю',
            instrumental='неделей',
            prepositional='неделе',
        ),
        plural=WordCases(
            nominative='недели',
            genitive='недель',
            dative='неделям',
            accusative='недели',
            instrumental='неделями',
            prepositional='неделях',
        )
    )
    MONTH = RussianWord(
        singular=WordCases(
            nominative='месяц',
            genitive='месяца',
            dative='месяцу',
            accusative='месяц',
            instrumental='месяцем',
            prepositional='месяце',
        ),
        plural=WordCases(
            nominative='месяцы',
            genitive='месяцев',
            dative='месяцам',
            accusative='месяцы',
            instrumental='месяцами',
            prepositional='месяцах',
        )
    )
    YEAR = RussianWord(
        singular=WordCases(
            nominative='год',
            genitive='года',
            dative='году',
            accusative='год',
            instrumental='годом',
            prepositional='годе',
        ),
        plural=WordCases(
            nominative='годы',
            genitive='лет',
            dative='годам',
            accusative='годы',
            instrumental='годами',
            prepositional='годах',
        )
    )

class Units:
    """Some commonly used units."""

    ITEM = Unit(
        singular=WordCases(
            nominative='штука',
            genitive='штуки',
            dative='штуке',
            accusative='штуку',
            instrumental='штукой',
            prepositional='штуке',
        ),
        plural=WordCases(
            nominative='штуки',
            genitive='штук',
            dative='штукам',
            accusative='штуки',
            instrumental='штуками',
            prepositional='штуках',
        ),
        abbreviation='шт.',
        ref='item',
        short_ref='i',
    )
    CONVENTIONAL_UNIT = Unit(
        singular=WordCases(
            nominative='условная единица',
            genitive='условной единицы',
            dative='условной единице',
            accusative='условную единицу',
            instrumental='условной единицей',
            prepositional='условной единице',
        ),
        plural=WordCases(
            nominative='условные единицы',
            genitive='условных единиц',
            dative='условным единицам',
            accusative='условные единицы',
            instrumental='условными единицами',
            prepositional='условных единицах',
        ),
        abbreviation='усл.ед.',
        short_abbreviation='уе',
        ref='cu',
        short_ref='cu',
    )
    REPORT = Unit(
        singular=WordCases(
            nominative='отчёт',
            genitive='отчёта',
            dative='отчёту',
            accusative='отчёт',
            instrumental='отчётом',
            prepositional='отчёте',
        ),
        plural=WordCases(
            nominative='отчёты',
            genitive='отчётов',
            dative='отчётам',
            accusative='отчёты',
            instrumental='отчётами',
            prepositional='отчётах',
        ),
        ref='report',
        short_ref='r',
        abbreviation='отч.',
        short_abbreviation='отч.'
    )
    all = [
        ITEM,
        CONVENTIONAL_UNIT,
        REPORT
    ]

    @classmethod
    def build_from_ref(cls, ref: str) -> Unit:
        for _ in cls.all:
            if ref in (_.ref, _.short_ref):
                return _
