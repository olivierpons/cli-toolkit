# cli-toolkit

**Languages**:
[English](README.md) ·
[Français](README.fr.md) ·
[Deutsch](README.de.md) ·
[中文](README.zh.md) ·
[日本語](README.ja.md) ·
[Italiano](README.it.md) ·
[Español](README.es.md)

[![Python versions](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/olivierpons/cli-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/olivierpons/cli-toolkit/actions/workflows/ci.yml)

Thread-safe CLI output with optional [Rich](https://github.com/Textualize/rich) support, plus `argparse` helpers that split `-h` (short memo) from `--help` (full documentation).

Zero required dependencies. Rich is an opt-in extra.

## Features

- **`OutputHandler`**: thread-safe writes, verbosity gating (0–3), automatic timestamps with aligned multi-line indentation, styled helpers (`success`, `warning`, `error`, `notice`, `debug`).
- **Rich integration with transparent fallback**: `Table`, `Panel`, `Text`, and `Console` are exposed as attributes. When Rich is missing, a plain-text approximation is used automatically.
- **Split `-h` / `--help`**: `-h` shows a compact memo for experienced users, `--help` shows the full argparse documentation. Designed for CLIs where `--help` is too long to scroll.
- **`NO_COLOR` support**: respects [the standard](https://no-color.org/) out of the box.
- **Standard logging bridge**: every output call also dispatches to `logging.getLogger(...)` at the matching level.

## Installation

Install directly from GitHub:

```bash
# Minimal install
pip install git+https://github.com/olivierpons/cli-toolkit.git

# With Rich support
pip install "cli-toolkit[rich] @ git+https://github.com/olivierpons/cli-toolkit.git"

# Pin to a specific version
pip install "git+https://github.com/olivierpons/cli-toolkit.git@v0.1.0"
```

Requires Python 3.14 or newer.

## Quick start

```python
from cli_toolkit import OutputHandler, build_parser

# Output
out = OutputHandler(verbosity=2)
out.success("Server started on port 8080")
out.warning("Cache directory missing, using /tmp")
out.error("Connection refused")
out.debug("request_id=af83c…")

# Rich table (auto-fallback to plain text)
table = out.Table(title="Results")
table.add_column("ID")
table.add_column("Status")
table.add_row("1", "OK")
out.rich_print(table)

# Parser with split -h / --help
parser = build_parser(
    prog="my_tool",
    description="Process uploaded files.",
    short_help="""
my_tool — Process uploaded files

  --all      Process everything
  --id N     Process a specific file

Use --help for full documentation.
""",
    epilog="""
EXAMPLES
  my_tool --all
  my_tool --id=42
""",
)
parser.add_argument("--all", action="store_true")
parser.add_argument("--id", type=int)
args = parser.parse_args()
```

## API overview

### `OutputHandler(verbosity=1, *, stdout=None, stderr=None, use_rich=True, no_color=False)`

| Method | Description | Default `min_level` |
| --- | --- | --- |
| `out(message, **opts)` | General-purpose output with full control | 1 |
| `success(message)` | Green success line | 1 |
| `warning(message)` | Yellow warning line | 1 |
| `error(message)` | Red error line on stderr | 0 |
| `notice(message)` | Cyan notice line | 1 |
| `info(message)` | Blue info line | 1 |
| `debug(message)` | Magenta debug line, no timestamp | 3 |
| `verbose(message)` | Shorthand for `out(msg, min_level=2)` | 2 |
| `trace(message)` | Shorthand for `out(msg, min_level=3, without_time=True)` | 3 |
| `thread_error/warning/success(message)` | Prefixed with current thread name | 0/1/1 |
| `rich_print(renderable, *, to_stderr=False)` | Thread-safe Rich print | — |

### Verbosity levels

| Level | Intended use |
| --- | --- |
| `0` | Errors only (silent mode) |
| `1` | Normal operation messages |
| `2` | Verbose / detailed output |
| `3` | Debug traces |

### `build_parser(*, prog, description, epilog, short_help, formatter_class=None, **kwargs)`

Returns a configured `ArgumentParser`. When `short_help` is provided, `-h` prints the compact memo and `--help` prints the full argparse output (description + arguments + epilog). When `short_help` is empty, `-h` and `--help` behave identically (standard argparse).

### `add_short_help(parser, short_help)`

Retrofits split `-h` / `--help` onto an existing parser created with `add_help=False`.

### `CLIApp`

All-in-one base class for small CLI scripts. Subclass, set `name`, `description`, `epilog`, and optionally `short_help`, then override `configure_parser` and `run`. See the [module docstring](src/cli_toolkit/__init__.py) for a complete example.

## Environment variables

| Variable | Effect |
| --- | --- |
| `NO_COLOR` | When set to any value, disables all ANSI colors and Rich styling. See [no-color.org](https://no-color.org/). |

## Development

```bash
git clone https://github.com/olivierpons/cli-toolkit.git
cd cli-toolkit
pip install -e ".[rich]"
pip install pytest pytest-cov ruff mypy

# Tests
pytest

# Lint + format
ruff check .
ruff format .

# Type check
mypy src
```

## License

MIT — see [LICENSE](LICENSE).
