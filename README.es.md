# cli-toolkit

**Idiomas**:
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

Salida CLI thread-safe con soporte opcional de [Rich](https://github.com/Textualize/rich), además de helpers de `argparse` que separan `-h` (memo corto) de `--help` (documentación completa).

Cero dependencias obligatorias. Rich es un extra opt-in.

## Características

- **`OutputHandler`**: escrituras thread-safe, filtrado por nivel de verbosidad (0–3), marcas de tiempo automáticas con sangría multilínea alineada, helpers estilizados (`success`, `warning`, `error`, `notice`, `debug`).
- **Integración Rich con fallback transparente**: `Table`, `Panel`, `Text` y `Console` se exponen como atributos. Cuando Rich falta, se usa automáticamente una aproximación en texto plano.
- **Separación `-h` / `--help`**: `-h` muestra un memo compacto para usuarios experimentados, `--help` muestra la documentación argparse completa. Diseñado para CLIs cuyo `--help` es demasiado largo para desplazarse.
- **Soporte `NO_COLOR`**: respeta [el estándar](https://no-color.org/) de forma predeterminada.
- **Puente al logging estándar**: cada llamada de salida también se despacha a `logging.getLogger(...)` en el nivel correspondiente.

## Instalación

Instalar directamente desde GitHub:

```bash
# Instalación mínima
pip install git+https://github.com/olivierpons/cli-toolkit.git

# Con soporte Rich
pip install "cli-toolkit[rich] @ git+https://github.com/olivierpons/cli-toolkit.git"

# Fijar a una versión específica
pip install "git+https://github.com/olivierpons/cli-toolkit.git@v0.1.0"
```

Requiere Python 3.14 o superior.

## Inicio rápido

```python
from cli_toolkit import OutputHandler, build_parser

# Salida
out = OutputHandler(verbosity=2)
out.success("Server started on port 8080")
out.warning("Cache directory missing, using /tmp")
out.error("Connection refused")
out.debug("request_id=af83c…")

# Tabla Rich (fallback automático a texto plano)
table = out.Table(title="Results")
table.add_column("ID")
table.add_column("Status")
table.add_row("1", "OK")
out.rich_print(table)

# Parser con -h / --help separados
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

## Descripción general de la API

### `OutputHandler(verbosity=1, *, stdout=None, stderr=None, use_rich=True, no_color=False)`

| Método | Descripción | `min_level` predeterminado |
| --- | --- | --- |
| `out(message, **opts)` | Salida de propósito general con control completo | 1 |
| `success(message)` | Línea verde de éxito | 1 |
| `warning(message)` | Línea amarilla de advertencia | 1 |
| `error(message)` | Línea roja de error en stderr | 0 |
| `notice(message)` | Línea cian de aviso | 1 |
| `info(message)` | Línea azul informativa | 1 |
| `debug(message)` | Línea magenta de depuración, sin marca de tiempo | 3 |
| `verbose(message)` | Atajo para `out(msg, min_level=2)` | 2 |
| `trace(message)` | Atajo para `out(msg, min_level=3, without_time=True)` | 3 |
| `thread_error/warning/success(message)` | Prefijado con el nombre del hilo actual | 0/1/1 |
| `rich_print(renderable, *, to_stderr=False)` | Print Rich thread-safe | — |

### Niveles de verbosidad

| Nivel | Uso previsto |
| --- | --- |
| `0` | Solo errores (modo silencioso) |
| `1` | Mensajes de operación normal |
| `2` | Salida detallada |
| `3` | Trazas de depuración |

### `build_parser(*, prog, description, epilog, short_help, formatter_class=None, **kwargs)`

Retorna un `ArgumentParser` configurado. Cuando se proporciona `short_help`, `-h` imprime el memo compacto y `--help` imprime la salida argparse completa (descripción + argumentos + epílogo). Cuando `short_help` está vacío, `-h` y `--help` se comportan de forma idéntica (argparse estándar).

### `add_short_help(parser, short_help)`

Adapta la separación `-h` / `--help` en un parser existente creado con `add_help=False`.

### `CLIApp`

Clase base todo-en-uno para scripts CLI pequeños. Subclasificar, establecer `name`, `description`, `epilog` y opcionalmente `short_help`, luego sobrescribir `configure_parser` y `run`. Vea el [docstring del módulo](src/cli_toolkit/__init__.py) para un ejemplo completo.

## Variables de entorno

| Variable | Efecto |
| --- | --- |
| `NO_COLOR` | Cuando se establece en cualquier valor, deshabilita todos los colores ANSI y el estilo Rich. Vea [no-color.org](https://no-color.org/). |

## Desarrollo

```bash
git clone https://github.com/olivierpons/cli-toolkit.git
cd cli-toolkit
pip install -e ".[rich]"
pip install pytest pytest-cov ruff mypy

# Tests
pytest

# Lint + formato
ruff check .
ruff format .

# Verificación de tipos
mypy src
```

## Licencia

MIT — ver [LICENSE](LICENSE).
