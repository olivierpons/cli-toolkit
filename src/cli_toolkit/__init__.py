"""Standalone CLI toolkit: thread-safe output with Rich and custom argparse help.

This module merges three Django-specific utilities into a single,
dependency-free (except optional Rich) toolkit for any Python CLI
application.

Requirements
------------
- Python >= 3.13
- Optional: `rich` library (`pip install rich`)
  When Rich is absent, every feature still works via ANSI fallback.

Quick start
-----------
::

    from cli_toolkit import OutputHandler, build_parser

    out = OutputHandler(verbosity=2)
    out.success("Server started on port 8080")
    out.warning("Cache directory missing, using /tmp")
    out.error("Connection refused")
    out.debug("request_id=af83c…")

    # Rich table (auto-fallback to plain text if Rich is missing)
    table = out.Table(title="Results")
    table.add_column("ID")
    table.add_column("Status")
    table.add_row("1", "OK")
    out.rich_print(table)

    # Custom argparse parser with epilog and split -h / --help
    parser = build_parser(
        prog="my_tool",
        description="Process uploaded files.",
        epilog='''
    Examples:
        my_tool --all
        my_tool --id=42
        ''',
        short_help='''
    my_tool — Process uploaded files

      --all    Process everything
      --id N   Process specific file

    Use --help for full documentation.
        ''',
    )
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--id", type=int)
    args = parser.parse_args()

Capabilities
------------

Output handler (`OutputHandler`)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- Thread-safe writes (`threading.RLock`): concurrent output never
  interleaves.
- Verbosity gating (0 = silent, 1 = normal, 2 = verbose, 3 = debug):
  every method accepts `min_level` to auto-filter.
- Automatic timestamps with aligned multi-line indentation.
- Styled helpers: `success()`, `warning()`, `error()`,
  `notice()`, `debug()`.
- `NO_COLOR` env-var respected (see https://no-color.org/).
- Rich integration when available:

  - `out.Console` — Rich `Console` (or ANSI fallback).
  - `out.Table` / `out.Panel` / `out.Text` — Rich renderables
    (or lightweight substitutes).
  - `out.rich_print(renderable)` — thread-safe `Console.print()`.

- Logging bridge: every `out.*` call also dispatches to
  `logging.getLogger(__name__)` at the matching level.

Custom argparse help (`build_parser` / `add_short_help`)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- `RawTextHelpFormatter` by default, so manual indentation and
  newlines are preserved in `description` and `epilog`.
- `epilog` parameter printed after the auto-generated argument list.
- Split `-h` / `--help`:

  - When `short_help` is provided, `-h` prints a compact memo and
    exits, while `--help` prints full argparse output (description +
    arguments + epilog).
  - When `short_help` is omitted, `-h` and `--help` behave
    identically (standard argparse).

- `add_short_help(parser, short_help)` can retrofit the split on any
  existing `ArgumentParser`.
- `get_epilog` / `get_short_help` callbacks for dynamic content
  (database look-ups, runtime detection, etc.).

Thread-safe rich helpers
^^^^^^^^^^^^^^^^^^^^^^^^
`OutputHandler` exposes Rich classes as attributes so callers never
need to check availability themselves::

    table = out.Table(title="Deployments")
    table.add_column("Env")
    table.add_column("Version")
    table.add_row("prod", "3.2.1")
    out.rich_print(table)      # thread-safe

    panel = out.Panel("All checks passed", title="Summary")
    out.rich_print(panel)

If Rich is missing, the fallback renders a plain-text approximation.

Verbosity levels
^^^^^^^^^^^^^^^^
+---------+----------------------------+
| Level   | Intended use               |
+---------+----------------------------+
| 0       | Errors only (silent mode)  |
| 1       | Normal operation messages  |
| 2       | Verbose / detailed output  |
| 3       | Debug traces               |
+---------+----------------------------+

Every output method defaults to `min_level=1` except `error`
(defaults to 0) and `debug` (defaults to 3).

Environment variables
^^^^^^^^^^^^^^^^^^^^^
`NO_COLOR`
    Set to any value to disable all ANSI colors and Rich markup.
    Both the ANSI fallback path and the Rich console respect this.
"""

