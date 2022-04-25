import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

import exceptions

load_dotenv()

logger = logging.getLogger(__name__)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправка в телеграмм сообщения о статусе домашней работы."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info(f'Бот отправил сообщение: {message}')
    except Exception as error:
        raise exceptions.BotSendingMessageError(
            f'Сбой при отправке сообщения в телеграмм: {error}'
        )


def get_api_answer(current_timestamp):
    """Функция запроса к API сервиса Практикум.Домашка.
    Возвращает ответ JSON с преобразованием к типам данных Python.
    """
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    logger.info(f'Бот начал обращение к API: {ENDPOINT}')

    try:
        homework_statuses = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params
        )
    except Exception as error:
        raise exceptions.ConnectionError(
            (f'Эндпоинт {ENDPOINT} недоступен.'
             'Не удалось установить соединение.')
        ) from error

    if homework_statuses.status_code != HTTPStatus.OK:
        raise exceptions.ResponseStatusCodeError(
            (f'Эндпоинт {ENDPOINT} недоступен. '
             f'Код ответа API: {homework_statuses.status_code}')
        )

    return homework_statuses.json()


def check_response(response):
    """Функция проверки, что ответ API соответствует ожиданиям."""
    if not isinstance(response, dict):
        raise TypeError('Ответ API имеет тип отличный от Dict')
    homeworks = response.get('homeworks')

    if not isinstance(homeworks, list):
        raise TypeError(
            'В ответе API объект homeworks имеет тип отличный от List'
        )

    if 'homeworks' not in response:
        raise exceptions.HomeworksNotInResponse(
            'Ответ API не вернул список домашних работ'
        )

    if 'current_date' not in response:
        raise exceptions.CurrentDateNotInResponse(
            'Ответ API не содержит информацию о метке даты-времени'
        )
    return response.get('homeworks')


def parse_status(homework):
    """Проверка статуса домашней работы и подготовка сообщения."""
    if 'homework_name' not in homework:
        raise KeyError(
            'В словаре homework не найден ключ homework_name'
        )
    if 'status' not in homework:
        raise KeyError(
            'В словаре homework не найден ключ status'
        )

    homework_name = homework['homework_name']
    homework_status = homework['status']

    if homework_status not in HOMEWORK_VERDICTS:
        logger.debug(
            ('В ответе API получен новый статус '
             f'домашней работы: {homework_status}')
        )
        raise exceptions.UnknownHomeworkStatus(
            (f'В ответе API получен неизвестный статус {homework_status}'
             'проверки домашней работы.')
        )
    verdict = HOMEWORK_VERDICTS[homework_status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка, что в программу переданы необходимые токены."""
    return all([PRACTICUM_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN])


def main():
    """Основная логика работы бота."""
    result = check_tokens()
    if not result:
        logger.critical(
            'Одна или более переменных окружения не определены. '
            'Работа программы остановлена.'
        )
        sys.exit(1)

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    current_status = None
    current_error_status = None

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            current_timestamp = int(time.time())
            if not homeworks:
                logger.info(
                    'Ответ API практикума вернул '
                    'пустой список домашних работ'
                )
                if current_status != 'Новых домашних работ для проверки нет':
                    current_status = 'Новых домашних работ для проверки нет'
                    send_message(bot, current_status)
            else:
                homework = homeworks[0]
            if current_status != homework['status']:
                parse_message = parse_status(homework)
                send_message(bot, parse_message)
                current_status = homework['status']
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            occured_error_type = type(error).__name__
            bot_error_type = exceptions.BotSendingMessageError.__name__
            if (
                occured_error_type != bot_error_type
                and current_error_status != occured_error_type
            ):
                send_message(bot, message)
                current_error_status = occured_error_type
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logger.setLevel(logging.DEBUG)
    stream_logging = logging.StreamHandler()
    stream_logging.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        ('%(asctime)s, '
         '%(levelname)s, '
         '%(funcName)s, '
         '%(lineno)d, '
         '%(message)s')
    )
    stream_logging.setFormatter(formatter)
    logger.addHandler(stream_logging)

    main()
