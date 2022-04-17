"""practicum_domashka_bot.exceptions.

This module contains the set of Yandex Practikum Domashka bot exceptions.
"""


class IncorrectTokens(Exception):
    """При запуске программы получены неверные токены."""


class UnexpectedAPIResponseType(Exception):
    """Объект response имеет некорректный тип (ожидается Dict)."""


class EmptyDictInAPIResponse(Exception):
    """В ответ на запрос API вернул пустой словарь response."""


class UnexpectedHomeworksTypeDict(Exception):
    """В ответе API объект homeworks имеет тип Dict, а не List."""


class HomeworksNotInResponse(Exception):
    """Список домашних работ homeworks не найден в http-ответе."""


class HomeworkNotContainKeys(Exception):
    """В словаре homework не найдены искомые ключи."""


class UnknownHomeworkStatus(Exception):
    """Неизвестный статус домашней работы.

    В ответе API получен неизвестный статус
    проверки домашней работы.
    """
