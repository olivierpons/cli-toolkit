# cli-toolkit

**语言**：
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

线程安全的 CLI 输出工具,可选 [Rich](https://github.com/Textualize/rich) 支持,并提供将 `-h`(简短备忘录)与 `--help`(完整文档)分离的 `argparse` 辅助函数。

零必需依赖。Rich 是可选附加项。

## 功能特性

- **`OutputHandler`**:线程安全写入、详细程度分级(0–3)、带对齐多行缩进的自动时间戳、样式化辅助函数(`success`、`warning`、`error`、`notice`、`debug`)。
- **Rich 集成与透明回退**:`Table`、`Panel`、`Text` 和 `Console` 作为属性公开。当 Rich 缺失时,自动使用纯文本近似。
- **`-h` / `--help` 分离**:`-h` 为有经验的用户显示紧凑备忘录,`--help` 显示完整的 argparse 文档。专为 `--help` 过长难以滚动的 CLI 设计。
- **`NO_COLOR` 支持**:开箱即用地遵循[该标准](https://no-color.org/)。
- **标准日志桥接**:每次输出调用也会以匹配级别分发到 `logging.getLogger(...)`。

## 安装

直接从 GitHub 安装:

```bash
# 最小安装
pip install git+https://github.com/olivierpons/cli-toolkit.git

# 带 Rich 支持
pip install "cli-toolkit[rich] @ git+https://github.com/olivierpons/cli-toolkit.git"

# 固定到特定版本
pip install "git+https://github.com/olivierpons/cli-toolkit.git@v0.1.0"
```

需要 Python 3.14 或更高版本。

## 快速开始

```python
from cli_toolkit import OutputHandler, build_parser

# 输出
out = OutputHandler(verbosity=2)
out.success("Server started on port 8080")
out.warning("Cache directory missing, using /tmp")
out.error("Connection refused")
out.debug("request_id=af83c…")

# Rich 表格(自动回退到纯文本)
table = out.Table(title="Results")
table.add_column("ID")
table.add_column("Status")
table.add_row("1", "OK")
out.rich_print(table)

# 带 -h / --help 分离的解析器
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

## API 概览

### `OutputHandler(verbosity=1, *, stdout=None, stderr=None, use_rich=True, no_color=False)`

| 方法 | 说明 | 默认 `min_level` |
| --- | --- | --- |
| `out(message, **opts)` | 具有完全控制的通用输出 | 1 |
| `success(message)` | 绿色成功行 | 1 |
| `warning(message)` | 黄色警告行 | 1 |
| `error(message)` | stderr 上的红色错误行 | 0 |
| `notice(message)` | 青色通知行 | 1 |
| `info(message)` | 蓝色信息行 | 1 |
| `debug(message)` | 洋红色调试行,无时间戳 | 3 |
| `verbose(message)` | `out(msg, min_level=2)` 的简写 | 2 |
| `trace(message)` | `out(msg, min_level=3, without_time=True)` 的简写 | 3 |
| `thread_error/warning/success(message)` | 以当前线程名称为前缀 | 0/1/1 |
| `rich_print(renderable, *, to_stderr=False)` | 线程安全的 Rich 打印 | — |

### 详细程度级别

| 级别 | 预期用途 |
| --- | --- |
| `0` | 仅错误(静默模式) |
| `1` | 正常操作消息 |
| `2` | 详细输出 |
| `3` | 调试跟踪 |

### `build_parser(*, prog, description, epilog, short_help, formatter_class=None, **kwargs)`

返回配置好的 `ArgumentParser`。提供 `short_help` 时,`-h` 打印紧凑备忘录,`--help` 打印完整的 argparse 输出(描述 + 参数 + 尾声)。`short_help` 为空时,`-h` 和 `--help` 行为相同(标准 argparse)。

### `add_short_help(parser, short_help)`

为使用 `add_help=False` 创建的现有解析器后加 `-h` / `--help` 分离。

### `CLIApp`

用于小型 CLI 脚本的一体化基类。继承、设置 `name`、`description`、`epilog` 和可选的 `short_help`,然后覆盖 `configure_parser` 和 `run`。完整示例见[模块文档字符串](src/cli_toolkit/__init__.py)。

## 环境变量

| 变量 | 效果 |
| --- | --- |
| `NO_COLOR` | 设为任意值时,禁用所有 ANSI 颜色和 Rich 样式。见 [no-color.org](https://no-color.org/)。 |

## 开发

```bash
git clone https://github.com/olivierpons/cli-toolkit.git
cd cli-toolkit
pip install -e ".[rich]"
pip install pytest pytest-cov ruff mypy

# 测试
pytest

# 代码检查 + 格式化
ruff check .
ruff format .

# 类型检查
mypy src
```

## 许可证

MIT — 见 [LICENSE](LICENSE)。