from __future__ import annotations

__version__ = "0.1.0"

import argparse
import logging
import os
import sys
import threading
from datetime import datetime
from typing import IO, Any


# ===================================================================
# Rich fallback stubs (defined first so the except block can bind them)
# ===================================================================


class _FallbackText:
    """Minimal stand-in for `rich.text.Text`."""

    def __init__(self, text: str = "", style: str = "") -> None:  # noqa
        self._text = text

    def __str__(self) -> str:
        return self._text


class _FallbackTable:
    """Minimal stand-in for `rich.table.Table`.

    Renders columns as tab-separated rows.
    """

    def __init__(self, *, title: str = "", **kwargs: Any) -> None:  # noqa
        self._title = title
        self._columns: list[str] = []
        self._rows: list[list[str]] = []

    def add_column(self, header: str, **kwargs: Any) -> None:  # noqa
        """Append a column header."""
        self._columns.append(header)

    def add_row(self, *values: str) -> None:
        """Append a data row."""
        self._rows.append(list(values))

    def __str__(self) -> str:
        lines: list[str] = []
        if self._title:
            lines.append(self._title)
            lines.append("-" * len(self._title))
        if self._columns:
            lines.append("\t".join(self._columns))
            lines.append("\t".join("-" * len(c) for c in self._columns))
        for row in self._rows:
            lines.append("\t".join(row))
        return "\n".join(lines)


class _FallbackPanel:
    """Minimal stand-in for `rich.panel.Panel`."""

    def __init__(
            self, content: str = "", *, title: str = "", **kwargs: Any  # noqa
    ) -> None:
        self._content = str(content)
        self._title = title

    def __str__(self) -> str:
        header = f"[{self._title}]" if self._title else ""
        return f"{header}\n{self._content}" if header else self._content


class _FallbackConsole:
    """Minimal stand-in for `rich.console.Console`."""

    def __init__(self, **kwargs: Any) -> None:
        stream: IO[str] | None = kwargs.get("file")
        if stream is None:
            stream = sys.stdout
        if stream is None:
            raise RuntimeError("No output stream available")
        self._file: IO[str] = stream

    def print(self, *args: Any, **kwargs: Any) -> None:  # noqa
        """Write stringified args to the underlying stream."""
        parts = " ".join(str(a) for a in args)
        self._file.write(parts + "\n")
        self._file.flush()


def _fallback_escape(text: str) -> str:
    """No-op escape when Rich is absent."""
    return text


# ---------------------------------------------------------------------------
# Rich detection — import once, expose availability flag
# ---------------------------------------------------------------------------

RICH_AVAILABLE: bool = False

try:
    from rich.console import Console as _RichConsole
    from rich.markup import escape as _rich_escape
    from rich.panel import Panel as _RichPanel
    from rich.table import Table as _RichTable
    from rich.text import Text as _RichText

    RICH_AVAILABLE = True
except ImportError:  # pragma: no cover
    _RichConsole = _FallbackConsole  # type: ignore[assignment, misc]
    _RichTable = _FallbackTable  # type: ignore[assignment, misc]
    _RichPanel = _FallbackPanel  # type: ignore[assignment, misc]
    _RichText = _FallbackText  # type: ignore[assignment, misc]
    _rich_escape = _fallback_escape

logger = logging.getLogger(__name__)


# ===================================================================
# ANSI color constants (used only when Rich is absent)
# ===================================================================

_ANSI_COLORS: dict[str, str] = {
    "RESET": "\033[0m",
    "SUCCESS": "\033[92m",
    "WARNING": "\033[93m",
    "ERROR": "\033[91m",
    "INFO": "\033[94m",
    "DEBUG": "\033[95m",
    "NOTICE": "\033[96m",
}


