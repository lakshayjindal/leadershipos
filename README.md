# Leadership OS

A local-first personal execution system that minimizes cognitive load.

## Features

- Morning planning workflow
- Focus timer with work session tracking
- Break management
- End-of-day review with Markdown journal generation
- System tray with floating overlay
- Keyboard-first design

## Installation

```bash
# Install with uv (recommended)
uv sync

# Or with pip
pip install -e ".[dev]"
```

## Development

```bash
# Run tests
python -m pytest tests/ -v

# Lint
ruff check src/ tests/

# Type check
pyright src/
```

## License

MIT
