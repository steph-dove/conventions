"""Documentation URL registry for detected conventions and tools.

This module provides a centralized mapping of tools, frameworks, and libraries
to their official documentation URLs.
"""

from __future__ import annotations

from typing import Optional

# Documentation URLs organized by category
DOCS_URLS: dict[str, str] = {
    # ==========================================================================
    # Node.js / JavaScript / TypeScript
    # ==========================================================================

    # Frameworks
    "express": "https://expressjs.com/",
    "fastify": "https://fastify.dev/docs/latest/",
    "koa": "https://koajs.com/",
    "nestjs": "https://docs.nestjs.com/",
    "hapi": "https://hapi.dev/",
    "next": "https://nextjs.org/docs",
    "nextjs": "https://nextjs.org/docs",
    "nuxt": "https://nuxt.com/docs",
    "remix": "https://remix.run/docs/en/main",
    "gatsby": "https://www.gatsbyjs.com/docs/",

    # Frontend frameworks
    "react": "https://react.dev/",
    "vue": "https://vuejs.org/guide/",
    "angular": "https://angular.io/docs",
    "svelte": "https://svelte.dev/docs",
    "solid": "https://docs.solidjs.com/",
    "preact": "https://preactjs.com/guide/v10/getting-started",
    "qwik": "https://qwik.dev/docs/",

    # UI Libraries
    "mui": "https://mui.com/material-ui/getting-started/",
    "material-ui": "https://mui.com/material-ui/getting-started/",
    "chakra": "https://chakra-ui.com/docs/getting-started",
    "antd": "https://ant.design/docs/react/introduce",
    "radix": "https://www.radix-ui.com/primitives/docs/overview/introduction",
    "headless": "https://headlessui.com/",
    "shadcn": "https://ui.shadcn.com/docs",
    "mantine": "https://mantine.dev/getting-started/",
    "blueprint": "https://blueprintjs.com/docs/",
    "vuetify": "https://vuetifyjs.com/en/getting-started/installation/",
    "primereact": "https://primereact.org/",
    "primevue": "https://primevue.org/",
    "react_bootstrap": "https://react-bootstrap.github.io/docs/getting-started/introduction",
    "semantic": "https://react.semantic-ui.com/",

    # State management
    "redux": "https://redux.js.org/",
    "redux_toolkit": "https://redux-toolkit.js.org/",
    "zustand": "https://docs.pmnd.rs/zustand/getting-started/introduction",
    "jotai": "https://jotai.org/docs/introduction",
    "recoil": "https://recoiljs.org/docs/introduction/getting-started",
    "mobx": "https://mobx.js.org/README.html",
    "xstate": "https://xstate.js.org/docs/",
    "pinia": "https://pinia.vuejs.org/",
    "vuex": "https://vuex.vuejs.org/",
    "ngrx": "https://ngrx.io/docs",
    "effector": "https://effector.dev/docs/introduction/",
    "valtio": "https://valtio.pmnd.rs/",
    "tanstack_query": "https://tanstack.com/query/latest/docs/framework/react/overview",
    "react_query": "https://tanstack.com/query/latest/docs/framework/react/overview",
    "swr": "https://swr.vercel.app/",

    # Testing
    "jest": "https://jestjs.io/docs/getting-started",
    "vitest": "https://vitest.dev/guide/",
    "mocha": "https://mochajs.org/",
    "ava": "https://github.com/avajs/ava/blob/main/docs/01-writing-tests.md",
    "tap": "https://node-tap.org/docs/",
    "jasmine": "https://jasmine.github.io/pages/docs_home.html",
    "sinon": "https://sinonjs.org/releases/latest/",
    "nock": "https://github.com/nock/nock#readme",
    "msw": "https://mswjs.io/docs/",
    "cypress": "https://docs.cypress.io/",
    "playwright": "https://playwright.dev/docs/intro",

    # Linting & Formatting
    "eslint": "https://eslint.org/docs/latest/",
    "prettier": "https://prettier.io/docs/en/",
    "biome": "https://biomejs.dev/guides/getting-started/",
    "standardjs": "https://standardjs.com/",

    # Build tools
    "webpack": "https://webpack.js.org/concepts/",
    "vite": "https://vitejs.dev/guide/",
    "esbuild": "https://esbuild.github.io/",
    "rollup": "https://rollupjs.org/introduction/",
    "parcel": "https://parceljs.org/docs/",
    "turbopack": "https://turbo.build/pack/docs",
    "swc": "https://swc.rs/docs/getting-started",
    "tsup": "https://tsup.egoist.dev/",

    # Package managers
    "npm": "https://docs.npmjs.com/",
    "yarn": "https://yarnpkg.com/getting-started",
    "pnpm": "https://pnpm.io/motivation",
    "bun": "https://bun.sh/docs",

    # Monorepo tools
    "turborepo": "https://turbo.build/repo/docs",
    "nx": "https://nx.dev/getting-started/intro",
    "lerna": "https://lerna.js.org/docs/introduction",
    "rush": "https://rushjs.io/pages/intro/welcome/",

    # Logging
    "pino": "https://getpino.io/",
    "winston": "https://github.com/winstonjs/winston#readme",
    "bunyan": "https://github.com/trentm/node-bunyan#readme",

    # Auth providers
    "auth0": "https://auth0.com/docs",
    "firebase": "https://firebase.google.com/docs/auth",
    "passport": "https://www.passportjs.org/docs/",
    "nextauth": "https://next-auth.js.org/getting-started/introduction",
    "clerk": "https://clerk.com/docs",
    "supabase": "https://supabase.com/docs/guides/auth",
    "cognito": "https://docs.aws.amazon.com/cognito/",
    "keycloak": "https://www.keycloak.org/documentation",
    "okta": "https://developer.okta.com/docs/",

    # Databases & ORMs
    "prisma": "https://www.prisma.io/docs",
    "typeorm": "https://typeorm.io/",
    "sequelize": "https://sequelize.org/docs/v6/",
    "mongoose": "https://mongoosejs.com/docs/",
    "drizzle": "https://orm.drizzle.team/docs/overview",
    "knex": "https://knexjs.org/guide/",
    "mongodb": "https://www.mongodb.com/docs/drivers/node/current/",

    # Code generation
    "plop": "https://plopjs.com/documentation/",
    "hygen": "https://www.hygen.io/docs/quick-start",
    "yeoman": "https://yeoman.io/learning/",

    # TypeScript
    "typescript": "https://www.typescriptlang.org/docs/",

    # Security
    "helmet": "https://helmetjs.github.io/",

    # ==========================================================================
    # Python
    # ==========================================================================

    # Frameworks
    "django": "https://docs.djangoproject.com/",
    "flask": "https://flask.palletsprojects.com/",
    "fastapi": "https://fastapi.tiangolo.com/",
    "starlette": "https://www.starlette.io/",
    "tornado": "https://www.tornadoweb.org/en/stable/",
    "aiohttp": "https://docs.aiohttp.org/",
    "bottle": "https://bottlepy.org/docs/dev/",
    "pyramid": "https://docs.pylonsproject.org/projects/pyramid/",
    "sanic": "https://sanic.dev/en/guide/",
    "litestar": "https://docs.litestar.dev/",

    # Testing
    "pytest": "https://docs.pytest.org/",
    "unittest": "https://docs.python.org/3/library/unittest.html",
    "nose2": "https://docs.nose2.io/",
    "hypothesis": "https://hypothesis.readthedocs.io/",
    "tox": "https://tox.wiki/",
    "nox": "https://nox.thea.codes/",

    # Linting & Formatting
    "ruff": "https://docs.astral.sh/ruff/",
    "black": "https://black.readthedocs.io/",
    "flake8": "https://flake8.pycqa.org/",
    "pylint": "https://pylint.readthedocs.io/",
    "mypy": "https://mypy.readthedocs.io/",
    "pyright": "https://microsoft.github.io/pyright/",
    "isort": "https://pycqa.github.io/isort/",
    "autopep8": "https://pypi.org/project/autopep8/",
    "yapf": "https://github.com/google/yapf",
    "bandit": "https://bandit.readthedocs.io/",

    # Data science & ML
    "pytorch": "https://pytorch.org/docs/stable/",
    "torch": "https://pytorch.org/docs/stable/",
    "tensorflow": "https://www.tensorflow.org/api_docs",
    "numpy": "https://numpy.org/doc/stable/",
    "pandas": "https://pandas.pydata.org/docs/",
    "scikit-learn": "https://scikit-learn.org/stable/documentation.html",
    "sklearn": "https://scikit-learn.org/stable/documentation.html",
    "scipy": "https://docs.scipy.org/doc/scipy/",
    "matplotlib": "https://matplotlib.org/stable/contents.html",
    "seaborn": "https://seaborn.pydata.org/",
    "plotly": "https://plotly.com/python/",
    "keras": "https://keras.io/api/",
    "huggingface": "https://huggingface.co/docs",
    "transformers": "https://huggingface.co/docs/transformers/",
    "jax": "https://jax.readthedocs.io/",
    "polars": "https://docs.pola.rs/",

    # Async
    "asyncio": "https://docs.python.org/3/library/asyncio.html",
    "trio": "https://trio.readthedocs.io/",
    "anyio": "https://anyio.readthedocs.io/",

    # Databases & ORMs
    "sqlalchemy": "https://docs.sqlalchemy.org/",
    "alembic": "https://alembic.sqlalchemy.org/",
    "peewee": "https://docs.peewee-orm.com/",
    "tortoise": "https://tortoise.github.io/",
    "databases": "https://www.encode.io/databases/",
    "psycopg2": "https://www.psycopg.org/docs/",
    "asyncpg": "https://magicstack.github.io/asyncpg/current/",

    # CLI
    "typer": "https://typer.tiangolo.com/",
    "click": "https://click.palletsprojects.com/",
    "argparse": "https://docs.python.org/3/library/argparse.html",
    "rich": "https://rich.readthedocs.io/",

    # Config
    "pydantic": "https://docs.pydantic.dev/",
    "pydantic_settings": "https://docs.pydantic.dev/latest/concepts/pydantic_settings/",
    "python_dotenv": "https://pypi.org/project/python-dotenv/",
    "dynaconf": "https://www.dynaconf.com/",

    # Package/dependency management
    "uv": "https://docs.astral.sh/uv/",
    "pdm": "https://pdm-project.org/",
    "pipenv": "https://pipenv.pypa.io/",
    "hatch": "https://hatch.pypa.io/",
    "pip_tools": "https://pip-tools.readthedocs.io/",
    "pip": "https://pip.pypa.io/",
    "poetry": "https://python-poetry.org/docs/",

    # GraphQL
    "strawberry": "https://strawberry.rocks/docs",
    "ariadne": "https://ariadnegraphql.org/docs/intro",
    "graphene": "https://graphene-python.org/",

    # Auth / JWT
    "pyjwt": "https://pyjwt.readthedocs.io/",
    "python_jose": "https://python-jose.readthedocs.io/",
    "authlib": "https://docs.authlib.org/",

    # Standard library docs
    "pathlib": "https://docs.python.org/3/library/pathlib.html",
    "logging": "https://docs.python.org/3/library/logging.html",
    "dataclasses": "https://docs.python.org/3/library/dataclasses.html",
    "enum": "https://docs.python.org/3/library/enum.html",
    "typing": "https://docs.python.org/3/library/typing.html",
    "json": "https://docs.python.org/3/library/json.html",
    "unittest_mock": "https://docs.python.org/3/library/unittest.mock.html",

    # Logging
    "loguru": "https://loguru.readthedocs.io/",
    "structlog": "https://www.structlog.org/",

    # HTTP clients
    "requests": "https://docs.python-requests.org/",
    "httpx": "https://www.python-httpx.org/",
    "aiohttp_client": "https://docs.aiohttp.org/en/stable/client.html",

    # Task queues
    "celery": "https://docs.celeryq.dev/",
    "rq": "https://python-rq.org/docs/",
    "dramatiq": "https://dramatiq.io/",
    "arq": "https://arq-docs.helpmanual.io/",

    # ==========================================================================
    # Go
    # ==========================================================================

    # Frameworks & routers
    "gin": "https://gin-gonic.com/docs/",
    "echo": "https://echo.labstack.com/docs",
    "fiber": "https://docs.gofiber.io/",
    "chi": "https://go-chi.io/#/README",
    "gorilla_mux": "https://github.com/gorilla/mux#readme",
    "httprouter": "https://pkg.go.dev/github.com/julienschmidt/httprouter",

    # Testing
    "go_testing": "https://pkg.go.dev/testing",
    "testify": "https://pkg.go.dev/github.com/stretchr/testify",
    "gomega": "https://onsi.github.io/gomega/",
    "ginkgo": "https://onsi.github.io/ginkgo/",
    "goconvey": "https://github.com/smartystreets/goconvey#readme",

    # Databases & ORMs
    "gorm": "https://gorm.io/docs/",
    "sqlx": "https://pkg.go.dev/github.com/jmoiron/sqlx",
    "ent": "https://entgo.io/docs/getting-started/",
    "bun_go": "https://bun.uptrace.dev/",

    # Logging
    "zap": "https://pkg.go.dev/go.uber.org/zap",
    "zerolog": "https://github.com/rs/zerolog#readme",
    "logrus": "https://pkg.go.dev/github.com/sirupsen/logrus",

    # Config
    "viper": "https://github.com/spf13/viper#readme",
    "envconfig": "https://pkg.go.dev/github.com/kelseyhightower/envconfig",

    # CLI
    "cobra": "https://cobra.dev/",
    "urfave_cli": "https://cli.urfave.org/",

    # ==========================================================================
    # Rust
    # ==========================================================================

    # Frameworks
    "actix": "https://actix.rs/docs/",
    "axum": "https://docs.rs/axum/latest/axum/",
    "rocket": "https://rocket.rs/guide/",
    "warp": "https://docs.rs/warp/latest/warp/",
    "tide": "https://docs.rs/tide/latest/tide/",

    # Async
    "tokio": "https://tokio.rs/tokio/tutorial",
    "async_std": "https://docs.rs/async-std/latest/async_std/",

    # Serialization
    "serde": "https://serde.rs/",

    # CLI
    "clap": "https://docs.rs/clap/latest/clap/",
    "structopt": "https://docs.rs/structopt/latest/structopt/",

    # Databases
    "diesel": "https://diesel.rs/guides/",
    "sqlx_rust": "https://docs.rs/sqlx/latest/sqlx/",
    "sea_orm": "https://www.sea-ql.org/SeaORM/docs/index/",

    # Logging
    "tracing": "https://docs.rs/tracing/latest/tracing/",
    "log": "https://docs.rs/log/latest/log/",
    "env_logger": "https://docs.rs/env_logger/latest/env_logger/",

    # Error handling
    "anyhow": "https://docs.rs/anyhow/latest/anyhow/",
    "thiserror": "https://docs.rs/thiserror/latest/thiserror/",

    # ==========================================================================
    # Generic / Cross-language
    # ==========================================================================

    # CI/CD
    "github_actions": "https://docs.github.com/en/actions",
    "gitlab_ci": "https://docs.gitlab.com/ee/ci/",
    "circleci": "https://circleci.com/docs/",
    "jenkins": "https://www.jenkins.io/doc/",
    "travis": "https://docs.travis-ci.com/",

    # Containerization
    "docker": "https://docs.docker.com/",
    "docker_compose": "https://docs.docker.com/compose/",
    "kubernetes": "https://kubernetes.io/docs/home/",
    "helm": "https://helm.sh/docs/",

    # Git
    "husky": "https://typicode.github.io/husky/",
    "commitlint": "https://commitlint.js.org/",
    "conventional_commits": "https://www.conventionalcommits.org/",
    "pre_commit": "https://pre-commit.com/",

    # Dependency updates
    "dependabot": "https://docs.github.com/en/code-security/dependabot",
    "renovate": "https://docs.renovatebot.com/",

    # API
    "openapi": "https://swagger.io/specification/",
    "graphql": "https://graphql.org/learn/",
    "grpc": "https://grpc.io/docs/",
    "rest": "https://restfulapi.net/",

    # Caching
    "redis": "https://redis.io/docs/",
    "memcached": "https://memcached.org/",

    # Message queues
    "rabbitmq": "https://www.rabbitmq.com/docs",
    "kafka": "https://kafka.apache.org/documentation/",

    # Observability
    "prometheus": "https://prometheus.io/docs/",
    "opentelemetry": "https://opentelemetry.io/docs/",
    "sentry": "https://docs.sentry.io/",
    "datadog": "https://docs.datadoghq.com/",
}


