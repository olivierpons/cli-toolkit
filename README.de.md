# cli-toolkit

**Sprachen**:
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

Thread-sichere CLI-Ausgabe mit optionaler [Rich](https://github.com/Textualize/rich)-Unterstützung, plus `argparse`-Helper, die `-h` (Kurzmemo) von `--help` (vollständige Dokumentation) trennen.

Null erforderliche Abhängigkeiten. Rich ist ein optionales Extra.

## Funktionen

- **`OutputHandler`**: thread-sichere Schreibvorgänge, Ausführlichkeitsfilter (0–3), automatische Zeitstempel mit ausgerichteter mehrzeiliger Einrückung, stilisierte Helfer (`success`, `warning`, `error`, `notice`, `debug`).
- **Rich-Integration mit transparentem Fallback**: `Table`, `Panel`, `Text` und `Console` werden als Attribute bereitgestellt. Fehlt Rich, wird automatisch eine Nur-Text-Annäherung verwendet.
- **Geteiltes `-h` / `--help`**: `-h` zeigt ein kompaktes Memo für erfahrene Benutzer, `--help` zeigt die vollständige argparse-Dokumentation. Entwickelt für CLIs, deren `--help` zu lang zum Scrollen ist.
- **`NO_COLOR`-Unterstützung**: respektiert [den Standard](https://no-color.org/) von Haus aus.
- **Standard-Logging-Brücke**: Jeder Ausgabeaufruf wird zusätzlich an `logging.getLogger(...)` auf der passenden Stufe weitergeleitet.

## Installation

Direkt von GitHub installieren:

```bash
# Minimalinstallation
pip install git+https://github.com/olivierpons/cli-toolkit.git

# Mit Rich-Unterstützung
pip install "cli-toolkit[rich] @ git+https://github.com/olivierpons/cli-toolkit.git"

# Auf eine bestimmte Version festlegen
pip install "git+https://github.com/olivierpons/cli-toolkit.git@v0.1.0"
```

Benötigt Python 3.14 oder neuer.

## Schnellstart

```python
from cli_toolkit import OutputHandler, build_parser

# Ausgabe
out = OutputHandler(verbosity=2)
out.success("Server started on port 8080")
out.warning("Cache directory missing, using /tmp")
out.error("Connection refused")
out.debug("request_id=af83c…")

# Rich-Tabelle (automatischer Fallback auf Nur-Text)
table = out.Table(title="Results")
table.add_column("ID")
table.add_column("Status")
table.add_row("1", "OK")
out.rich_print(table)

# Parser mit geteiltem -h / --help
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

## API-Übersicht

### `OutputHandler(verbosity=1, *, stdout=None, stderr=None, use_rich=True, no_color=False)`

| Methode | Beschreibung | Standard `min_level` |
| --- | --- | --- |
| `out(message, **opts)` | Allzweck-Ausgabe mit voller Kontrolle | 1 |
| `success(message)` | Grüne Erfolgszeile | 1 |
| `warning(message)` | Gelbe Warnzeile | 1 |
| `error(message)` | Rote Fehlerzeile auf stderr | 0 |
| `notice(message)` | Cyanfarbene Hinweiszeile | 1 |
| `info(message)` | Blaue Infozeile | 1 |
| `debug(message)` | Magenta-Debug-Zeile, ohne Zeitstempel | 3 |
| `verbose(message)` | Abkürzung für `out(msg, min_level=2)` | 2 |
| `trace(message)` | Abkürzung für `out(msg, min_level=3, without_time=True)` | 3 |
| `thread_error/warning/success(message)` | Mit aktuellem Threadnamen präfixiert | 0/1/1 |
| `rich_print(renderable, *, to_stderr=False)` | Thread-sicheres Rich-Print | — |

### Ausführlichkeitsstufen

| Stufe | Verwendungszweck |
| --- | --- |
| `0` | Nur Fehler (stiller Modus) |
| `1` | Normale Betriebsmeldungen |
| `2` | Ausführliche/detaillierte Ausgabe |
| `3` | Debug-Traces |

### `build_parser(*, prog, description, epilog, short_help, formatter_class=None, **kwargs)`

Gibt einen konfigurierten `ArgumentParser` zurück. Wenn `short_help` angegeben ist, druckt `-h` das kompakte Memo und `--help` die vollständige argparse-Ausgabe (Beschreibung + Argumente + Epilog). Wenn `short_help` leer ist, verhalten sich `-h` und `--help` identisch (Standard-argparse).

### `add_short_help(parser, short_help)`

Rüstet das geteilte `-h` / `--help` auf einem bestehenden Parser nach, der mit `add_help=False` erstellt wurde.

### `CLIApp`

Allround-Basisklasse für kleine CLI-Skripte. Ableiten, `name`, `description`, `epilog` und optional `short_help` setzen, dann `configure_parser` und `run` überschreiben. Siehe [Modul-Docstring](src/cli_toolkit/__init__.py) für ein vollständiges Beispiel.

## Umgebungsvariablen

| Variable | Wirkung |
| --- | --- |
| `NO_COLOR` | Wenn auf einen beliebigen Wert gesetzt, werden alle ANSI-Farben und das Rich-Styling deaktiviert. Siehe [no-color.org](https://no-color.org/). |

## Entwicklung

```bash
git clone https://github.com/olivierpons/cli-toolkit.git
cd cli-toolkit
pip install -e ".[rich]"
pip install pytest pytest-cov ruff mypy

# Tests
pytest

# Lint + Formatierung
ruff check .
ruff format .

# Typprüfung
mypy src
```

## Lizenz

MIT — siehe [LICENSE](LICENSE).