def _ansi_colorize(text: str, color: str) -> str:
    """Wrap *text* in ANSI escape codes.

    Args:
        text: Plain text to colorize.
        color: Key into `_ANSI_COLORS`.

    Returns:
        Colorized string, or *text* unchanged when colors are
        disabled (`NO_COLOR` set or stdout is not a TTY).
    """
    if os.getenv("NO_COLOR") or sys.stdout is None or not sys.stdout.isatty():
        return text
    code = _ANSI_COLORS.get(color, "")
    if not code:
        return text
    return f"{code}{text}{_ANSI_COLORS['RESET']}"


def _resolve_stream(
    explicit: IO[str] | None,
    fallback: IO[str] | None,
) -> IO[str]:
    """Return *explicit* if set, otherwise *fallback*, with a None guard.

    Args:
        explicit: Stream passed by the caller.
        fallback: System default (e.g. `sys.stdout`).

    Returns:
        A guaranteed non-None writable stream.

    Raises:
        RuntimeError: If both *explicit* and *fallback* are `None`.
    """
    if explicit is not None:
        return explicit
    if fallback is not None:
        return fallback
    raise RuntimeError("No output stream available (sys.stdout/stderr is None)")


# ===================================================================
# OutputHandler
# ===================================================================


class OutputHandler:
    """Thread-safe, verbosity-aware console output with Rich support.

    Args:
        verbosity: Initial verbosity level (0-3).
        stdout: Output stream for normal messages.
        stderr: Output stream for error messages.
        use_rich: Attempt to use Rich when available.
        no_color: Force colors off regardless of terminal capability.
    """

    _output_lock: threading.RLock = threading.RLock()

    # -- Rich / fallback class aliases (set per-instance in __init__) --

    Console: type
    Table: type
    Panel: type
    Text: type
    escape: Any  # callable

    def __init__(
        self,
        verbosity: int = 1,
        *,
        stdout: IO[str] | None = None,
        stderr: IO[str] | None = None,
        use_rich: bool = True,
        no_color: bool = False,
    ) -> None:
        self.verbosity: int = max(0, min(3, verbosity))
        self.stdout: IO[str] = _resolve_stream(stdout, sys.stdout)
        self.stderr: IO[str] = _resolve_stream(stderr, sys.stderr)
        self.no_color: bool = no_color or bool(os.getenv("NO_COLOR"))
        self._use_rich: bool = use_rich and RICH_AVAILABLE and not self.no_color
        self._logger: logging.Logger = logging.getLogger(__name__)

        self._setup_rich()

    # -- setup --------------------------------------------------------

    def _setup_rich(self) -> None:
        """Bind Rich classes or fallback stubs to instance attributes."""
        if self._use_rich:
            self.Console = _RichConsole
            self.Table = _RichTable
            self.Panel = _RichPanel
            self.Text = _RichText
            self.escape = _rich_escape
            self._console = _RichConsole(
                file=self.stdout,
                no_color=self.no_color,
            )
            self._err_console = _RichConsole(
                file=self.stderr,
                no_color=self.no_color,
            )
        else:
            self.Console = _FallbackConsole
            self.Table = _FallbackTable
            self.Panel = _FallbackPanel
            self.Text = _FallbackText
            self.escape = _fallback_escape
            self._console = _FallbackConsole(file=self.stdout)
            self._err_console = _FallbackConsole(file=self.stderr)

    # -- properties ---------------------------------------------------

    @property
    def has_rich(self) -> bool:
        """Whether the real Rich library is active."""
        return self._use_rich

    # -- verbosity ----------------------------------------------------

    def set_verbosity(self, level: int) -> None:
        """Clamp and set verbosity.

        Args:
            level: Desired verbosity (0-3).
        """
        self.verbosity = max(0, min(3, level))

    def _should_output(self, min_level: int) -> bool:
        """Return `True` when current verbosity >= *min_level*."""
        return self.verbosity >= min_level

    # -- timestamp ----------------------------------------------------

    @staticmethod
    def _timestamp() -> str:
        """Return `YYYY/MM/DD HH:MM:SS` for the current instant."""
        return datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    # -- low-level write ----------------------------------------------

    def _write(
        self,
        message: str,
        *,
        stream: IO[str] | None = None,
        color: str = "",
        without_time: bool = False,
        keep_spaces: bool = True,
        no_newline: bool = False,
    ) -> None:
        """Write a single (possibly multi-line) message to *stream*.

        Called under the output lock by every public method.

        Args:
            message: Text to emit.
            stream: Target stream (defaults to `self.stdout`).
            color: ANSI color key or Rich style name.
            without_time: Skip the timestamp prefix.
            keep_spaces: Align continuation lines with the first line.
            no_newline: Suppress the trailing newline.
        """
        target: IO[str] = stream if stream is not None else self.stdout
        ending: str = "" if no_newline else "\n"

        # Build prefix / spacing
        if without_time:
            prefix = ""
            spacing = ""
        else:
            ts = self._timestamp()
            prefix = f"> {ts} : "
            spacing = " " * len(prefix) if keep_spaces else ""

        lines = message.split("\n")

        for idx, line in enumerate(lines):
            leader = prefix if idx == 0 else spacing
            styled = self._style_line(line, color)
            target.write(f"{leader}{styled}{ending}")

        target.flush()

    def _style_line(self, text: str, color: str) -> str:
        """Apply ANSI color to *text* (no-op when Rich or no_color)."""
        if self._use_rich or self.no_color or not color:
            return text
        return _ansi_colorize(text, color)

    # -- public output methods ----------------------------------------

    def out(
        self,
        message: str | list[str],
        *,
        min_level: int = 1,
        color: str = "",
        without_time: bool = False,
        keep_spaces: bool = True,
        no_newline: bool = False,
        is_error: bool = False,
    ) -> None:
        """General-purpose, thread-safe output.

        Args:
            message: Text or list of texts to emit.
            min_level: Minimum verbosity to actually print.
            color: ANSI color key (`SUCCESS`, `WARNING`, …).
            without_time: Skip the timestamp prefix.
            keep_spaces: Align continuation lines under the timestamp.
            no_newline: Omit the trailing newline.
            is_error: Route to stderr instead of stdout.
        """
        if not self._should_output(min_level):
            return

        stream = self.stderr if is_error else self.stdout
        messages = [message] if isinstance(message, str) else message

        with self._output_lock:
            for msg in messages:
                self._log_dispatch(msg, is_error=is_error)
                self._write(
                    msg,
                    stream=stream,
                    color=color,
                    without_time=without_time,
                    keep_spaces=keep_spaces,
                    no_newline=no_newline,
                )

    def success(self, message: str, *, min_level: int = 1) -> None:
        """Emit a green success message.

        Args:
            message: Text to print.
            min_level: Minimum verbosity.
        """
        if self._use_rich:
            self._rich_styled(message, style="bold green", min_level=min_level)
        else:
            self.out(message, min_level=min_level, color="SUCCESS")

    def warning(self, message: str, *, min_level: int = 1) -> None:
        """Emit a yellow warning message.

        Args:
            message: Text to print.
            min_level: Minimum verbosity.
        """
        if self._use_rich:
            self._rich_styled(message, style="bold yellow", min_level=min_level)
        else:
            self.out(message, min_level=min_level, color="WARNING")

    def error(self, message: str, *, min_level: int = 0) -> None:
        """Emit a red error message to stderr.

        Args:
            message: Text to print.
            min_level: Minimum verbosity.
        """
        if not self._should_output(min_level):
            return
        with self._output_lock:
            self._log_dispatch(message, is_error=True)
            if self._use_rich:
                ts = self._timestamp()
                self._err_console.print(
                    f"> {ts} : ERROR: {message}", style="bold red"
                )
            else:
                ts = self._timestamp()
                line = f"> {ts} : ERROR: {message}"
                self.stderr.write(_ansi_colorize(line, "ERROR") + "\n")
                self.stderr.flush()

    def notice(self, message: str, *, min_level: int = 1) -> None:
        """Emit a cyan notice message.

        Args:
            message: Text to print.
            min_level: Minimum verbosity.
        """
        if self._use_rich:
            self._rich_styled(message, style="bold cyan", min_level=min_level)
        else:
            self.out(message, min_level=min_level, color="NOTICE")

    def info(self, message: str, *, min_level: int = 1) -> None:
        """Emit a blue informational message.

        Args:
            message: Text to print.
            min_level: Minimum verbosity.
        """
        if self._use_rich:
            self._rich_styled(message, style="blue", min_level=min_level)
        else:
            self.out(message, min_level=min_level, color="INFO")

    def debug(self, message: str, *, min_level: int = 3) -> None:
        """Emit a debug message without a timestamp.

        Args:
            message: Text to print.
            min_level: Minimum verbosity.
        """
        if self._use_rich:
            if not self._should_output(min_level):
                return
            with self._output_lock:
                self._log_dispatch(message, is_error=False)
                self._console.print(f"[DEBUG] {message}", style="magenta")
        else:
            self.out(
                f"[DEBUG] {message}",
                min_level=min_level,
                color="DEBUG",
                without_time=True,
            )

    # -- verbosity shorthand ------------------------------------------

    def verbose(self, message: str) -> None:
        """Shorthand for `out(…, min_level=2)`.

        Args:
            message: Text to print.
        """
        self.out(message, min_level=2)

    def trace(self, message: str) -> None:
        """Shorthand for `out(…, min_level=3, without_time=True)`.

        Args:
            message: Text to print.
        """
        self.out(message, min_level=3, without_time=True)

    # -- thread-identified output -------------------------------------

    def thread_error(self, message: str, *, min_level: int = 0) -> None:
        """Error prefixed with the current thread name.

        Args:
            message: Text to print.
            min_level: Minimum verbosity.
        """
        tid = threading.current_thread().name
        self.error(f"[Thread {tid}] {message}", min_level=min_level)

    def thread_warning(self, message: str, *, min_level: int = 1) -> None:
        """Warning prefixed with the current thread name.

        Args:
            message: Text to print.
            min_level: Minimum verbosity.
        """
        tid = threading.current_thread().name
        self.warning(f"[Thread {tid}] {message}", min_level=min_level)

    def thread_success(self, message: str, *, min_level: int = 1) -> None:
        """Success message prefixed with the current thread name.

        Args:
            message: Text to print.
            min_level: Minimum verbosity.
        """
        tid = threading.current_thread().name
        self.success(f"[Thread {tid}] {message}", min_level=min_level)

    # -- Rich helpers -------------------------------------------------

    def rich_print(self, renderable: Any, *, to_stderr: bool = False) -> None:
        """Thread-safe print of any Rich renderable (or fallback string).

        Args:
            renderable: A Rich `Table`, `Panel`, `Text`, or any
                object with a `__str__` method.
            to_stderr: Route to stderr console.
        """
        console = self._err_console if to_stderr else self._console
        with self._output_lock:
            console.print(renderable)

    # -- silent mode --------------------------------------------------

    @staticmethod
    def silent_error(message: str) -> None:
        """Write an error line to stderr unconditionally.

        Args:
            message: Error text.
        """
        sys.stderr.write(f"[Error: {message}]\n")
        sys.stderr.flush()

    # -- option display -----------------------------------------------

    def option_status(self, enabled: bool, description: str) -> None:
        """Print whether an option is active.

        Args:
            enabled: Current state.
            description: Human label for the option.
        """
        label = "With" if enabled else "Without"
        self.out(f"[{label} option '{description}']")

    # -- internals ----------------------------------------------------

    def _rich_styled(
        self,
        message: str,
        *,
        style: str,
        min_level: int,
    ) -> None:
        """Emit a Rich-styled message with timestamp.

        Args:
            message: Text to print.
            style: Rich style string.
            min_level: Minimum verbosity.
        """
        if not self._should_output(min_level):
            return
        with self._output_lock:
            self._log_dispatch(message, is_error=False)
            ts = self._timestamp()
            self._console.print(f"> {ts} : {message}", style=style)

    def _log_dispatch(self, message: str, *, is_error: bool) -> None:
        """Forward a message to the stdlib logger.

        Args:
            message: Text to log.
            is_error: Use `logger.error` when `True`.
        """
        if is_error:
            self._logger.error(message)
        else:
            self._logger.info(message)


