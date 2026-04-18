"""Tests for build_parser, add_short_help, and PreservingHelpFormatter."""

from __future__ import annotations

import argparse
import io

import pytest

from cli_toolkit import PreservingHelpFormatter, add_short_help, build_parser


def test_build_parser_without_short_help_keeps_standard_argparse_behaviour() -> None:
    """-h and --help should behave identically when short_help is empty."""
    parser: argparse.ArgumentParser = build_parser(
        prog="tool", description="A tool."
    )
    with pytest.raises(SystemExit):
        parser.parse_args(["--help"])


def test_short_help_option_prints_compact_memo_and_exits() -> None:
    """-h must print the short_help text verbatim, not the full help."""
    parser: argparse.ArgumentParser = build_parser(
        prog="tool",
        description="A tool.",
        short_help="SHORT MEMO GOES HERE",
    )
    buffer: io.StringIO = io.StringIO()
    parser._print_message = lambda msg, _file=None: buffer.write(msg)  # type: ignore[method-assign]
    with pytest.raises(SystemExit):
        parser.parse_args(["-h"])
    assert "SHORT MEMO GOES HERE" in buffer.getvalue()


def test_full_help_option_prints_argparse_default() -> None:
    """--help must print the full argparse-generated help."""
    parser: argparse.ArgumentParser = build_parser(
        prog="tool",
        description="A tool.",
        short_help="SHORT MEMO",
    )
    buffer: io.StringIO = io.StringIO()
    parser._print_message = lambda msg, _file=None: buffer.write(msg)  # type: ignore[method-assign]
    with pytest.raises(SystemExit):
        parser.parse_args(["--help"])
    output: str = buffer.getvalue()
    assert "A tool." in output
    assert "SHORT MEMO" not in output


def test_version_action_substitutes_prog_name() -> None:
    """PreservingHelpFormatter must preserve %(prog)s substitution.

    Regression test: the formatter override must not break argparse's
    built-in version string expansion.
    """
    parser: argparse.ArgumentParser = build_parser(
        prog="awesome-tool", description="test"
    )
    parser.add_argument(
        "-V", "--version", action="version", version="%(prog)s 1.2.3"
    )
    buffer: io.StringIO = io.StringIO()
    parser._print_message = lambda msg, _file=None: buffer.write(msg)  # type: ignore[method-assign]
    with pytest.raises(SystemExit):
        parser.parse_args(["--version"])
    assert "awesome-tool 1.2.3" in buffer.getvalue()


def test_epilog_substitutes_prog_name() -> None:
    """The epilog should also expand %(prog)s."""
    parser: argparse.ArgumentParser = build_parser(
        prog="my-cmd",
        description="Does things.",
        epilog="Run %(prog)s --help for details.",
    )
    buffer: io.StringIO = io.StringIO()
    parser._print_message = lambda msg, _file=None: buffer.write(msg)  # type: ignore[method-assign]
    with pytest.raises(SystemExit):
        parser.parse_args(["--help"])
    assert "Run my-cmd --help for details." in buffer.getvalue()


def test_preserving_formatter_strips_bracket_noise() -> None:
    """PreservingHelpFormatter must strip square-bracket noise."""
    formatter: PreservingHelpFormatter = PreservingHelpFormatter(prog="tool")
    result: str = formatter._format_text("Hello [world] from [Django]")
    assert "[" not in result
    assert "]" not in result
    assert "Hello world from Django" in result


def test_add_short_help_retrofits_on_existing_parser() -> None:
    """add_short_help should work on a parser built with add_help=False."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser(add_help=False)
    add_short_help(parser, "custom short help text")
    buffer: io.StringIO = io.StringIO()
    parser._print_message = lambda msg, _file=None: buffer.write(msg)  # type: ignore[method-assign]
    with pytest.raises(SystemExit):
        parser.parse_args(["-h"])
    assert "custom short help text" in buffer.getvalue()
