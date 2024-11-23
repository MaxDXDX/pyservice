"""Tool for loggers."""
import inspect
from logging import StreamHandler, FileHandler, Logger, getLogger, Formatter
import logging
from pathlib import Path

import seqlog
from seqlog.structured_logging import SeqLogHandler


class CustomizedSeqHandler(SeqLogHandler):
    """Tuned SeqLogHandler."""

    def __init__(self, *args, **kwargs):
        level = kwargs.pop('level')
        super().__init__(*args, **kwargs)
        formatter = Formatter(
            style='{',
        )
        self.setFormatter(formatter)
        self.setLevel(level)

    def emit(self, record):
        """Sometimes a default SeqLogHandler stop its consumer.

        We are going to force run a stopped consumer.
        """
        if not self.consumer.is_running:
            self.consumer.start()
        super().emit(record)


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


def remove_all_stream_handlers(logger: Logger):
    all_handlers = logger.handlers
    # pylint:disable=C0123
    matched = [_ for _ in all_handlers if type(_) == StreamHandler]
    for _ in matched:
        logger.removeHandler(_)


def get_content_of_log_file_of_logger(logger: Logger) -> str:
    log_file = get_file_of_logger(logger)
    with open(log_file, 'r', encoding='utf-8') as f:
        return f.read()


def get_logger_for_pyfile(
        pyfile: str | Path,
        directory_for_logs: Path,
        with_path: bool = False,
        erase: bool = True,
        seq_params: dict = None,
) -> Logger:
    pyfile = Path(pyfile)
    stem = pyfile.stem
    path = str(pyfile.parent).partition('/src/')[2]
    with_parent = f'{path}/{stem}'.replace('/', '.')
    log_name = with_parent if with_path else stem
    logger = get_logger(
        log_name=log_name,
        directory_for_logs=directory_for_logs,
        erase=erase,
        seq_params=seq_params,
    )
    logger.debug('Logger for %s: %s', pyfile, logger)
    return logger


def add_seq_handler_to_logger(
        logger: Logger,
        url: str,
        api_key: str,
        level: str = 'DEBUG',
        extra_field: dict = None,
):
    # pylint:disable=C0123
    current_seq_handlers = [_ for _ in logger.handlers
                            if type(_) == CustomizedSeqHandler]

    assert len(current_seq_handlers) <= 1
    if len(current_seq_handlers) == 1:
        return

    seq_handler = CustomizedSeqHandler(
        server_url=url,
        api_key=api_key,
        level=level,
    )
    logger.addHandler(seq_handler)
    if extra_field:
        class ContextFilter(logging.Filter):
            def filter(self, record):
                try:
                    log_props: dict = getattr(record, 'log_props')
                except AttributeError:
                    record.log_props = extra_field
                else:
                    record.log_props = {**log_props, **extra_field}
                return True
        seq_handler.addFilter(ContextFilter())


def indented_decorator(func):

    def wrapper(*args, **kwargs):
        if args and isinstance(args[0], str):
            frames = inspect.getouterframes(inspect.currentframe())
            filtered = [frame for frame in frames if 'src' in frame.filename]
            levels = len(filtered)
            indent = levels * '='

            args_as_list = list(args)
            msg = f'{indent}{args[0]}'
            args_as_list[0] = msg
            args = tuple(args_as_list)
        func(*args, **kwargs)
    return wrapper


def get_logger(
        log_name: str,
        directory_for_logs: Path,
        erase: bool = True,
        seq_params: dict = None,
) -> Logger:
    log = getLogger(log_name)
    # if indented:
    #     log.debug = indented_decorator(log.debug)
    log_file = directory_for_logs / f'{log_name}.log'
    error_log_file = directory_for_logs / 'errors.log'
    log_files = [log_file, error_log_file]

    if erase and log_file.is_file():
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write('')
    # pylint:disable=C0123
    current_file_handlers = [_ for _ in log.handlers if type(_) == FileHandler]
    orphans = []
    for handler in current_file_handlers:
        handler: FileHandler
        current_file = Path(handler.baseFilename)
        if current_file not in log_files:
            orphans.append(handler)
    for orphan in orphans:
        log.removeHandler(orphan)

    file_handlers: list[FileHandler] = \
        [_ for _ in log.handlers if type(_) == FileHandler]
    current_files = [Path(_.baseFilename) for _ in file_handlers]

    for f in log_files:
        if f not in current_files:
            file_handler = FileHandler(f)
            formatter = Formatter(
                '%(asctime)s %(name)-20s - %(levelname)-5s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            if f == error_log_file:
                file_handler.setLevel('ERROR')
            else:
                file_handler.setLevel('DEBUG')
            log.addHandler(file_handler)

    remove_all_stream_handlers(log)

    seq_handlers = [_ for _ in log.handlers if type(_) == CustomizedSeqHandler]
    assert len(seq_handlers) <= 1

    desired_number_of_handlers = 3 if seq_handlers else 2

    if len(log.handlers) != desired_number_of_handlers:
        raise RuntimeError(f'number of handlers for {log_name} is not 2: '
                           f'{log.handlers}')
    log.setLevel('DEBUG')

    if seq_params and not seq_handlers:
        global_properties = seq_params.get('global_properties', {})
        seqlog.set_global_log_properties(**global_properties)
        add_seq_handler_to_logger(
            log, seq_params['url'],
            seq_params['api_key'],
            seq_params.get('level', 'DEBUG'),
            seq_params.get('extra_field'),
        )

    log.propagate = False

    return log