# ===================================================================
# Custom argparse help actions
# ===================================================================


class _ShortHelpAction(argparse.Action):
    """Print the short help memo stored on the parser, then exit.

    Registered automatically by `build_parser` or `add_short_help`
    when a *short_help* string is provided.
    """

    def __init__(
        self,
        option_strings: list[str],
        dest: str = argparse.SUPPRESS,
        default: str = argparse.SUPPRESS,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            **kwargs,
        )

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: Any,
        option_string: str | None = None,
    ) -> None:
        """Print short help and exit."""
        text: str = getattr(parser, "_short_help_text", "")
        if text:
            parser._print_message(text.strip() + "\n", sys.stdout)
        else:
            parser.print_help(sys.stdout)
        parser.exit()


class _FullHelpAction(argparse.Action):
    """Print the full argparse help (description + args + epilog), then exit.

    Registered automatically alongside `_ShortHelpAction`.
    """

    def __init__(
        self,
        option_strings: list[str],
        dest: str = argparse.SUPPRESS,
        default: str = argparse.SUPPRESS,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            **kwargs,
        )

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: Any,
        option_string: str | None = None,
    ) -> None:
        """Print full help and exit."""
        parser.print_help(sys.stdout)
        parser.exit()


# ===================================================================
# Custom formatter (preserves indentation & newlines)
# ===================================================================


