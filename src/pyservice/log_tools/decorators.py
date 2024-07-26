"""Logging decorators."""

import functools
import logging
from logging import Logger


def shrink(string, limit):
    """Shrink too long strings"""
    string_length = len(string)
    if string_length > limit:
        result = string[:limit - 1] + ' ... ' + string[-4:]
    else:
        result = string
    return result


def execute_function_with_logging(
        logger: Logger,
        level: str,
        fn, args, kwargs,
        class_name: str = '',
        arg_length_limit: int = 100,
        log_message_limit: int = 200,
):
    if not level:
        level = logging.getLevelName(logger.level)
    logger_method_name = level.lower()
    logger_method = getattr(logger, logger_method_name)
    signature_elements = []
    args_for_logging = list(args)
    if class_name:
        args_for_logging.pop(0)
    if args_for_logging:
        shrunk = [shrink(repr(_), arg_length_limit) for _ in args_for_logging]
        args_repr = ', '.join(shrunk).replace('\n', ' ')
        signature_elements.append(args_repr)
    if kwargs:
        as_list = [f'{keyword}={shrink(repr(value), arg_length_limit)}'
                   for keyword, value in kwargs.items()]
        kwargs_repr = ', '.join(as_list)
        signature_elements.append(kwargs_repr)
    method_signature = '(' + ', '.join(signature_elements) + ')'
    method_name = fn.__name__ if hasattr(fn, '__name__') else ''
    if class_name:
        method_name = class_name + '.' + method_name
    function_repr = method_name + method_signature

    message_before = f'{function_repr} starts ...'.replace('\n', ' ')
    logger_method(message_before)

    result = fn(*args, **kwargs)
    result_for_log = shrink(repr(result), log_message_limit)
    message_after = f'{method_name} ➞ {result_for_log}'.replace(
        '\n', ' ')
    logger_method(message_after)
    return result


def logged(func=None, *, logger: logging.Logger, level: str = None):
    """Add two log records: before calling a function and after execution"""

    def log_decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            result = execute_function_with_logging(
                logger, level, fn, args, kwargs)
            return result
        return wrapper
    if func:
        return log_decorator(func)
    else:
        return log_decorator


def logged_method(func=None, *, logger: logging.Logger, level: str = None):
    """Add two log records: before calling a function and after execution"""

    def log_decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            args_without_self = list(args)
            class_instance = args_without_self.pop(0)
            class_name = type(class_instance).__name__
            result = execute_function_with_logging(
                logger, level, fn, args, kwargs, class_name=class_name)
            return result
        return wrapper
    if func:
        return log_decorator(func)
    else:
        return log_decorator


# def logged(_func=None, *, logger: logging.Logger, level: str = 'DEBUG'):
#     """Add two log records: before calling a function and after execution"""
#
#     def log_decorator(fn):
#         @functools.wraps(fn)
#         def wrapper(*args, **kwargs):
#             if inspect.ismethod(fn):  # TODO: inspect does not work here!!!
#                 args_without_self = list(args)
#                 class_instance = args_without_self.pop(0)
#                 class_name = type(class_instance).__name__
#             else:
#                 class_name = None
#             result = execute_function_with_logging(
#                 logger, fn, args, kwargs, class_name=class_name)
#             return result
#         return wrapper
#     if _func:
#         return log_decorator(_func)
#     else:
#         return log_decorator
