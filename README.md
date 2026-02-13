# Conventions CLI

A command-line tool that automatically discovers and documents coding conventions in your codebase. It analyzes your source code to detect patterns, rates them on a 1-5 scale, and provides actionable improvement suggestions.

## Features

- **Automatic Convention Detection**: Scans your codebase to identify coding patterns and conventions
- **Multi-Language Support**: Python, Go, Node.js/TypeScript, and Rust
- **Cross-Language Detection**: CI/CD, Git conventions, Docker, Kubernetes, and more
- **Convention Rating**: Rates each convention on a 1-5 scale (Poor to Excellent)
- **Improvement Suggestions**: Provides actionable suggestions for conventions that could be improved
- **CLAUDE.md Generation**: Generate agent-optimized context files for Claude Code
- **Multiple Output Formats**: JSON, Markdown, HTML reports, SARIF, and CLAUDE.md
- **Configuration File Support**: Customize behavior with `.conventionsrc.json`
- **Plugin System**: Extend with custom detectors and rating rules

## Installation & Usage

### Using pipx (Recommended)

[pipx](https://pipx.pypa.io/) installs CLI tools in isolated environments:

```bash
# Install pipx if you don't have it
brew install pipx  # macOS
# or: pip install --user pipx

# Install conventions-cli
pipx install conventions-cli
```

### Using pip

```bash
# In a virtual environment
pip install conventions-cli

# Or with --user flag
pip install --user conventions-cli
```

### From Source

```bash
git clone https://github.com/steph-dove/conventions.git
cd conventions
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Requirements

- Python 3.10 or higher

### Quick Start

```bash
# Scan the current directory
conventions discover

# Scan a specific repository
conventions discover -r /path/to/your/repo
```

### Typical Workflow

1. **Discover**: Run `conventions discover` on your repo
2. **Review**: Check `.conventions/conventions-review.md` for ratings and suggestions
3. **Improve**: Address the issues listed in "Improvement Priorities"
4. **Re-run**: Run discovery again to verify improvements
5. **Track**: Add `.conventions/` to version control to track conventions over time

### Command Options

| Option | Short | Description |
|--------|-------|-------------|
| `--repo` | `-r` | Path to repository root (default: current directory) |
| `--languages` | `-l` | Comma-separated list of languages to scan |
| `--max-files` | | Maximum files to scan (default: 2000) |
| `--verbose` | `-v` | Enable verbose output |
| `--quiet` | `-q` | Suppress output except errors |
| `--detailed` | `-d` | Show detailed rule information |
| `--config` | `-c` | Path to configuration file |
| `--ignore-config` | | Ignore configuration file even if present |
| `--format` | | Output format(s): json, markdown, review, html, sarif, claude |
| `--claude` | | Generate CLAUDE.md in `.claude/` directory |
| `--init` | | Enrich CLAUDE.md using Claude Code CLI (requires `claude` installed) |

## CLAUDE.md Generation

Generate an agent-optimized context file for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) containing project overview, directory structure, architecture patterns, tech stack, commands, conventions, and deployment info — structured to help AI coding agents understand your codebase quickly.

```bash
# Generate CLAUDE.md in .claude/ directory
conventions discover --claude

# Or include with other formats (writes to project root)
conventions discover --format claude
```

### Enhanced with `--init`

Add the `--init` flag to enrich the generated CLAUDE.md using the Claude Code CLI. This pipes the static-analysis output through Claude, which reads your actual codebase to fill in runnable commands, an architecture narrative, known pitfalls, and a decision log — turning a good starting point into a comprehensive project guide.

```bash
conventions discover --claude --init
```

Requires the Claude Code CLI (`npm install -g @anthropic-ai/claude-code`).

## Language Support

| Language | Conventions | Categories |
|----------|-------------|------------|
| **Python** | 70+ | typing, docs, testing, logging, errors, security, async, architecture, API, DI, database, CLI, caching, GraphQL, code style, validation, tooling, resilience |
| **Node.js/TypeScript** | 45+ | TypeScript, testing, logging, errors, security, async, architecture, API, frontend, state management, tooling, data flow, migrations |
| **Go** | 40+ | modules, testing, logging, errors, security, concurrency, architecture, API, patterns, CLI, gRPC, DI, data flow, migrations |
| **Rust** | 15+ | Cargo, testing, errors, async, web, CLI, serialization, docs, unsafe, macros, logging, database, data flow |
| **Generic** | 20+ | CI/CD, Git, Docker, Kubernetes, editor config, repo layout, task runners, code ownership, environment setup, generated code |

For the full list of convention IDs, see the [Convention ID Reference](docs/conventions-reference.md).

## Example Output

```
╭───────────────────────────────╮
│ Conventions Detection Summary │
╰───────────────────────────────╯

Repository: /path/to/your/repo
Languages: node, python
Files scanned: 150
Rules detected: 38
Warnings: 0

Detected Conventions:

┃ ID                              ┃ Title              ┃ Confidence ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ node.conventions.formatting     │ Formatting:        │        95% │
│                                 │ Prettier           │            │
│ node.conventions.monorepo       │ Monorepo:          │        95% │
│                                 │ Turborepo          │            │
│ generic.conventions.ci_platform │ CI/CD: GitHub      │        80% │
│                                 │ Actions            │            │
└─────────────────────────────────┴────────────────────┴────────────┘
```

### Example Reports

The `examples/` directory contains sample reports generated by running `conventions discover` on the [FastAPI](https://github.com/fastapi/fastapi) repository:

- **[CLAUDE.md](examples/fastapi/CLAUDE.md)** - Agent-optimized context for Claude Code
- **[conventions.html](examples/fastapi/conventions.html)** - Interactive HTML report with filtering and dark mode
- **[conventions-review.md](examples/fastapi/conventions-review.md)** - Review report with scores and suggestions
- **[conventions.md](examples/fastapi/conventions.md)** - Markdown summary
- **[conventions.raw.json](examples/fastapi/conventions.raw.json)** - Machine-readable JSON
- **[conventions.sarif](examples/fastapi/conventions.sarif)** - SARIF format for CI integration

## Output Files

After running `conventions discover`, files are created in the `.conventions/` directory.

**Default formats:** json, markdown, review
**Optional formats:** html, sarif (use `--format json,markdown,review,html,sarif`)

| File | Description |
|------|-------------|
| `conventions.raw.json` | Machine-readable JSON with all detected conventions |
| `conventions.md` | Human-readable Markdown summary |
| `conventions-review.md` | Review report with ratings (1-5) and improvement suggestions, sorted by priority |
| `conventions.html` | Interactive HTML report with dark/light mode, sortable tables, filtering, and expandable code evidence |
| `conventions.sarif` | SARIF format for GitHub Code Scanning and other SARIF-compatible tools |

## Rating Scale

Each convention is rated on a 1-5 scale:

| Score | Rating | Description |
|-------|--------|-------------|
| 5 | Excellent | Best practices followed consistently |
| 4 | Good | Minor improvements possible |
| 3 | Average | Room for improvement |
| 2 | Below Average | Significant improvements needed |
| 1 | Poor | Major issues detected |

## Configuration

### Configuration File

Create a `.conventionsrc.json` file in your repository root:

```json
{
  "languages": ["python", "node"],
  "max_files": 1000,
  "disabled_detectors": ["python_graphql"],
  "disabled_rules": ["python.conventions.graphql"],
  "output_formats": ["json", "markdown", "review", "html"],
  "exclude_patterns": ["**/generated/**", "**/vendor/**"],
  "plugin_paths": ["./custom_rules.py"],
  "min_score": 3.0
}
```

### Configuration Options

| Option | Type | Description |
|--------|------|-------------|
| `languages` | `string[]` | Languages to scan (auto-detect if not specified) |
| `max_files` | `number` | Maximum files to scan per language (default: 2000) |
| `disabled_detectors` | `string[]` | Detector names to skip |
| `disabled_rules` | `string[]` | Rule IDs to exclude from output |
| `output_formats` | `string[]` | Output formats: json, markdown, review, html, sarif |
| `exclude_patterns` | `string[]` | Glob patterns to exclude from scanning |
| `plugin_paths` | `string[]` | Paths to plugin files |
| `min_score` | `number` | Exit with code 2 if average score is below this threshold |

### Automatic Exclusions

The tool respects `.gitignore` files and automatically excludes:
- `node_modules/`, `vendor/`, `site-packages/`
- `venv/`, `.venv/`, `.tox/`, `.nox/`
- `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`
- `.git/`, `.svn/`, `.hg/`
- Build directories (`build/`, `dist/`, `eggs/`)
- Documentation and examples (`docs/`, `examples/`, `tutorials/`, `docs_src/`)

## CI/CD Integration

### Basic Workflow

```yaml
# .github/workflows/conventions.yml
name: Check Conventions
on: [push, pull_request]

jobs:
  conventions:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install conventions-cli
      - run: conventions discover
      - run: cat .conventions/conventions-review.md
```

### Quality Gate

Add `min_score` to your `.conventionsrc.json` to enforce minimum standards. The workflow will fail (exit code 2) if the average score falls below the threshold.

```json
{
  "min_score": 3.5,
  "output_formats": ["json", "markdown", "review"]
}
```

### SARIF Upload to GitHub Code Scanning

```yaml
# .github/workflows/conventions.yml
name: Convention Analysis
on: [push, pull_request]

jobs:
  analyze:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install conventions-cli
      - run: conventions discover --format sarif
      - uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: .conventions/conventions.sarif
```

## Plugins

Create custom detectors and rating rules by adding plugin files:

```python
# custom_rules.py
from conventions.detectors.base import BaseDetector, DetectorContext, DetectorResult
from conventions.ratings import RatingRule

class MyCustomDetector(BaseDetector):
    name = "my_custom_detector"
    description = "Detects my custom convention"
    languages = {"python"}

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        result = DetectorResult()
        # Custom detection logic
        return result

# Required exports
DETECTORS = [MyCustomDetector]

# Optional: custom rating rules
RATING_RULES = {
    "custom.my_rule": RatingRule(
        score_func=lambda r: 5 if r.stats.get("metric", 0) > 0.8 else 3,
        reason_func=lambda r, s: f"Custom metric: {r.stats.get('metric', 0):.0%}",
        suggestion_func=lambda r, s: None if s >= 5 else "Improve the custom metric.",
    ),
}
```

Add the plugin to your config:

```json
{
  "plugin_paths": ["./custom_rules.py"]
}
```

## Contributing

Contributions are welcome! To add support for new conventions:

1. Create a new detector in `src/conventions/detectors/<language>/`
2. Register it with `@DetectorRegistry.register`
3. Add rating rules in `src/conventions/ratings.py`
4. Add tests in `tests/`

For quick prototyping, use the plugin system instead of modifying the core codebase.

## Ownership and Governance

conventions is an open-source project owned and maintained by Dovatech LLC.

Dovatech LLC is a privately held company founded and wholly owned by Stephanie Dover, who is also the original author and lead maintainer of this project.
