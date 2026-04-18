"""Tests for the OutputHandler class."""

from __future__ import annotations

import io
import threading

import pytest

from cli_toolkit import OutputHandler


def test_verbosity_gating_silences_level_1_messages() -> None:
    """A verbosity of 0 must hide level-1 messages like success/notice."""
    stdout: io.StringIO = io.StringIO()
    stderr: io.StringIO = io.StringIO()
    out: OutputHandler = OutputHandler(
        verbosity=0, stdout=stdout, stderr=stderr, use_rich=False
    )
    out.success("should not appear")
    out.warning("should not appear")
    out.notice("should not appear")
    assert stdout.getvalue() == ""


def test_error_is_written_to_stderr_even_at_verbosity_zero() -> None:
    """Errors default to min_level=0, so they bypass silent mode."""
    stdout: io.StringIO = io.StringIO()
    stderr: io.StringIO = io.StringIO()
    out: OutputHandler = OutputHandler(
        verbosity=0, stdout=stdout, stderr=stderr, use_rich=False
    )
    out.error("something broke")
    assert "something broke" in stderr.getvalue()
    assert "something broke" not in stdout.getvalue()


def test_verbosity_is_clamped_to_valid_range() -> None:
    """Out-of-range verbosity values are clamped to the 0..3 window."""
    out: OutputHandler = OutputHandler(verbosity=99, use_rich=False)
    assert out.verbosity == 3
    out = OutputHandler(verbosity=-5, use_rich=False)
    assert out.verbosity == 0


def test_no_color_flag_disables_ansi_sequences() -> None:
    """When no_color is True, ANSI escape codes must not appear."""
    stdout: io.StringIO = io.StringIO()
    out: OutputHandler = OutputHandler(
        verbosity=1, stdout=stdout, use_rich=False, no_color=True
    )
    out.success("plain message")
    assert "\033[" not in stdout.getvalue()


def test_has_rich_flag_matches_runtime_setup() -> None:
    """has_rich must reflect the actual rendering path chosen."""
    out: OutputHandler = OutputHandler(verbosity=1, use_rich=False)
    assert out.has_rich is False


def test_rich_print_handles_string_renderable() -> None:
    """rich_print must accept a plain string and write it to stdout."""
    stdout: io.StringIO = io.StringIO()
    out: OutputHandler = OutputHandler(verbosity=1, stdout=stdout, use_rich=False)
    out.rich_print("hello world")
    assert "hello world" in stdout.getvalue()


def test_concurrent_output_does_not_interleave_characters() -> None:
    """The output lock must serialize concurrent writes from threads."""
    stdout: io.StringIO = io.StringIO()
    out: OutputHandler = OutputHandler(verbosity=1, stdout=stdout, use_rich=False)

    def worker(index: int) -> None:
        for _ in range(50):
            out.success(f"thread-{index}")

    threads: list[threading.Thread] = [
        threading.Thread(target=worker, args=(i,)) for i in range(4)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    lines: list[str] = stdout.getvalue().splitlines()
    assert len(lines) == 200
    for line in lines:
        assert "thread-" in line


@pytest.mark.parametrize(
    "method_name",
    ["success", "warning", "notice", "info", "verbose", "debug"],
)
def test_output_methods_accept_string_argument(method_name: str) -> None:
    """Every output method must be callable with a plain string message."""
    stdout: io.StringIO = io.StringIO()
    stderr: io.StringIO = io.StringIO()
    out: OutputHandler = OutputHandler(
        verbosity=3, stdout=stdout, stderr=stderr, use_rich=False
    )
    method = getattr(out, method_name)
    method("test message")
    combined: str = stdout.getvalue() + stderr.getvalue()
    assert "test message" in combined
