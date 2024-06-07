class Errors(Exception):
    """Базовый класс исключений."""

    def __init__(self, message):
        self.message = message


class MessageError(Errors):
    """Исключение для ошибок отправки сообщений."""

    pass


class ResponseError(Errors):
    """Исключение для ответов сервера кроме HTTPStatus.OK."""

    pass


class RequestError(Errors):
    """Исключение для ошибки запроса сервера."""

    pass
