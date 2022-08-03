import logging
import os
import sys
import time as time

import requests
import telegram
from dotenv import load_dotenv

import exceptions

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TOKENS = (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def send_message(bot, message):
    """Отправление сообщения в Telegram."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        logger.error('Сообщение не удалось отправить.')
        raise exceptions.FailSendMessageTg(error)
    logger.info('Сообщение отправлено.')


def get_api_answer(current_timestamp):
    """Запрос к эндпоинту сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        logger.error(
            f'Эндпоинт не доступен: {ENDPOINT}'
        )
        raise exceptions.EndpointNotAvailable(error)
    if response.status_code != 200:
        raise requests.exceptions.HTTPError
    logger.info('Эндпоинт доступен.')
    return response.json()


def check_response(response):
    """Проверка API на корректность и доступность ключа."""
    if response['homeworks'] is None:
        err_row = 'Список по ключу "homeworks" пуст.'
        logger.error(err_row)
        raise exceptions.EmptyList(err_row)
    if isinstance(response['homeworks'], dict):
        raise TypeError
    logger.info('Список с домашней работой найден по ключу "homeworks".')
    return response['homeworks']


def parse_status(homework):
    """Анализ статуса домашней работы."""
    if not homework:
        raise exceptions.ExceptionApi('Словарь homeworks пуст')
    if 'homework_name' not in homework:
        raise KeyError('Ключ homework_name отсутствует')
    if 'status' not in homework:
        raise KeyError('Ключ status отсутствует')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_STATUSES:
        raise KeyError(f'{homework_status} отсутствует в словаре verdicts')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка доступности переменных окружения."""
    err_row = 'Переменная окружения {} is None.'
    if PRACTICUM_TOKEN is None:
        logger.critical(err_row.format(PRACTICUM_TOKEN))
        return False
    elif TELEGRAM_TOKEN is None:
        logger.critical(err_row.format(TELEGRAM_TOKEN))
        return False
    elif TELEGRAM_CHAT_ID is None:
        logger.critical(err_row.format(TELEGRAM_CHAT_ID))
        return False
    else:
        logger.info('Все переменные найдены.')
        return True


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        exit()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            message = parse_status(homework[0])
            send_message(bot, message)
            current_timestamp = response.get('current_date', current_timestamp)
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
