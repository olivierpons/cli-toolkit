# cli-toolkit

**言語**:
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

オプションで [Rich](https://github.com/Textualize/rich) をサポートするスレッドセーフな CLI 出力、および `-h`(短いメモ)と `--help`(完全なドキュメント)を分離する `argparse` ヘルパー。

必須の依存関係はありません。Rich はオプトインの追加機能です。

## 機能

- **`OutputHandler`**: スレッドセーフな書き込み、詳細度フィルタリング(0–3)、複数行で整列された自動タイムスタンプ、スタイル付きヘルパー(`success`、`warning`、`error`、`notice`、`debug`)。
- **透過的フォールバックを備えた Rich 統合**: `Table`、`Panel`、`Text`、`Console` が属性として公開されます。Rich が欠落している場合、プレーンテキストの近似が自動的に使用されます。
- **`-h` / `--help` の分離**: `-h` は経験豊富なユーザー向けのコンパクトなメモを表示し、`--help` は完全な argparse ドキュメントを表示します。`--help` がスクロールできないほど長い CLI 向けに設計されています。
- **`NO_COLOR` サポート**: 標準で[標準仕様](https://no-color.org/)を尊重します。
- **標準ロギングブリッジ**: すべての出力呼び出しは、対応するレベルで `logging.getLogger(...)` にもディスパッチされます。

## インストール

GitHub から直接インストール:

```bash
# 最小インストール
pip install git+https://github.com/olivierpons/cli-toolkit.git

# Rich サポート付き
pip install "cli-toolkit[rich] @ git+https://github.com/olivierpons/cli-toolkit.git"

# 特定のバージョンに固定
pip install "git+https://github.com/olivierpons/cli-toolkit.git@v0.1.0"
```

Python 3.14 以上が必要です。

## クイックスタート

```python
from cli_toolkit import OutputHandler, build_parser

# 出力
out = OutputHandler(verbosity=2)
out.success("Server started on port 8080")
out.warning("Cache directory missing, using /tmp")
out.error("Connection refused")
out.debug("request_id=af83c…")

# Rich テーブル(プレーンテキストへの自動フォールバック)
table = out.Table(title="Results")
table.add_column("ID")
table.add_column("Status")
table.add_row("1", "OK")
out.rich_print(table)

# -h / --help 分離のパーサー
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

## API 概要

### `OutputHandler(verbosity=1, *, stdout=None, stderr=None, use_rich=True, no_color=False)`

| メソッド | 説明 | デフォルト `min_level` |
| --- | --- | --- |
| `out(message, **opts)` | 完全な制御を持つ汎用出力 | 1 |
| `success(message)` | 緑の成功行 | 1 |
| `warning(message)` | 黄色の警告行 | 1 |
| `error(message)` | stderr の赤いエラー行 | 0 |
| `notice(message)` | シアンの通知行 | 1 |
| `info(message)` | 青の情報行 | 1 |
| `debug(message)` | マゼンタのデバッグ行、タイムスタンプなし | 3 |
| `verbose(message)` | `out(msg, min_level=2)` のショートハンド | 2 |
| `trace(message)` | `out(msg, min_level=3, without_time=True)` のショートハンド | 3 |
| `thread_error/warning/success(message)` | 現在のスレッド名をプレフィックス | 0/1/1 |
| `rich_print(renderable, *, to_stderr=False)` | スレッドセーフな Rich print | — |

### 詳細度レベル

| レベル | 想定用途 |
| --- | --- |
| `0` | エラーのみ(サイレントモード) |
| `1` | 通常の操作メッセージ |
| `2` | 詳細出力 |
| `3` | デバッグトレース |

### `build_parser(*, prog, description, epilog, short_help, formatter_class=None, **kwargs)`

設定済みの `ArgumentParser` を返します。`short_help` が提供されると、`-h` はコンパクトなメモを表示し、`--help` は完全な argparse 出力(説明 + 引数 + エピログ)を表示します。`short_help` が空の場合、`-h` と `--help` は同じように動作します(標準 argparse)。

### `add_short_help(parser, short_help)`

`add_help=False` で作成された既存のパーサーに `-h` / `--help` 分離を後付けします。

### `CLIApp`

小さな CLI スクリプト用のオールインワン基底クラス。サブクラス化し、`name`、`description`、`epilog`、およびオプションで `short_help` を設定してから、`configure_parser` と `run` をオーバーライドします。完全な例については[モジュールドキュメント文字列](src/cli_toolkit/__init__.py)を参照してください。

## 環境変数

| 変数 | 効果 |
| --- | --- |
| `NO_COLOR` | 任意の値に設定すると、すべての ANSI 色と Rich スタイルを無効にします。[no-color.org](https://no-color.org/) を参照。 |

## 開発

```bash
git clone https://github.com/olivierpons/cli-toolkit.git
cd cli-toolkit
pip install -e ".[rich]"
pip install pytest pytest-cov ruff mypy

# テスト
pytest

# Lint + フォーマット
ruff check .
ruff format .

# 型チェック
mypy src
```

## ライセンス

MIT — [LICENSE](LICENSE) を参照。
