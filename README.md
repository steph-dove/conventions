# Conventions CLI

A command-line tool that automatically discovers and documents coding conventions in your codebase. It analyzes your source code to detect patterns, rates them on a 1-5 scale, and provides actionable improvement suggestions.

## Features

- **Automatic Convention Detection**: Scans your codebase to identify coding patterns and conventions
- **Multi-Language Support**: Python, Go, Node.js/TypeScript, and Rust
- **Cross-Language Detection**: CI/CD, Git conventions, Docker, Kubernetes, and more
- **Convention Rating**: Rates each convention on a 1-5 scale (Poor to Excellent)
- **Improvement Suggestions**: Provides actionable suggestions for conventions that could be improved
- **Multiple Output Formats**: JSON, Markdown reports, and review reports

## Language Support

| Language | Conventions | Categories |
|----------|-------------|------------|
| **Python** | 30+ | typing, docs, testing, logging, errors, security, async, architecture, API, CLI, caching, GraphQL |
| **Node.js/TypeScript** | 25+ | TypeScript, testing, logging, errors, security, async, architecture, API, frontend, state management, tooling |
| **Go** | 20+ | modules, testing, logging, errors, security, concurrency, architecture, API, patterns, CLI, gRPC, DI |
| **Rust** | 12 | Cargo, testing, errors, async, web, CLI, serialization, docs, unsafe, macros, logging, database |
| **Generic** | 10+ | CI/CD, Git, Docker, Kubernetes, API docs, editor config |

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/your-org/conventions-cli.git
cd conventions-cli

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install the package
pip install -e .
```

### Requirements

- Python 3.10 or higher

## Usage

### Discover Conventions

Run the `discover` command in your repository to detect conventions:

```bash
# Scan the current directory
conventions discover

# Scan a specific repository
conventions discover -r /path/to/your/repo

# Scan with verbose output
conventions discover -r /path/to/your/repo --verbose

