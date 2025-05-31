import typing as t
import logging
import warnings
from datetime import datetime

from boltons.tbutils import ExceptionInfo
from rich.console import ConsoleRenderable, Group, Console
from rich.style import Style
from rich.theme import Theme
from rich.text import Text
from rich.logging import RichHandler
from rich.highlighter import RegexHighlighter
from logfmter import Logfmter
from pythonjsonlogger.json import JsonFormatter

from .base import RecordAttr, SpanDict, Level


class SpanAwareLogFmtFormatter(Logfmter):
    def __init__(
        self,
        include_keys: t.List[str],
        exclude_keys: t.Sequence[str] = tuple(),
        datefmt: str = "%H:%M:%S:%f",
    ):
        # HACK: For some wired reason, LogfmtFormatter doesn't call super().__init__ in its own __init__
        #       so we need to call it manually. Otherwise, something somewhere breaks due to missing
        #       attributes in cerain conditions.
        logging.Formatter.__init__(self, datefmt=datefmt)
        super().__init__(keys=include_keys, datefmt=datefmt)
        self._exclude_keys = exclude_keys

    def get_extra(self, record: logging.LogRecord) -> dict:  # type: ignore
        result = super().get_extra(record)

        if isinstance(record.args, t.Mapping):

            def updates_iter():
                for key, value in record.args.items():  # type: ignore
                    if key in result:
                        warnings.warn(f"Key {key} is already present in record.args")
                    yield key, value

            result.update(updates_iter())

        for key in self._exclude_keys:
            result.pop(key, None)

        return result

    def formatTime(self, record, datefmt=None):
        if not datefmt:
            return super().formatTime(record, datefmt=datefmt)
        return datetime.fromtimestamp(record.created).astimezone().strftime(datefmt)

    def format(self, record: logging.LogRecord) -> str:
        record = _ensure_spans_denormalized(record)
        return super().format(record)


class SpanAwareRichHandler(RichHandler):
    LOGGER_NAME_STYLE = Style(color="dark_violet", bold=True)
    OP_PATH_SEPARATOR = ">"
    SPAN_PATH_STYLE = Style(color="dark_orange")

    LEVEL_MAPPING: t.Mapping[Level, tuple[str, Style]] = {
        "debug": ("DEBUG", Style(color="white", bold=True)),
        "info": ("INFO", Style(color="blue", bold=True)),
        "warning": ("WARN", Style(color="yellow", bold=True)),
        "error": ("ERROR", Style(color="red", bold=True)),
        "critical": ("FATAL", Style(color="bright_red", blink=True, bold=True)),
    }

    class LogfmtHighlighter(RegexHighlighter):
        base_style = "logging.logfmt."
        highlights = [
            r'(?P<key>(?:"(?:[^"\\]|\\.)*"|[\w_]+))(?P<equals>=)(?P<value>(?:"(?:[^"\\]|\\.)*"|[^\s]+))'
        ]

    def __init__(self, *args, **kwargs):
        kwargs["console"] = kwargs.get(
            "console",
            Console(
                theme=Theme(
                    {
                        "logging.keyword": "sandy_brown",
                        "logging.logfmt.key": "tan",
                        "logging.logfmt.equals": "grey30",
                        "logging.logfmt.value": "yellow4",
                    }
                )
            ),
        )
        kwargs["highlighter"] = kwargs.get("highlighter", self.LogfmtHighlighter())
        super().__init__(*args, **kwargs)

    def get_level_text(self, record: logging.LogRecord) -> Text:
        try:
            level_name, style = self.LEVEL_MAPPING[
                t.cast(Level, record.levelname.lower())
            ]
        except KeyError:
            level_name, style = record.levelname.upper(), Style(color="grey42")

        return Text.styled(level_name.ljust(5), style)

    def render_message(
        self, record: logging.LogRecord, message: str
    ) -> ConsoleRenderable:
        record = _ensure_spans_denormalized(record)
        message_renderable = super().render_message(record, message)
        logger_path = Text(
            f"{self.OP_PATH_SEPARATOR} {record.name}", style=self.LOGGER_NAME_STYLE
        )
        span_path = Text(
            " ".join(
                f"{self.OP_PATH_SEPARATOR} {r}"
                for r in getattr(record, RecordAttr.SPANS_MESSAGES, [])
            ),
            style=self.SPAN_PATH_STYLE,
        )
        op_path_renderable = Text(" ").join(f for f in [span_path, logger_path] if f)
        message_renderable = Group(op_path_renderable, message_renderable)
        return message_renderable


class SpanAwareJsonFormatter(JsonFormatter):
    def formatException(self, ei):  # type: ignore
        exc_info = ExceptionInfo.from_exc_info(*ei)  # type: ignore
        return exc_info.to_dict()

    def formatStack(self, stack_info):  # type: ignore
        # TODO: Implement stack_info serialization
        return super().formatStack(stack_info)

    def format(self, record: logging.LogRecord) -> str:
        record = _ensure_spans_denormalized(record)
        return super().format(record)


# NOTE: This function should be called from handler and not from filter because ambient context is filter itself
#       and we don't guarantee, in what order filters are applied.
def _ensure_spans_denormalized[T: logging.LogRecord](record: T) -> T:
    try:
        spans: t.Sequence[SpanDict] = getattr(record, RecordAttr.RAW_SPANS)
    except AttributeError:
        return record

    setattr(record, RecordAttr.SPANS_IDS, spans_ids := [])
    setattr(record, RecordAttr.SPANS_MSGS, spans_msgs := [])
    setattr(record, RecordAttr.SPANS_MESSAGES, spans_messages := [])

    for span in spans:
        spans_ids.append(span["id"])
        spans_msgs.append(span["msg"])
        spans_messages.append(span["message"])

    return record
