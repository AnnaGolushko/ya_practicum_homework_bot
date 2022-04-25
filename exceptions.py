"""practicum_domashka_bot.exceptions.

This module contains the set of Yandex Practikum Domashka bot exceptions.
"""


class IncorrectTokens(Exception):
    """При запуске программы получены неверные токены."""


class ConnectionError(Exception):
    """Не удалось установить соединение с API."""


class ResponseStatusCodeError(Exception):
    """Ответ на запрос к API вернул ошибку 4xx или 5xx."""


class HomeworksNotInResponse(Exception):
    """Список домашних работ homeworks не найден в http-ответе."""


class CurrentDateNotInResponse(Exception):
    """Метка даты-времени current_date не найдена в http-ответе."""


class UnknownHomeworkStatus(Exception):
    """Неизвестный статус домашней работы.

    В ответе API получен неизвестный статус
    проверки домашней работы.
    """


class BotSendingMessageError(Exception):
    """Ошибка при отправке сообщения в телеграмм-бот."""
