class EmptyEnvVariable(Exception):
    """Недоступна переменная окружения."""

    pass


class EndpointNotAvailable(Exception):
    """Эндпоинт недоступен."""

    pass


class FailSendMessageTg(Exception):
    """Сообщение не было отправлено."""

    pass


class ExceptionApi(Exception):
    """Некорректный API."""

    pass


class WrongResponseCode(Exception):
    """Неверный код ответа."""

    pass


class NotForReference(Exception):
    """Исключение с внутренними ошибками."""

    pass


class ExceptionForTelegram(NotForReference):
    """Исключения которые необходимо отравить в Telegram."""

    pass


class EmptyAPIResponse(NotForReference):
    """Пустой ответ от API."""

    pass
