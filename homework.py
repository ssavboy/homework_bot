import logging
import os
import sys
import time as time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

import exceptions

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)


def send_message(bot, message):
    """Отправление сообщения в Telegram."""
    logger.info('Начало отправки сообщения.')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.error.NetworkError as err:
        raise exceptions.NotForReference(err)
    else:
        logger.info('Сообщение отправлено.')


def get_api_answer(current_timestamp):
    """Запрос к эндпоинту сервиса."""
    timestamp = current_timestamp or int(time.time())
    arguments = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': {'from_date': timestamp},
    }
    try:
        logger.info('Запрос к API.')
        response = requests.get(**arguments)
        if response.status_code != HTTPStatus.OK:
            raise exceptions.WrongResponseCode(
                ('Ошибка в ответе от API. '
                 'status_code: {status_code}, '
                 'endpoint: {url}, '
                 'headers: {headers}, '
                 'params: {params}.'.format(response.status_code, **arguments))
            )
        logger.info('Эндпоинт доступен.')
        return response.json()
    except Exception as err:
        raise ConnectionError(
            ('Ошибка подключения {err}. '
             'endpoint: {url}, '
             'headers: {headers}, '
             'params: {params}.'.format(err, **arguments))
        )


def check_response(response):
    """Проверка API на корректность и доступность ключа."""
    logger.info('Начало проверки response.')
    if not isinstance(response, dict):
        raise TypeError(response)
    if not response['homeworks']:
        raise exceptions.EmptyAPIResponse('Список с домашкой пуст.')
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise KeyError
    return homeworks


def parse_status(homework):
    """Анализ статуса домашней работы."""
    logger.info('Проверка статуса домашки.')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if not homework_name:
        raise KeyError(homework_name)
    if homework_status not in VERDICTS:
        raise ValueError(f'{homework_status} отсутствует в словаре verdicts')
    return ('Изменился статус проверки работы "{homework_name}". '
            '{verdict}'.format(homework_name=homework_name, verdict=VERDICTS.get(homework_status)))


def check_tokens():
    """Проверка доступности переменных окружения."""
    logger.info('Проверка токенов.')
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        sys.exit('Одна из переменных окружения не доступна.')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    current_report = {
        'name': '',
        'message': ''
    }
    prev_report = {
        'name': '',
        'output': ''
    }
    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response.get('current_date', current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                homework = homeworks[0]
                current_report['name'] = homework.get('homework_name')
                current_report['message'] = homework.get('status')
            else:
                current_report['message'] = 'Нового статуса нет.'
            if current_report != prev_report:
                send_message(bot, parse_status(homeworks[0]))
                prev_report = current_report.copy()
            else:
                logger.error('Нет нового статуса.')
                raise exceptions.NotForReference()
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.exception(message)
            current_report['message'] = message
            if current_report != prev_report:
                send_message(bot, message)
                prev_report = current_report.copy()
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s: [%(filename)s:%(lineno)s - %(funcName)s] %(levelname)s - %(message)s'
    )
    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    stdout_handler.setFormatter(formatter)
    file_handler = logging.FileHandler((__name__.strip('_'))+'.log', encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)
    logger.addHandler(file_handler)
    main()
