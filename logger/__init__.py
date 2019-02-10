import logging
import threading

initLock = threading.Lock()
rootLoggerInitialized = False

log_format = "%(asctime)s %(name)s [%(levelname)s] %(message)s"
level = logging.DEBUG
file_log = None  # File name
console_log = True


def init_handler(handler):
    handler.setFormatter(Formatter(log_format))


def init_logger(logger):
    logger.setLevel(level)

    if file_log is not None:
        file_handler = logging.FileHandler(file_log)
        init_handler(file_handler)
        logger.addHandler(file_handler)

    if console_log:
        console_handler = logging.StreamHandler()
        init_handler(console_handler)
        logger.addHandler(console_handler)


def initialize():
    global rootLoggerInitialized
    with initLock:
        if not rootLoggerInitialized:
            init_logger(logging.getLogger())
            rootLoggerInitialized = True


def get_logger(name=None):
    initialize()
    return logging.getLogger(name)


# This formatter provides a way to hook in formatTime.
class Formatter(logging.Formatter):
    DATETIME_HOOK = None

    def formatTime(self, record, date_fmt=None):
        new_datetime = None

        if Formatter.DATETIME_HOOK is not None:
            new_datetime = Formatter.DATETIME_HOOK()

        if new_datetime is None:
            ret = super(Formatter, self).formatTime(record, date_fmt)
        else:
            ret = str(new_datetime)
        return ret
