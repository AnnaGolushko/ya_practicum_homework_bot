import logging
import os

import requests
import time

import telegram
from dotenv import load_dotenv

import exceptions

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
stream_logging = logging.StreamHandler()
stream_logging.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s, %(levelname)s, %(message)s')
stream_logging.setFormatter(formatter)
logger.addHandler(stream_logging)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправка в телеграмм сообщения о статусе домашней работы."""
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    logger.info(f'Бот отправил сообщение: {message}')


def get_api_answer(current_timestamp):
    """Функция запроса к API сервиса Практикум.Домашка.
    Возвращает ответ JSON с преобразованием к типам данных Python.
    """
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}

    homework_statuses = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if homework_statuses.status_code != 200:
        raise requests.ConnectionError(
            (f'Эндпоинт {ENDPOINT} недоступен. '
             f'Код ответа API: {homework_statuses.status_code}')
        )

    return homework_statuses.json()


def check_response(response):
    """Функция проверки, что ответ API соответствует ожиданиям."""
    if not isinstance(response, dict):
        response = response[0]

    if len(response) == 0:
        raise exceptions.EmptyDictInAPIResponse(
            'В ответ на запрос API вернул пустой словарь response'
        )

    homeworks = response.get('homeworks')
    if isinstance(homeworks, dict):
        raise exceptions.UnexpectedHomeworksTypeDict(
            'В ответе API объект homeworks имеет тип Dict, а не List'
        )

    if 'homeworks' not in response.keys():
        raise exceptions.HomeworksNotInResponse(
            'Ответ API не вернул список домашних работ'
        )

    return response.get('homeworks')


def parse_status(homework):
    """Проверка статуса домашней работы и подготовка сообщения."""
    if 'homework_name' and 'status' not in homework.keys():
        raise exceptions.HomeworkNotContainKeys(
            'В словаре homework не найдены искомые ключи'
        )

    homework_name = homework['homework_name']
    homework_status = homework['status']

    if homework_status not in HOMEWORK_STATUSES.keys():
        logger.debug(
            ('В ответе API получен новый статус '
             f'домашней работы: {homework_status}')
        )
        raise exceptions.UnknownHomeworkStatus(
            (f'В ответе API получен неизвестный статус {homework_status}'
             'проверки домашней работы.')
        )

    for status in HOMEWORK_STATUSES.keys():
        if homework_status == status:
            verdict = HOMEWORK_STATUSES[status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка, что в программу переданы необходимые токены."""
    is_exist = True
    if (
        PRACTICUM_TOKEN is None
        or TELEGRAM_CHAT_ID is None
        or TELEGRAM_TOKEN is None
    ):
        logger.critical('Одна или более переменных окружения не определены')
        is_exist = False
    return is_exist


def main():
    """Основная логика работы бота."""
    result = check_tokens()
    if result is True:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        current_timestamp = int(time.time())

        current_status = None

        while True:
            try:
                response = get_api_answer(current_timestamp)
                homeworks = check_response(response)
                current_timestamp = int(time.time())
                time.sleep(RETRY_TIME)

            except Exception as error:
                message = f'Сбой в работе программы: {error}'
                logger.error(message)
                bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
                logger.info(f'Бот отправил сообщение: {message}')
                time.sleep(RETRY_TIME)
            else:
                try:
                    homework = homeworks[0]
                    if current_status != homework['status']:
                        parse_message = parse_status(homework)
                        send_message(bot, parse_message)
                        current_status = homework['status']
                except Exception as error:
                    message = f'Сбой в работе программы: {error}'
                    logger.error(message)
                    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
                    logger.info(f'Бот отправил сообщение: {message}')
    else:
        raise exceptions.IncorrectTokens(
            'Работа программы остановлена. Получены некорректные токены'
        )


if __name__ == '__main__':
    main()
