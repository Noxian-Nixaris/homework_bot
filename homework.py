import logging
import os
import requests
import time


from dotenv import load_dotenv
from telebot import TeleBot

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='main.log',
    filemode='w'
)

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


def check_tokens():
    """Проверяем наличие переменных окружения."""
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        return True


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
        homework_statuses = requests.get(
            ENDPOINT, headers=headers, params=payload
        )
        homework = homework_statuses.json()
        if check_response(homework):
            logging.debug('Ответ сервера получен.')
            return homework.get('homeworks')[0]
        logging.error('Не верный ответ сервера.')
        return dict()
    except requests.RequestException as error:
        logging.error(error)


def check_response(response):
    """Проверяем корректность ответа от Практикума."""
    if type(response) is dict:
        if 'homeworks' in response:
            answer = response.get('homeworks')
            if type(answer) is list:
                if len(answer) > 0:
                    return True
                else:
                    logging.error('Cприсок "homeworks" пуст')
                    return False
            else:
                logging.error('Значение homeworks - не список.')
                raise TypeError()
        else:
            logging.error('Ключ "homeworks" не найден')
            raise KeyError()
    else:
        logging.error('Ответ сервера не словарь.')
        raise TypeError()


def parse_status(homework):
    """Получаем статус домашней работы из ответа сервера."""
    if homework.get('status') not in HOMEWORK_VERDICTS:
        logging.error('Неправильный статус.')
        raise KeyError()
    if 'homework_name' not in homework:
        logging.error('Нет имени домашней работы.')
        raise KeyError()
    verdict_key = homework.get('status')
    homework_name = homework.get('homework_name')
    verdict = HOMEWORK_VERDICTS.get(verdict_key)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Отсутствует обязательная переменная окружения')
        raise Exception()
    bot = TeleBot(TELEGRAM_TOKEN)
    timestamp = int(time.time()) - 1209600
    first_message = None
    while True:
        try:
            response = get_api_answer(timestamp)
            message = parse_status(response)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(error, exc_info=True)
        if message == first_message:
            logging.debug('Нет обновлений статуса')
        else:
            send_message(bot, message)
            first_message = message
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
