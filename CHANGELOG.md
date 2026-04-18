# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-04-18

### Added

- Initial public release.
- `OutputHandler`: thread-safe, verbosity-aware console output with
  optional Rich support and ANSI fallback.
- `build_parser` and `add_short_help`: argparse helpers with split
  `-h` (compact memo) and `--help` (full documentation).
- `PreservingHelpFormatter`: `RawTextHelpFormatter` that preserves
  `%(prog)s` substitution while cleaning up description and epilog
  whitespace.
- `CLIApp`: all-in-one base class combining `OutputHandler` with a
  configured argument parser for simple CLI scripts.

[Unreleased]: https://github.com/olivierpons/cli-toolkit/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/olivierpons/cli-toolkit/releases/tag/v0.1.0
