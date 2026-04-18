# cli-toolkit

**Lingue**:
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

Output CLI thread-safe con supporto opzionale per [Rich](https://github.com/Textualize/rich), più helper `argparse` che separano `-h` (memo breve) da `--help` (documentazione completa).

Zero dipendenze obbligatorie. Rich è un extra opt-in.

## Funzionalità

- **`OutputHandler`**: scritture thread-safe, filtro per livello di verbosità (0–3), timestamp automatici con indentazione multi-linea allineata, helper stilizzati (`success`, `warning`, `error`, `notice`, `debug`).
- **Integrazione Rich con fallback trasparente**: `Table`, `Panel`, `Text` e `Console` sono esposti come attributi. Quando Rich manca, viene utilizzata automaticamente un'approssimazione in testo semplice.
- **Separazione `-h` / `--help`**: `-h` mostra un memo compatto per utenti esperti, `--help` mostra la documentazione argparse completa. Progettato per CLI il cui `--help` è troppo lungo da scorrere.
- **Supporto `NO_COLOR`**: rispetta [lo standard](https://no-color.org/) di default.
- **Ponte verso logging standard**: ogni chiamata di output viene anche dispatchata verso `logging.getLogger(...)` al livello corrispondente.

## Installazione

Installa direttamente da GitHub:

```bash
# Installazione minima
pip install git+https://github.com/olivierpons/cli-toolkit.git

# Con supporto Rich
pip install "cli-toolkit[rich] @ git+https://github.com/olivierpons/cli-toolkit.git"

# Fissa una versione specifica
pip install "git+https://github.com/olivierpons/cli-toolkit.git@v0.1.0"
```

Richiede Python 3.14 o superiore.

## Avvio rapido

```python
from cli_toolkit import OutputHandler, build_parser

# Output
out = OutputHandler(verbosity=2)
out.success("Server started on port 8080")
out.warning("Cache directory missing, using /tmp")
out.error("Connection refused")
out.debug("request_id=af83c…")

# Tabella Rich (fallback automatico a testo semplice)
table = out.Table(title="Results")
table.add_column("ID")
table.add_column("Status")
table.add_row("1", "OK")
out.rich_print(table)

# Parser con -h / --help separati
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

## Panoramica dell'API

### `OutputHandler(verbosity=1, *, stdout=None, stderr=None, use_rich=True, no_color=False)`

| Metodo | Descrizione | `min_level` predefinito |
| --- | --- | --- |
| `out(message, **opts)` | Output generico con controllo completo | 1 |
| `success(message)` | Linea verde di successo | 1 |
| `warning(message)` | Linea gialla di avvertimento | 1 |
| `error(message)` | Linea rossa di errore su stderr | 0 |
| `notice(message)` | Linea ciano di avviso | 1 |
| `info(message)` | Linea blu informativa | 1 |
| `debug(message)` | Linea magenta di debug, senza timestamp | 3 |
| `verbose(message)` | Abbreviazione per `out(msg, min_level=2)` | 2 |
| `trace(message)` | Abbreviazione per `out(msg, min_level=3, without_time=True)` | 3 |
| `thread_error/warning/success(message)` | Prefissato con il nome del thread corrente | 0/1/1 |
| `rich_print(renderable, *, to_stderr=False)` | Print Rich thread-safe | — |

### Livelli di verbosità

| Livello | Uso previsto |
| --- | --- |
| `0` | Solo errori (modalità silenziosa) |
| `1` | Messaggi di operazione normale |
| `2` | Output dettagliato |
| `3` | Tracce di debug |

### `build_parser(*, prog, description, epilog, short_help, formatter_class=None, **kwargs)`

Restituisce un `ArgumentParser` configurato. Quando viene fornito `short_help`, `-h` stampa il memo compatto e `--help` stampa l'output argparse completo (descrizione + argomenti + epilogo). Quando `short_help` è vuoto, `-h` e `--help` si comportano in modo identico (argparse standard).

### `add_short_help(parser, short_help)`

Aggiunge la separazione `-h` / `--help` a un parser esistente creato con `add_help=False`.

### `CLIApp`

Classe base tutto-in-uno per piccoli script CLI. Sottoclassare, impostare `name`, `description`, `epilog` e opzionalmente `short_help`, poi sovrascrivere `configure_parser` e `run`. Vedi la [docstring del modulo](src/cli_toolkit/__init__.py) per un esempio completo.

## Variabili d'ambiente

| Variabile | Effetto |
| --- | --- |
| `NO_COLOR` | Quando impostata a qualsiasi valore, disabilita tutti i colori ANSI e lo stile Rich. Vedi [no-color.org](https://no-color.org/). |

## Sviluppo

```bash
git clone https://github.com/olivierpons/cli-toolkit.git
cd cli-toolkit
pip install -e ".[rich]"
pip install pytest pytest-cov ruff mypy

# Test
pytest

# Lint + formattazione
ruff check .
ruff format .

# Controllo dei tipi
mypy src
```

## Licenza

MIT — vedi [LICENSE](LICENSE).
