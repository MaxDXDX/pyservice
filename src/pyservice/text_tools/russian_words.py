"""Russian words."""

from pyservice.domain.base import BaseModel


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


class WordCases(BaseModel):
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


class RussianWord(BaseModel):
    singular: WordCases
    plural: WordCases

    def form(self,
             case: str = RussianCases.nominative,
             number: str = Numbers.singular) -> str:
        cases: WordCases = getattr(self, number)
        case: str = getattr(cases, case)
        return case


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
