# Convention ID Reference

This is the full reference of all convention IDs detected by the Conventions CLI, organized by language and category.

For an overview of language support, see the [README](../README.md#language-support).

## Generic (Cross-Language)

| Category | Convention ID | Description |
|----------|--------------|-------------|
| **CI/CD** | `generic.conventions.ci_platform` | CI/CD platform (GitHub Actions, GitLab CI, CircleCI, etc.) |
| **CI/CD** | `generic.conventions.ci_quality` | CI/CD best practices (testing, linting, caching) |
| **Git** | `generic.conventions.commit_messages` | Commit message conventions (Conventional Commits, etc.) |
| **Git** | `generic.conventions.branch_naming` | Branch naming conventions (GitFlow, trunk-based) |
| **Git** | `generic.conventions.git_hooks` | Git hooks (pre-commit, Husky, Lefthook) |
| **Dependencies** | `generic.conventions.dependency_updates` | Dependency update automation (Dependabot, Renovate) |
| **API Docs** | `generic.conventions.api_documentation` | API documentation (OpenAPI, AsyncAPI, GraphQL) |
| **Containers** | `generic.conventions.dockerfile` | Dockerfile best practices |
| **Containers** | `generic.conventions.docker_compose` | Docker Compose configuration |
| **Containers** | `generic.conventions.kubernetes` | Kubernetes manifests (Helm, Kustomize) |
| **Editor** | `generic.conventions.editor_config` | Editor configuration (.editorconfig, VS Code, JetBrains) |
| **Repository** | `generic.conventions.repo_layout` | Repository structure and organization |
| **Repository** | `generic.conventions.standard_files` | Standard files (README, LICENSE, CONTRIBUTING) |

## Python

| Category | Convention ID | Description |
|----------|--------------|-------------|
| **Typing** | `python.conventions.typing_coverage` | Type annotation coverage |
| **Typing** | `python.conventions.optional_usage` | Optional type hint patterns |
| **Typing** | `python.conventions.none_returns` | None return type annotations |
| **Typing** | `python.conventions.result_types` | Result type patterns (returns) |
| **Documentation** | `python.conventions.docstrings` | Docstring coverage |
| **Documentation** | `python.conventions.docstring_style` | Docstring style (Google, NumPy, Sphinx) |
| **Documentation** | `python.docs_conventions.organization` | Documentation organization |
| **Documentation** | `python.docs_conventions.example_structure` | Example code structure |
| **Documentation** | `python.docs_conventions.example_completeness` | Example completeness |
| **Style** | `python.conventions.naming` | PEP 8 naming conventions |
| **Style** | `python.conventions.import_style` | Import organization style |
| **Style** | `python.conventions.string_formatting` | String formatting (f-strings, format, %) |
| **Style** | `python.conventions.string_constants` | String constant patterns |
| **Style** | `python.conventions.constant_naming` | Constant naming conventions |
| **Style** | `python.conventions.path_handling` | Path handling (pathlib vs os.path) |
| **Testing** | `python.conventions.testing_framework` | Test framework (pytest, unittest) |
| **Testing** | `python.conventions.test_naming` | Test naming conventions |
| **Testing** | `python.conventions.test_structure` | Test file organization |
| **Testing** | `python.test_conventions.fixtures` | Fixture patterns |
| **Testing** | `python.test_conventions.mocking` | Mocking library usage |
| **Testing** | `python.test_conventions.assertions` | Assertion patterns |
| **Testing** | `python.test_conventions.parametrized` | Parametrized test usage |
| **Testing** | `python.conventions.test_coverage_threshold` | Test coverage threshold configuration |
| **Logging** | `python.conventions.logging_library` | Logging library (structlog, loguru, stdlib) |
| **Logging** | `python.conventions.logging_fields` | Structured logging fields |
| **Error Handling** | `python.conventions.error_handling_boundary` | HTTP exception placement |
| **Error Handling** | `python.conventions.error_taxonomy` | Custom exception naming |
| **Error Handling** | `python.conventions.exception_handlers` | Exception handler organization |
| **Error Handling** | `python.conventions.error_wrapper` | Error wrapping patterns |
| **Error Handling** | `python.conventions.error_transformation` | Error transformation patterns |
| **Error Handling** | `python.conventions.exception_chaining` | Exception chaining (raise X from Y) |
| **Security** | `python.conventions.raw_sql_usage` | Raw SQL detection |
| **Security** | `python.conventions.auth_pattern` | Authentication patterns |
| **Security** | `python.conventions.secrets_access_style` | Configuration/secrets access |
| **Security** | `python.conventions.env_separation` | Environment separation (dynaconf, Pydantic Settings) |
| **Security** | `python.conventions.secret_management` | Secret management (Vault, AWS/GCP Secrets) |
| **Async** | `python.conventions.async_style` | Async/sync API style |
| **Architecture** | `python.conventions.layering_direction` | Import layer dependencies |
| **Architecture** | `python.conventions.forbidden_imports` | Layer boundary violations |
| **Architecture** | `python.conventions.container_local_dev` | Containerized local development (devcontainer, docker-compose) |
| **API** | `python.conventions.api_framework` | Web framework (FastAPI, Flask, Django) |
| **API** | `python.conventions.schema_library` | Schema/validation library (Pydantic, etc.) |
| **API** | `python.conventions.data_class_style` | Data class style (dataclass, Pydantic, attrs, msgspec) |
| **API** | `python.conventions.response_shape` | API response structure |
| **API** | `python.conventions.response_envelope` | Response envelope patterns |
| **API** | `python.conventions.error_response_pattern` | Error response format |
| **API** | `python.conventions.pagination_pattern` | Pagination patterns |
| **Validation** | `python.conventions.validation_style` | Input validation patterns |
| **DI** | `python.conventions.di_style` | Dependency injection patterns |
| **Database** | `python.conventions.db_library` | Database library (SQLAlchemy, etc.) |
| **Database** | `python.conventions.db_query_style` | Query style (ORM vs raw) |
| **Database** | `python.conventions.db_session_lifecycle` | Session management |
| **Database** | `python.conventions.db_transactions` | Transaction patterns |
| **Database** | `python.conventions.async_orm` | Async ORM (SQLAlchemy AsyncIO, Tortoise) |
| **Observability** | `python.conventions.metrics` | Metrics collection |
| **Observability** | `python.conventions.tracing` | Distributed tracing |
| **Observability** | `python.conventions.correlation_ids` | Correlation ID patterns |
| **Resilience** | `python.conventions.retries` | Retry patterns |
| **Resilience** | `python.conventions.timeouts` | Timeout configuration |
| **Resilience** | `python.conventions.circuit_breakers` | Circuit breaker patterns (pybreaker) |
| **Resilience** | `python.conventions.health_checks` | Health check endpoints |
| **Tooling** | `python.conventions.formatter` | Code formatter (Black, Ruff, YAPF) |
| **Tooling** | `python.conventions.linter` | Linter (Ruff, Flake8, Pylint, mypy) |
| **Tooling** | `python.conventions.import_sorting` | Import sorting with grouping (isort, Ruff) |
| **Tooling** | `python.conventions.line_length` | Line length configuration (88/100/120) |
| **Tooling** | `python.conventions.string_quotes` | String quote style (double/single) |
| **Tooling** | `python.conventions.pre_commit_hooks` | Pre-commit hooks (ruff, mypy, black) |
| **Dependencies** | `python.conventions.dependency_management` | Dependency management (Poetry, uv, PDM) |
| **CLI** | `python.conventions.cli_framework` | CLI framework (Typer, Click, argparse) |
| **Background** | `python.conventions.background_tasks` | Background tasks (Celery, RQ, Dramatiq) |
| **Background** | `python.conventions.background_jobs` | Background job patterns |
| **Caching** | `python.conventions.caching` | Caching (Redis, lru_cache, cachetools) |
| **GraphQL** | `python.conventions.graphql` | GraphQL library (Strawberry, Graphene) |
| **Patterns** | `python.conventions.class_style` | Class definition style (dataclass, Pydantic, attrs) |
| **Patterns** | `python.conventions.enum_usage` | Enum usage patterns |
| **Patterns** | `python.conventions.custom_decorators` | Custom decorator patterns |
| **Patterns** | `python.conventions.context_managers` | Context manager usage |

## Go

| Category | Convention ID | Description |
|----------|--------------|-------------|
| **Modules** | `go.conventions.modules` | Go modules and dependencies |
| **Documentation** | `go.conventions.doc_comments` | Doc comment coverage |
| **Documentation** | `go.conventions.example_tests` | Example test functions |
| **Testing** | `go.conventions.testing` | Testing patterns |
| **Testing** | `go.conventions.testing_framework` | Testing framework (testify, gomega) |
| **Testing** | `go.conventions.table_driven_tests` | Table-driven test patterns |
| **Testing** | `go.conventions.subtests` | Subtest usage (t.Run) |
| **Testing** | `go.conventions.test_helpers` | Test helper patterns |
| **Logging** | `go.conventions.logging_library` | Logging library (zap, zerolog, slog) |
| **Logging** | `go.conventions.structured_logging` | Structured logging patterns |
| **Error Handling** | `go.conventions.error_handling` | Error handling patterns |
| **Error Handling** | `go.conventions.error_types` | Custom error types |
| **Error Handling** | `go.conventions.sentinel_errors` | Sentinel error patterns |
| **Error Handling** | `go.conventions.error_wrapping` | Error wrapping (errors.Is/As) |
| **Security** | `go.conventions.sql_injection` | SQL injection prevention |
| **Security** | `go.conventions.secrets_config` | Configuration (Viper, envconfig) |
| **Security** | `go.conventions.input_validation` | Input validation patterns |
| **Concurrency** | `go.conventions.goroutine_patterns` | Goroutine usage patterns |
| **Concurrency** | `go.conventions.context_usage` | Context propagation |
| **Concurrency** | `go.conventions.sync_primitives` | Sync primitives usage |
| **Concurrency** | `go.conventions.channel_usage` | Channel patterns |
| **Architecture** | `go.conventions.package_structure` | Package layout (cmd, internal, pkg) |
| **Architecture** | `go.conventions.interface_segregation` | Interface sizes |
| **Architecture** | `go.conventions.interfaces` | Interface patterns |
| **Architecture** | `go.conventions.dependency_direction` | Dependency direction |
| **API** | `go.conventions.framework` | Web framework detection |
| **API** | `go.conventions.http_framework` | HTTP framework (Gin, Echo, Chi, Fiber) |
| **API** | `go.conventions.http_middleware` | Middleware patterns |
| **API** | `go.conventions.response_patterns` | Response patterns |
| **API** | `go.conventions.grpc` | gRPC and Protocol Buffers |
| **Patterns** | `go.conventions.options_pattern` | Functional options pattern |
| **Patterns** | `go.conventions.builder_pattern` | Builder pattern |
| **Patterns** | `go.conventions.repository_pattern` | Repository pattern |
| **CLI** | `go.conventions.cli_framework` | CLI framework (Cobra, urfave/cli) |
| **DI** | `go.conventions.di_framework` | DI framework (Wire, Fx, dig) |
| **Database** | `go.conventions.migrations` | Migration tools (golang-migrate, goose) |
| **Codegen** | `go.conventions.codegen` | go:generate directives |

## Node.js/TypeScript

| Category | Convention ID | Description |
|----------|--------------|-------------|
| **Language** | `node.conventions.typescript` | TypeScript strictness |
| **Language** | `node.conventions.strict_mode` | Strict mode configuration |
| **Language** | `node.conventions.type_coverage` | Type coverage (any usage) |
| **Language** | `node.conventions.module_system` | ES Modules vs CommonJS |
| **Documentation** | `node.conventions.jsdoc` | JSDoc coverage |
| **Testing** | `node.conventions.testing_framework` | Testing framework (Jest, Vitest, Mocha) |
| **Testing** | `node.conventions.mocking` | Mocking patterns |
| **Testing** | `node.conventions.coverage_config` | Coverage configuration |
| **Testing** | `node.conventions.test_patterns` | Test organization patterns |
| **Logging** | `node.conventions.logging_library` | Logging library (Pino, Winston) |
| **Logging** | `node.conventions.structured_logging` | Structured vs console.log |
| **Error Handling** | `node.conventions.error_classes` | Custom Error classes |
| **Error Handling** | `node.conventions.error_middleware` | Error middleware patterns |
| **Error Handling** | `node.conventions.async_error_handling` | Async error handling |
| **Security** | `node.conventions.env_config` | Environment configuration (dotenv) |
| **Security** | `node.conventions.input_validation` | Input validation (Zod, Joi, Yup) |
| **Security** | `node.conventions.helmet_security` | Security middleware (Helmet) |
| **Security** | `node.conventions.sql_injection` | SQL injection prevention |
| **Async** | `node.conventions.async_style` | async/await vs callbacks |
| **Async** | `node.conventions.promise_patterns` | Promise combinators |
| **Architecture** | `node.conventions.layer_separation` | Layer separation |
| **Architecture** | `node.conventions.barrel_exports` | Barrel exports (index.ts) |
| **Architecture** | `node.conventions.project_structure` | Project structure patterns |
| **API** | `node.conventions.framework` | Web framework (Express, Fastify, NestJS) |
| **API** | `node.conventions.middleware_patterns` | Middleware organization |
| **API** | `node.conventions.route_organization` | Route file structure |
| **API** | `node.conventions.response_patterns` | Response patterns |
| **Patterns** | `node.conventions.dependency_injection` | Dependency injection patterns |
| **Patterns** | `node.conventions.repository_pattern` | Repository pattern |
| **Patterns** | `node.conventions.singleton_pattern` | Singleton pattern |
| **Tooling** | `node.conventions.package_manager` | Package manager (npm, Yarn, pnpm, Bun) |
| **Tooling** | `node.conventions.monorepo` | Monorepo tools (Turborepo, Nx, Lerna) |
| **Tooling** | `node.conventions.build_tools` | Build tools (Vite, webpack, esbuild) |
| **Tooling** | `node.conventions.linting` | Linting (ESLint, Biome) |
| **Tooling** | `node.conventions.formatting` | Formatting (Prettier, Biome) |
| **Frontend** | `node.conventions.frontend` | Frontend framework (React, Vue, Svelte) |
| **State** | `node.conventions.state_management` | State management (Redux, Zustand, Pinia) |

## Rust

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
