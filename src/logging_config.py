import logging
import sys

LOGGER_NAME = "fastai"
LOG_FORMAT = "%(levelname)s: %(message)s"


def get_logger(name: str | None = None) -> logging.Logger:
    """Вернуть логгер приложения (дочерний для `fastai`)."""
    if not name or name == LOGGER_NAME:
        return logging.getLogger(LOGGER_NAME)
    return logging.getLogger(f"{LOGGER_NAME}.{name}")


def setup_logging(*, debug: bool = False) -> None:
    """Настроить логи приложения: вывод в консоль и уровень детализации.

    Вызывается один раз при старте приложения или скрипта. Флаг `debug`
    (переменная окружения `DEBUG`) включает уровень DEBUG только для логов
    приложения и не затрагивает сторонние библиотеки. Повторные вызовы
    безопасны: обработчик добавляется один раз.
    """
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.propagate = False
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)
