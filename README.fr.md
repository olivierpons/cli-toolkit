# cli-toolkit

**Langues** :
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

Sortie CLI thread-safe avec prise en charge optionnelle de [Rich](https://github.com/Textualize/rich), ainsi que des helpers `argparse` qui séparent `-h` (mémo court) de `--help` (documentation complète).

Zéro dépendance obligatoire. Rich est un extra opt-in.

## Fonctionnalités

- **`OutputHandler`** : écritures thread-safe, filtrage par verbosité (0–3), horodatage automatique avec indentation alignée sur plusieurs lignes, helpers stylisés (`success`, `warning`, `error`, `notice`, `debug`).
- **Intégration Rich avec fallback transparent** : `Table`, `Panel`, `Text`, et `Console` sont exposés comme attributs. Quand Rich est absent, une approximation en texte brut est utilisée automatiquement.
- **Split `-h` / `--help`** : `-h` affiche un mémo compact pour les utilisateurs expérimentés, `--help` affiche la documentation argparse complète. Conçu pour les CLI dont `--help` est trop long à faire défiler.
- **Support `NO_COLOR`** : respecte [le standard](https://no-color.org/) par défaut.
- **Pont vers le logging standard** : chaque appel de sortie est aussi dispatché vers `logging.getLogger(...)` au niveau correspondant.

## Installation

Installation directe depuis GitHub :

```bash
# Installation minimale
pip install git+https://github.com/olivierpons/cli-toolkit.git

# Avec le support Rich
pip install "cli-toolkit[rich] @ git+https://github.com/olivierpons/cli-toolkit.git"

# Fixer une version spécifique
pip install "git+https://github.com/olivierpons/cli-toolkit.git@v0.1.0"
```

Nécessite Python 3.14 ou supérieur.

## Démarrage rapide

```python
from cli_toolkit import OutputHandler, build_parser

# Sortie
out = OutputHandler(verbosity=2)
out.success("Server started on port 8080")
out.warning("Cache directory missing, using /tmp")
out.error("Connection refused")
out.debug("request_id=af83c…")

# Table Rich (fallback automatique en texte brut)
table = out.Table(title="Results")
table.add_column("ID")
table.add_column("Status")
table.add_row("1", "OK")
out.rich_print(table)

# Parser avec split -h / --help
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

## Aperçu de l'API

### `OutputHandler(verbosity=1, *, stdout=None, stderr=None, use_rich=True, no_color=False)`

| Méthode | Description | `min_level` par défaut |
| --- | --- | --- |
| `out(message, **opts)` | Sortie générale avec contrôle complet | 1 |
| `success(message)` | Ligne verte de succès | 1 |
| `warning(message)` | Ligne jaune d'avertissement | 1 |
| `error(message)` | Ligne rouge d'erreur sur stderr | 0 |
| `notice(message)` | Ligne cyan de notice | 1 |
| `info(message)` | Ligne bleue d'information | 1 |
| `debug(message)` | Ligne magenta de debug, sans horodatage | 3 |
| `verbose(message)` | Raccourci pour `out(msg, min_level=2)` | 2 |
| `trace(message)` | Raccourci pour `out(msg, min_level=3, without_time=True)` | 3 |
| `thread_error/warning/success(message)` | Préfixé par le nom du thread courant | 0/1/1 |
| `rich_print(renderable, *, to_stderr=False)` | Print Rich thread-safe | — |

### Niveaux de verbosité

| Niveau | Usage prévu |
| --- | --- |
| `0` | Erreurs seulement (mode silencieux) |
| `1` | Messages d'opération normale |
| `2` | Sortie verbose / détaillée |
| `3` | Traces de debug |

### `build_parser(*, prog, description, epilog, short_help, formatter_class=None, **kwargs)`

Retourne un `ArgumentParser` configuré. Quand `short_help` est fourni, `-h` imprime le mémo compact et `--help` imprime la sortie argparse complète (description + arguments + epilog). Quand `short_help` est vide, `-h` et `--help` se comportent de façon identique (argparse standard).

### `add_short_help(parser, short_help)`

Ajoute le split `-h` / `--help` à un parser existant créé avec `add_help=False`.

### `CLIApp`

Classe de base tout-en-un pour les petits scripts CLI. Sous-classer, définir `name`, `description`, `epilog`, et optionnellement `short_help`, puis surcharger `configure_parser` et `run`. Voir le [docstring du module](src/cli_toolkit/__init__.py) pour un exemple complet.

## Variables d'environnement

| Variable | Effet |
| --- | --- |
| `NO_COLOR` | Quand définie à n'importe quelle valeur, désactive toutes les couleurs ANSI et le style Rich. Voir [no-color.org](https://no-color.org/). |

## Développement

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

# Vérification de types
mypy src
```

## Licence

MIT — voir [LICENSE](LICENSE).
