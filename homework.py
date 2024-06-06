import logging
import os
import sys
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telebot import TeleBot

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

ONE_WEEK = 604800


def check_tokens():
    """Проверяем наличие переменных окружения."""
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def send_message(bot, message):
    """Отправляем сообщение в чат."""
    try:
        chat_id = TELEGRAM_CHAT_ID
        bot.send_message(chat_id=chat_id, text=message)
        logging.debug('Сообщение отправлено')
    except Exception as error:
        logging.error(error)


def get_api_answer(timestamp):
    """Запрашиваем данные по домашней работе с Практикума."""
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    payload = {'from_date': timestamp}
    try:
        response = requests.get(
            ENDPOINT, headers=headers, params=payload
        )
        if response.status_code != HTTPStatus.OK:
            raise TypeError('Неверный ответ сервера')
        return response.json()
    except requests.RequestException as error:
        raise TypeError(error)


def check_response(response):
    """Проверяем корректность ответа от Практикума."""
    if not isinstance(response, dict):
        raise TypeError('Ответ сервера не словарь.')
    if 'homeworks' not in response:
        raise KeyError('Ключ "homeworks" не найден.')
    answer = response.get('homeworks')
    if not isinstance(answer, list):
        raise TypeError('Значение homeworks - не список.')
    return response.get('homeworks')


def parse_status(homework):
    """Получаем статус домашней работы из ответа сервера."""
    if homework.get('status') not in HOMEWORK_VERDICTS:
        raise KeyError('Неправильный статус.')
    if 'homework_name' not in homework:
        raise KeyError('Нет имени домашней работы.')
    verdict_key = homework.get('status')
    homework_name = homework.get('homework_name')
    verdict = HOMEWORK_VERDICTS.get(verdict_key)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Отсутствует обязательная переменная окружения')
        sys.exit()
    bot = TeleBot(TELEGRAM_TOKEN)
    timestamp = int(time.time()) - ONE_WEEK
    last_message = None
    while True:
        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)
            timestamp = response.get('current_date') - ONE_WEEK
            if len(homework) > 0:
                message = parse_status(homework[0])
            else:
                message = 'Список домашних работ за период пуст'
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.exception(error)
        if message == last_message:
            logging.debug('Нет обновлений статуса')
        else:
            send_message(bot, message)
            last_message = message
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("main.log"),
            logging.StreamHandler()
        ]
    )
    main()
