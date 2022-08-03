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
