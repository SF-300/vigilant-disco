import logging
import typing as t
import re

from ._span_utils import run_with_logger_substituted, get_span_message, spanned

__all__ = (
    "extract_placeholders",
    "NormalizingFilter",
    "run_with_logger_substituted",
    "get_span_message",
    "spanned",
)


_pattern = r"%\((.*?)\)[diouxXeEfFgGcrs%]"


# TODO: Cache extracted placeholders
def extract_placeholders(format_string: str) -> t.List[str]:
    """
    Extract all placeholders in the format %(name)s from a string.

    Args:
        format_string: The string containing %-style placeholders

    Returns:
        List of placeholder names without the %(...)x wrapper
    """
    return re.findall(_pattern, format_string)


class NormalizingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # NOTE: Unicorn sometimes logs exceptions as messages
        if isinstance(record.msg, BaseException):
            exc = record.msg
            record.msg = str(exc)
            record.exc_text = str(exc)
            record.exc_info = (type(exc), exc, exc.__traceback__)
        return True


# class _StdOutErrAdapter:
#     """
#     Internal adapter that redirects messages, initially sent to a file, to a logger.
#     """

#     def __init__(self, logger: LoggerLike, mode: LevelName):
#         self.__logger = logger
#         self.__mode = mode  # None => adapt DEBUG/INFO/ERROR/...
#         self.__last_level = mode  # None => adapt DEBUG/INFO/ERROR/...
#         self.__lvl_re = re.compile(r"(\((DEBUG|INFO|WARNING|ERROR)\))")
#         self.__lvl_map: t.Mapping[str, LevelName] = {
#             "DEBUG": "debug",
#             "INFO": "info",
#             "WARNING": "warning",
#             "ERROR": "error",
#         }

#     def write(self, message):
#         """
#         Overrides sys.stdout.write() method
#         """
#         messages = message.rstrip().splitlines()
#         for msg in messages:
#             if self.__mode:
#                 lvl = self.__mode
#             else:
#                 match = self.__lvl_re.search(msg)
#                 if match:
#                     lvl = self.__lvl_map[match.group(2)]
#                 else:
#                     lvl = self.__last_level or "info"
#             # OTB may have multi line messages.
#             # In that case, reset happens with a new message
#             self.__last_level = lvl
#             self.__logger.log(lvl, msg)

#     def flush(self):
#         """
#         Overrides sys.stdout.flush() method
#         """
#         pass

#     def isatty(self):  # pylint: disable=no-self-use
#         """
#         Overrides sys.stdout.isatty() method.
#         This is required by OTB Python bindings.
#         """
#         return False


# @contextmanager
# def stdstreams_redirected_to(logger: LoggerLike):
#     """
#     A context manager that redirects messages sent to stdout and stderr to a proper logger.

#     This is a very simplified version tuned to answer specific needs.

#     Usage:
#         with redirect_std_to_logger(logger):
#             # code that prints to stdout/stderr
#     """
#     orig_stdout = sys.stdout
#     orig_stderr = sys.stderr

#     sys.stdout = _StdOutErrAdapter(logger, "info")
#     sys.stderr = _StdOutErrAdapter(logger, "error")

#     try:
#         yield
#     finally:
#         sys.stdout = orig_stdout
#         sys.stderr = orig_stderr
