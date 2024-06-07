class MessageError(Exception):
    """Исключение для ошибок отправки сообщений."""

    def __init__(self, message):
        self.message = message


class ResponseError(Exception):
    """Исключение для ответов сервера кроме HTTPStatus.OK."""

    def __init__(self, message):
        self.message = message


class RequestError(Exception):
    """Исключение для ошибки запроса сервера."""

    def __init__(self, message):
        self.message = message