def get_docs_url(key: str) -> Optional[str]:
    """Get documentation URL for a tool/framework/library.

    Args:
        key: The identifier for the tool (case-insensitive, supports aliases)

    Returns:
        Documentation URL or None if not found
    """
    # Normalize key
    normalized = key.lower().replace("-", "_").replace(" ", "_")

    # Direct lookup
    if normalized in DOCS_URLS:
        return DOCS_URLS[normalized]

    # Try without underscores
    no_underscores = normalized.replace("_", "")
    for k, v in DOCS_URLS.items():
        if k.replace("_", "") == no_underscores:
            return v

    return None


def get_docs_url_for_rule(rule_id: str, stats: dict) -> Optional[str]:
    """Get the most relevant documentation URL for a detected rule.

    This function inspects the rule ID and stats to determine the best
    documentation link to provide.

    Args:
        rule_id: The rule identifier (e.g., "node.conventions.framework")
        stats: The stats dict from the rule

    Returns:
        Most relevant documentation URL or None
    """
    # Check for primary_* keys in stats (various naming patterns used by detectors)
    primary_keys = [
        "primary_framework",
        "primary_library",
        "primary_provider",
        "primary_tool",
        "primary_formatter",
        "primary_linter",
        "primary_sorter",
        "primary_lock",
        "primary",
    ]
    for key in primary_keys:
        if key in stats:
            url = get_docs_url(stats[key])
            if url:
                return url

    # Check for specific tool/library names in stats
    tool_keys = [
        "di_library",
        "mock_library",
        "coverage_tools",
        "linter",
        "formatter",
        "type_checker",
        "graphql_library",
        "http_client",
        "cache_backend",
        "queue_backend",
        "observability_tool",
    ]
    for key in tool_keys:
        if key in stats:
            value = stats[key]
            if isinstance(value, str):
                url = get_docs_url(value)
                if url:
                    return url
            elif isinstance(value, list) and value:
                url = get_docs_url(value[0])
                if url:
                    return url

    # Fall back to rule-specific defaults based on rule_id
    rule_docs_map = {
        # Node/TypeScript
        "node.conventions.typescript": "typescript",
        "node.conventions.strict_mode": "typescript",
        "node.conventions.jsdoc": "typescript",

        # Python tooling
        "python.conventions.typing": "mypy",
        "python.conventions.typing_coverage": "typing",
        "python.conventions.type_checker_strictness": "mypy",
        "python.conventions.import_sorting": "ruff",
        "python.conventions.line_length": "ruff",
        "python.conventions.string_quotes": "ruff",
        "python.conventions.pre_commit_hooks": "pre_commit",

        # Python dependencies
        "python.conventions.dependency_management": "uv",
        "python.conventions.lock_file": "uv",

        # Python testing
        "python.test_conventions.fixtures": "pytest",
        "python.test_conventions.mocking": "unittest_mock",
        "python.test_conventions.parametrized": "pytest",
        "python.test_conventions.assertions": "pytest",

        # Python code patterns
        "python.conventions.naming": "ruff",
        "python.conventions.path_handling": "pathlib",
        "python.conventions.string_formatting": "ruff",
        "python.conventions.context_managers": "typing",
        "python.conventions.data_class_style": "pydantic",
        "python.conventions.class_style": "pydantic",
        "python.conventions.decorator_caching": "typing",
        "python.conventions.json_library": "json",
        "python.conventions.enum_usage": "enum",
        "python.conventions.optional_usage": "typing",
        "python.conventions.constant_naming": "ruff",
        "python.conventions.import_style": "ruff",
        "python.conventions.docstrings": "ruff",

        # Python API patterns
        "python.conventions.api_versioning": "fastapi",
        "python.conventions.auth_pattern": "pyjwt",
        "python.conventions.openapi_docs": "openapi",
        "python.conventions.env_separation": "pydantic_settings",
        "python.conventions.secrets_access_style": "pydantic_settings",
        "python.conventions.validation_style": "pydantic",
        "python.conventions.response_envelope": "pydantic",
        "python.conventions.pagination_pattern": "fastapi",
        "python.conventions.background_jobs": "fastapi",
        "python.conventions.health_checks": "fastapi",

        # Python database
        "python.conventions.db_query_style": "sqlalchemy",
        "python.conventions.db_session_lifecycle": "sqlalchemy",
        "python.conventions.db_connection_pooling": "sqlalchemy",
        "python.conventions.db_transactions": "sqlalchemy",

        # Python errors
        "python.conventions.error_handling_boundary": "fastapi",
        "python.conventions.exception_chaining": "typing",
        "python.conventions.error_taxonomy": "typing",
        "python.conventions.exception_handlers": "fastapi",
        "python.conventions.error_wrapper": "typing",

        # Python logging
        "python.conventions.logging_library": "logging",

        # Python caching
        "python.conventions.caching": "redis",

        # Python docs
        "python.docs_conventions.example_structure": "fastapi",
        "python.docs_conventions.organization": "fastapi",
        "python.docs_conventions.example_completeness": "fastapi",

        # Python testing organization
        "python.conventions.test_naming": "pytest",
        "python.conventions.test_structure": "pytest",

        # Python timeouts/resilience
        "python.conventions.timeouts": "httpx",

        # Generic CI/CD
        "generic.conventions.ci_platform": "github_actions",
        "generic.conventions.ci_quality": "github_actions",
        "generic.conventions.dependency_updates": "dependabot",
        "generic.conventions.git_hooks": "pre_commit",
        "generic.conventions.repo_layout": "github_actions",
        "generic.conventions.standard_files": "github_actions",

        # Go
        "go.conventions.error_handling": "go_testing",
    }

    if rule_id in rule_docs_map:
        return get_docs_url(rule_docs_map[rule_id])

    return None