class PreservingHelpFormatter(argparse.RawTextHelpFormatter):
    """`RawTextHelpFormatter` that cleans bracket noise from Django
    lazy-translation leftovers and adds a leading blank line for
    readability.

    The override of :meth:`_format_text` preserves argparse's standard
    ``%(prog)s`` substitution that the parent class performs before
    formatting. Without it, ``version=`` strings and any description
    or epilog referencing ``%(prog)s`` would be printed literally.
    """

    def _format_text(self, text: str) -> str:
        """Format description / epilog text.

        Args:
            text: Raw text block.

        Returns:
            Cleaned and slightly padded text, with ``%(prog)s``
            substituted when present.
        """
        if not text:
            return ""
        # Preserve argparse's built-in %(prog)s expansion
        if "%(prog)" in text:
            text = text % {"prog": self._prog}
        cleaned = text.replace("[", "").replace("]", "")
        return "\n" + cleaned.strip() + "\n\n"


# ===================================================================
# Parser builder (public API)
# ===================================================================


def build_parser(
    *,
    prog: str = "",
    description: str = "",
    epilog: str = "",
    short_help: str = "",
    formatter_class: type[argparse.HelpFormatter] | None = None,
    **kwargs: Any,
) -> argparse.ArgumentParser:
    """Create an `ArgumentParser` with custom formatting and optional
    split `-h` / `--help`.

    Args:
        prog: Program name shown in the usage line.
        description: Text shown before the argument list.
        epilog: Text shown after the argument list. Whitespace is
            preserved thanks to `PreservingHelpFormatter`.
        short_help: Compact memo displayed by `-h`.  When provided,
            `-h` prints this text and exits while `--help` prints
            the full argparse output.  When empty, `-h` and
            `--help` behave identically.
        formatter_class: Override the formatter (defaults to
            `PreservingHelpFormatter`).
        **kwargs: Forwarded to `ArgumentParser.__init__`.

    Returns:
        Configured `ArgumentParser` instance.
    """
    add_help = not bool(short_help)
    fmt = formatter_class or PreservingHelpFormatter

    parser = argparse.ArgumentParser(
        prog=prog or None,
        description=description or None,
        epilog=epilog or None,
        formatter_class=fmt,
        add_help=add_help,
        **kwargs,
    )

    if short_help:
        add_short_help(parser, short_help)

    return parser