# Scan specific languages only
conventions discover -r /path/to/your/repo --languages python,go
```

### View Existing Conventions

If you've already run discovery, view the results:

```bash
conventions show -r /path/to/your/repo
```

### Command Options

| Option | Short | Description |
|--------|-------|-------------|
| `--repo` | `-r` | Path to repository root (default: current directory) |
| `--languages` | `-l` | Comma-separated list of languages to scan |
| `--max-files` | `-m` | Maximum files to scan (default: 2000) |
| `--verbose` | `-v` | Enable verbose output |
| `--quiet` | `-q` | Suppress output except errors |
| `--detailed` | `-d` | Show detailed rule information |

## Output Files

After running `conventions discover`, three files are created in the `.conventions/` directory:

### 1. `conventions.raw.json`

Machine-readable JSON containing all detected conventions with full details.

### 2. `conventions.md`

Human-readable Markdown report summarizing detected conventions.

### 3. `conventions-review.md`

Review report with ratings (1-5) and improvement suggestions, sorted by priority.

## Detected Conventions

### Generic (Cross-Language)

| Category | Convention ID | Description |
|----------|--------------|-------------|
| **CI/CD** | `generic.conventions.ci_platform` | CI/CD platform (GitHub Actions, GitLab CI, CircleCI, etc.) |
| **CI/CD** | `generic.conventions.ci_quality` | CI/CD best practices (testing, linting, caching) |
| **Git** | `generic.conventions.commit_messages` | Commit message conventions (Conventional Commits, etc.) |
| **Git** | `generic.conventions.branch_naming` | Branch naming conventions (GitFlow, trunk-based) |
| **Git** | `generic.conventions.git_hooks` | Git hooks (pre-commit, Husky, Lefthook) |
| **Dependencies** | `generic.conventions.dependency_updates` | Dependency update automation (Dependabot, Renovate) |
| **API Docs** | `generic.conventions.api_documentation` | API documentation (OpenAPI, AsyncAPI, GraphQL) |
| **Containers** | `generic.conventions.dockerfile_practices` | Dockerfile best practices |
| **Containers** | `generic.conventions.docker_compose` | Docker Compose configuration |
| **Containers** | `generic.conventions.kubernetes` | Kubernetes manifests (Helm, Kustomize) |
| **Editor** | `generic.conventions.editor_config` | Editor configuration (.editorconfig, VS Code, JetBrains) |

### Python

| Category | Convention ID | Description |
|----------|--------------|-------------|
| **Typing** | `python.conventions.typing_coverage` | Type annotation coverage |
| **Documentation** | `python.conventions.docstrings` | Docstring coverage |
| **Documentation** | `python.conventions.docstring_style` | Docstring style (Google, NumPy, Sphinx) |
| **Style** | `python.conventions.naming` | PEP 8 naming conventions |
| **Testing** | `python.conventions.testing_framework` | Test framework (pytest, unittest) |
| **Testing** | `python.conventions.testing_fixtures` | Fixture patterns |
| **Testing** | `python.conventions.testing_mocking` | Mocking library usage |
| **Logging** | `python.conventions.logging_library` | Logging library (structlog, loguru, stdlib) |
| **Logging** | `python.conventions.logging_fields` | Structured logging fields |
| **Error Handling** | `python.conventions.error_handling_boundary` | HTTP exception placement |
| **Error Handling** | `python.conventions.error_taxonomy` | Custom exception naming |
| **Error Handling** | `python.conventions.exception_handlers` | Exception handler organization |
| **Security** | `python.conventions.raw_sql_usage` | Raw SQL detection |
| **Security** | `python.conventions.auth_pattern` | Authentication patterns |
| **Security** | `python.conventions.secrets_access_style` | Configuration/secrets access |
| **Async** | `python.conventions.async_style` | Async/sync API style |
| **Architecture** | `python.conventions.layering_direction` | Import layer dependencies |
| **Architecture** | `python.conventions.forbidden_imports` | Layer boundary violations |
| **API** | `python.conventions.api_framework` | Web framework (FastAPI, Flask, Django) |
| **API** | `python.conventions.schema_library` | Schema/validation library (Pydantic, etc.) |
| **Tooling** | `python.conventions.formatter` | Code formatter (Black, Ruff, YAPF) |
| **Tooling** | `python.conventions.linter` | Linter (Ruff, Flake8, Pylint, mypy) |
| **Tooling** | `python.conventions.import_sorting` | Import sorting (isort, Ruff) |
| **Dependencies** | `python.conventions.dependency_management` | Dependency management (Poetry, uv, PDM) |
| **CLI** | `python.conventions.cli_framework` | CLI framework (Typer, Click, argparse) |
| **Background** | `python.conventions.background_tasks` | Background tasks (Celery, RQ, Dramatiq) |
| **Caching** | `python.conventions.caching` | Caching (Redis, lru_cache, cachetools) |
| **GraphQL** | `python.conventions.graphql` | GraphQL library (Strawberry, Graphene) |

### Go

| Category | Convention ID | Description |
|----------|--------------|-------------|
| **Modules** | `go.conventions.modules` | Go modules and dependencies |
| **Documentation** | `go.conventions.doc_comments` | Doc comment coverage |
| **Documentation** | `go.conventions.example_tests` | Example test functions |
| **Testing** | `go.conventions.testing_framework` | Testing framework (testify, gomega) |
| **Testing** | `go.conventions.table_driven_tests` | Table-driven test patterns |
| **Testing** | `go.conventions.subtests` | Subtest usage (t.Run) |
| **Logging** | `go.conventions.logging_library` | Logging library (zap, zerolog, slog) |
| **Error Handling** | `go.conventions.error_types` | Custom error types |
| **Error Handling** | `go.conventions.sentinel_errors` | Sentinel error patterns |
| **Error Handling** | `go.conventions.error_wrapping` | Error wrapping (errors.Is/As) |
| **Security** | `go.conventions.sql_injection` | SQL injection prevention |
| **Security** | `go.conventions.secrets_config` | Configuration (Viper, envconfig) |
| **Concurrency** | `go.conventions.goroutine_patterns` | Goroutine usage patterns |
| **Concurrency** | `go.conventions.context_usage` | Context propagation |
| **Concurrency** | `go.conventions.sync_primitives` | Sync primitives usage |
| **Architecture** | `go.conventions.package_structure` | Package layout (cmd, internal, pkg) |
| **Architecture** | `go.conventions.interface_segregation` | Interface sizes |
| **API** | `go.conventions.http_framework` | HTTP framework (Gin, Echo, Chi, Fiber) |
| **API** | `go.conventions.http_middleware` | Middleware patterns |
| **API** | `go.conventions.grpc` | gRPC and Protocol Buffers |
| **Patterns** | `go.conventions.options_pattern` | Functional options pattern |
| **Patterns** | `go.conventions.repository_pattern` | Repository pattern |
| **CLI** | `go.conventions.cli_framework` | CLI framework (Cobra, urfave/cli) |
| **DI** | `go.conventions.di_framework` | DI framework (Wire, Fx, dig) |
| **Database** | `go.conventions.migrations` | Migration tools (golang-migrate, goose) |
| **Codegen** | `go.conventions.codegen` | go:generate directives |

### Node.js/TypeScript

| Category | Convention ID | Description |
|----------|--------------|-------------|
| **Language** | `node.conventions.typescript` | TypeScript strictness |
| **Language** | `node.conventions.type_coverage` | Type coverage (any usage) |
| **Language** | `node.conventions.module_system` | ES Modules vs CommonJS |
| **Documentation** | `node.conventions.jsdoc` | JSDoc coverage |
| **Testing** | `node.conventions.testing_framework` | Testing framework (Jest, Vitest, Mocha) |
| **Testing** | `node.conventions.mocking` | Mocking patterns |
| **Testing** | `node.conventions.coverage_config` | Coverage configuration |
| **Logging** | `node.conventions.logging_library` | Logging library (Pino, Winston) |
| **Logging** | `node.conventions.structured_logging` | Structured vs console.log |
| **Error Handling** | `node.conventions.error_classes` | Custom Error classes |
| **Error Handling** | `node.conventions.async_error_handling` | Async error handling |
| **Security** | `node.conventions.env_config` | Environment configuration (dotenv) |
| **Security** | `node.conventions.input_validation` | Input validation (Zod, Joi, Yup) |
| **Security** | `node.conventions.helmet_security` | Security middleware (Helmet) |
| **Async** | `node.conventions.async_style` | async/await vs callbacks |
| **Async** | `node.conventions.promise_patterns` | Promise combinators |
| **Architecture** | `node.conventions.layer_separation` | Layer separation |
| **Architecture** | `node.conventions.barrel_exports` | Barrel exports (index.ts) |
| **API** | `node.conventions.framework` | Web framework (Express, Fastify, NestJS) |
| **API** | `node.conventions.middleware_patterns` | Middleware organization |
| **API** | `node.conventions.route_organization` | Route file structure |
| **Tooling** | `node.conventions.package_manager` | Package manager (npm, Yarn, pnpm, Bun) |
| **Tooling** | `node.conventions.monorepo` | Monorepo tools (Turborepo, Nx, Lerna) |
| **Tooling** | `node.conventions.build_tools` | Build tools (Vite, webpack, esbuild) |
| **Tooling** | `node.conventions.linting` | Linting (ESLint, Biome) |
| **Tooling** | `node.conventions.formatting` | Formatting (Prettier, Biome) |
| **Frontend** | `node.conventions.frontend` | Frontend framework (React, Vue, Svelte) |
| **State** | `node.conventions.state_management` | State management (Redux, Zustand, Pinia) |

### Rust

| Category | Convention ID | Description |
|----------|--------------|-------------|
| **Project** | `rust.conventions.cargo` | Cargo.toml analysis (edition, dependencies) |
| **Testing** | `rust.conventions.testing` | Testing patterns (proptest, criterion) |
| **Error Handling** | `rust.conventions.error_handling` | Error handling (anyhow, thiserror) |
| **Async** | `rust.conventions.async_runtime` | Async runtime (Tokio, async-std) |
| **Web** | `rust.conventions.web_framework` | Web framework (Axum, Actix, Rocket) |
| **CLI** | `rust.conventions.cli_framework` | CLI framework (clap, structopt) |
| **Data** | `rust.conventions.serialization` | Serialization (Serde, formats) |
| **Documentation** | `rust.conventions.documentation` | Doc comments and examples |
| **Safety** | `rust.conventions.unsafe_code` | Unsafe code analysis |
| **Patterns** | `rust.conventions.macros` | Macro usage (macro_rules!, proc-macro) |
| **Observability** | `rust.conventions.logging` | Logging (tracing, log) |
| **Database** | `rust.conventions.database` | Database libraries (SQLx, Diesel, SeaORM) |

## Rating Scale

Each convention is rated on a 1-5 scale:

| Score | Rating | Description |
|-------|--------|-------------|
| 5 | Excellent | Best practices followed consistently |
| 4 | Good | Minor improvements possible |
| 3 | Average | Room for improvement |
| 2 | Below Average | Significant improvements needed |
| 1 | Poor | Major issues detected |

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

## Example Workflow

1. **Initial Discovery**: Run `conventions discover` on your repo
2. **Review Results**: Check `.conventions/conventions-review.md` for ratings
3. **Address Suggestions**: Fix issues listed in "Improvement Priorities"
4. **Re-run**: Run discovery again to verify improvements
5. **Commit**: Add `.conventions/` to version control to track conventions over time

## Integrating with CI/CD

You can integrate conventions checking into your CI pipeline:

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
      - run: conventions discover -r .
      - run: cat .conventions/conventions-review.md
```

## Configuration

The tool respects `.gitignore` files and automatically excludes:
- `node_modules/`
- `venv/`, `.venv/`
- `__pycache__/`
- `.git/`
- Build directories

## Contributing

Contributions are welcome! To add support for new conventions:

1. Create a new detector in `src/conventions/detectors/<language>/`
2. Register it with `@DetectorRegistry.register`
3. Add rating rules in `src/conventions/ratings.py`
4. Add tests in `tests/`

### Directory Structure

```
src/conventions/detectors/
├── base.py              # Base detector classes
├── registry.py          # Detector registration
├── orchestrator.py      # Detection orchestration
├── generic/             # Cross-language detectors
│   ├── ci_cd.py
│   ├── git_conventions.py
│   ├── containerization.py
│   └── ...
├── python/              # Python detectors
│   ├── index.py
│   ├── typing.py
│   ├── testing.py
│   └── ...
├── go/                  # Go detectors
│   ├── index.py
│   ├── testing.py
│   └── ...
├── node/                # Node.js/TypeScript detectors
│   ├── index.py
│   ├── typescript.py
│   └── ...
└── rust/                # Rust detectors
    ├── index.py
    ├── cargo.py
    └── ...
```

## License

MIT License - see LICENSE file for details.
