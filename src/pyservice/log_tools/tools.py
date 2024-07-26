"""Tool for loggers."""


from logging import FileHandler, Logger
from pathlib import Path


def get_file_of_logger(logger: Logger) -> Path:
    log_file = next(filter(
        lambda h: isinstance(h, FileHandler),
        logger.handlers)).baseFilename
    return Path(log_file)


def clean_file_for_logger(logger: Logger) -> Path:
    log_file = get_file_of_logger(logger)
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write('')
    return log_file


def get_content_of_log_file_of_logger(logger: Logger) -> str:
    log_file = get_file_of_logger(logger)
    with open(log_file, 'r', encoding='utf-8') as f:
        return f.read()