def add_short_help(
    parser: argparse.ArgumentParser,
    short_help: str,
) -> None:
    """Retrofit split `-h` / `--help` onto an existing parser.

    After calling this function:

    - `-h` prints *short_help* and exits.
    - `--help` prints the full argparse help and exits.

    Args:
        parser: Target parser (must have been created with
            `add_help=False`).
        short_help: Compact memo text for `-h`.
    """
    parser._short_help_text = short_help  # type: ignore[attr-defined]
    parser.add_argument(
        "-h",
        action=_ShortHelpAction,
        help="Show short help summary and exit.",
    )
    parser.add_argument(
        "--help",
        action=_FullHelpAction,
        help="Show full help with examples and exit.",
    )


# ===================================================================
# Convenience: CLIApp (combines OutputHandler + argparse)
# ===================================================================


class CLIApp:
    """All-in-one base for a CLI script with output and argument parsing.

    Subclass and override `configure_parser` and `run` to build a
    complete command-line tool with Rich output, custom help, and
    verbosity control.

    Example::

        class MyTool(CLIApp):
            name = "my_tool"
            description = "Import records from CSV."
            epilog = '''
        Examples:
            my_tool data.csv --dry-run
            my_tool data.csv --batch=500
            '''

            def configure_parser(self, parser):
                parser.add_argument("file", help="CSV file to import.")
                parser.add_argument("--dry-run", action="store_true")
                parser.add_argument("--batch", type=int, default=100)

            def run(self, args):
                self.out.success(f"Importing {args.file}")
                if args.dry_run:
                    self.out.warning("Dry-run mode — nothing written.")

        if __name__ == "__main__":
            MyTool().main()

    Attributes:
        name: Program name (shown in the usage line).
        description: Help text before the argument list.
        epilog: Help text after the argument list (whitespace
            preserved).
        short_help: Compact memo for `-h` (leave empty to keep
            `-h` and `--help` identical).
    """

    name: str = ""
    description: str = ""
    epilog: str = ""
    short_help: str = ""

    def __init__(self) -> None:
        self.out: OutputHandler = OutputHandler(verbosity=1)
        self.args: argparse.Namespace | None = None

    def get_epilog(self) -> str:
        """Override to build epilog dynamically at runtime.

        Returns:
            Epilog string or empty for no epilog.
        """
        return self.epilog

    def get_short_help(self) -> str:
        """Override to build short help dynamically at runtime.

        Returns:
            Short help string, or empty for default behavior.
        """
        return self.short_help

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """Add arguments to *parser*. Override in subclasses.

        Args:
            parser: The `ArgumentParser` to configure.
        """

    def run(self, args: argparse.Namespace) -> None:
        """Entry point after argument parsing. Override in subclasses.

        Args:
            args: Parsed command-line arguments.
        """
        raise NotImplementedError("Subclasses must implement run()")

    def main(self, argv: list[str] | None = None) -> None:
        """Parse arguments, set up the output handler, and call `run`.

        Args:
            argv: Argument list (defaults to `sys.argv[1:]`).
        """
        epilog = self.get_epilog()
        short_help = self.get_short_help()

        parser = build_parser(
            prog=self.name,
            description=self.description,
            epilog=epilog,
            short_help=short_help,
        )

        # Standard --verbosity flag
        parser.add_argument(
            "-v",
            "--verbosity",
            type=int,
            choices=[0, 1, 2, 3],
            default=1,
            help="Verbosity level: 0=silent, 1=normal, 2=verbose, 3=debug.",
        )
        parser.add_argument(
            "-n",
            "--no-color",
            action="store_true",
            default=False,
            help="Disable colored output.",
        )

        self.configure_parser(parser)

        parsed = parser.parse_args(argv)
        self.args = parsed
        self.out = OutputHandler(
            verbosity=parsed.verbosity,
            no_color=parsed.no_color,
        )
        self.run(parsed)