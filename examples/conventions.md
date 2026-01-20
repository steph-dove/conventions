# Code Conventions Report

*Generated: 2026-01-19 16:33:32*

## Summary

- **Repository:** `/private/tmp/fastapi_test`
- **Languages:** node, python
- **Files scanned:** 1252
- **Conventions detected:** 38

## Detected Conventions

| ID | Title | Confidence | Evidence |
|:---|:------|:----------:|:--------:|
| `python.conventions.dependency_management` | Dependency management: uv | 95% | 0 |
| `python.conventions.graphql` | GraphQL: Strawberry | 95% | 2 |
| `python.conventions.naming` | PEP 8 snake_case naming | 95% | 0 |
| `python.conventions.testing_framework` | pytest-based testing | 95% | 5 |
| `python.conventions.typing_coverage` | High type annotation coverage | 95% | 4 |
| `generic.conventions.ci_quality` | CI/CD best practices | 90% | 0 |
| `node.conventions.typescript` | JavaScript codebase | 90% | 0 |
| `python.conventions.cli_framework` | CLI framework: Typer | 90% | 5 |
| `python.conventions.import_sorting` | Import sorting: Ruff (isort rules) | 90% | 0 |
| `python.conventions.testing_fixtures` | Centralized pytest fixtures in conftest.py | 90% | 5 |
| `python.conventions.testing_mocking` | Uses unittest.mock for mocking | 90% | 5 |
| `python.conventions.async_style` | Async-first API design | 90% | 2 |
| `python.conventions.background_jobs` | Background jobs with FastAPI BackgroundTasks | 90% | 5 |
| `python.conventions.db_query_style` | SQLAlchemy 2.0 select() style | 90% | 5 |
| `python.conventions.docstring_style` | Sphinx/reST style docstrings | 90% | 2 |
| `python.conventions.linter` | Linters: Ruff, mypy | 90% | 0 |
| `python.conventions.logging_library` | Uses Python standard logging | 90% | 5 |
| `python.conventions.auth_pattern` | JWT-based authentication | 85% | 5 |
| `python.conventions.db_session_lifecycle` | FastAPI-style session dependency injection | 85% | 2 |
| `python.conventions.secrets_access_style` | Structured configuration with Pydantic Settings | 85% | 5 |
| `python.conventions.schema_library` | Primary schema library: Pydantic | 84% | 5 |
| `python.conventions.api_framework` | Primary API framework: FastAPI | 84% | 5 |
| `python.conventions.caching` | Caching: functools.lru_cache | 80% | 5 |
| `python.conventions.logging_fields` | Structured logging with request/trace IDs | 80% | 0 |
| `generic.conventions.ci_platform` | CI/CD: GitHub Actions | 80% | 0 |
| `generic.conventions.dependency_updates` | Dependency updates: Dependabot | 80% | 0 |
| `generic.conventions.git_hooks` | Git hooks: pre-commit | 80% | 0 |
| `python.conventions.db_library` | Primary database library: SQLModel | 79% | 5 |
| `node.conventions.jsdoc` | Partial JSDoc coverage | 75% | 5 |
| `python.conventions.di_style` | Mixed DI patterns: FastAPI Depends dominant | 73% | 5 |
| `generic.conventions.repo_layout` | Standard repository layout | 70% | 0 |
| `python.conventions.error_handling_boundary` | HTTP errors raised in service layer | 70% | 5 |
| `generic.conventions.standard_files` | Standard repository files | 65% | 0 |
| `python.conventions.db_transactions` | Implicit transaction management | 60% | 0 |
| `python.conventions.docstrings` | Low docstring coverage | 60% | 4 |
| `python.conventions.error_taxonomy` | Mixed exception naming conventions | 60% | 5 |
| `python.conventions.exception_handlers` | Distributed exception handling | 60% | 5 |
| `python.conventions.timeouts` | Infrequent timeout specification | 60% | 4 |

## Convention Details

### Dependency management: uv

**ID:** `python.conventions.dependency_management`  
**Category:** dependencies  
**Language:** python  
**Confidence:** 95%

Uses uv with lock file for dependencies.

**Statistics:**

- tools: `['uv']`
- primary_tool: `uv`
- tool_details: `{'uv': {'name': 'uv', 'has_lock': True}}`

---

### GraphQL: Strawberry

**ID:** `python.conventions.graphql`  
**Category:** api  
**Language:** python  
**Confidence:** 95%

Uses Strawberry for GraphQL API. (code-first (type hints))

**Statistics:**

- libraries: `['strawberry']`
- primary_library: `strawberry`
- library_details: `{'strawberry': {'name': 'Strawberry', 'import_count': 2, 'style': 'code-first (type hints)'}}`

**Evidence:**

1. `docs_src/graphql_/tutorial001_py39.py:1-4`

```
import strawberry
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

```

2. `docs_src/graphql_/tutorial001_py39.py:1-6`

```
import strawberry
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter


@strawberry.type
```

---

### PEP 8 snake_case naming

**ID:** `python.conventions.naming`  
**Category:** style  
**Language:** python  
**Confidence:** 95%

Function names follow PEP 8 snake_case convention. 1243/1243 functions use snake_case. Found 45 module-level constants.

**Statistics:**

- snake_case_functions: `1243`
- camel_case_functions: `0`
- snake_case_ratio: `1.0`
- module_constants: `45`

---

### pytest-based testing

**ID:** `python.conventions.testing_framework`  
**Category:** testing  
**Language:** python  
**Confidence:** 95%

Uses pytest as primary testing framework. Found 888 pytest usages.

**Statistics:**

- framework_counts: `{'pytest': 888, 'unittest': 1}`
- primary_framework: `pytest`
- test_file_count: `559`

**Evidence:**

1. `tests/test_datastructures.py:1-7`

```
import io
from pathlib import Path

import pytest
from fastapi import FastAPI, UploadFile
from fastapi.datastructures import Default
from fastapi.testclient import TestClient
```

2. `tests/test_union_body_discriminator_annotated.py:2-8`

```

from typing import Annotated, Union

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from inline_snapshot import snapshot
```

3. `tests/test_computed_fields.py:1-4`

```
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

```

---

### High type annotation coverage

**ID:** `python.conventions.typing_coverage`  
**Category:** typing  
**Language:** python  
**Confidence:** 95%

Type annotations are commonly used in this codebase. 1081/1326 functions (82%) have at least one type annotation.

**Statistics:**

- total_functions: `1326`
- annotated_functions: `1081`
- fully_annotated_functions: `285`
- any_annotation_coverage: `0.815`
- full_annotation_coverage: `0.215`

**Evidence:**

1. `pdm_build.py:4-14`

```
from pdm.backend.hooks import Context

TIANGOLO_BUILD_PACKAGE = os.getenv("TIANGOLO_BUILD_PACKAGE", "fastapi")


def pdm_build_initialize(context: Context) -> None:
    metadata = context.config.metadata
    # Get custom config for the current package, from the env var
    config: dict[str, Any] = context.config.data["tool"]["tiangolo"][
        "_internal-slim-build"
```

2. `fastapi/params.py:25-35`

```


class Param(FieldInfo):  # type: ignore[misc]
    in_: ParamTypes

    def __init__(
        self,
        default: Any = Undefined,
        *,
        default_factory: Union[Callable[[], Any], None] = _Unset,
```

3. `scripts/translation_fixer.py:21-31`

```

cli = typer.Typer()


@cli.callback()
def callback():
    pass


def iter_all_lang_paths(lang_path_root: Path) -> Iterable[Path]:
```

---

### CI/CD best practices

**ID:** `generic.conventions.ci_quality`  
**Category:** ci_cd  
**Language:** generic  
**Confidence:** 90%

CI configuration includes: testing, deployment, caching, matrix builds.

**Statistics:**

- has_test_workflow: `True`
- has_lint_workflow: `False`
- has_deploy_workflow: `True`
- has_caching: `True`
- has_matrix: `True`
- features: `['testing', 'deployment', 'caching', 'matrix builds']`

---

### JavaScript codebase

**ID:** `node.conventions.typescript`  
**Category:** language  
**Language:** node  
**Confidence:** 90%

Codebase is written in JavaScript. 3 files.

**Statistics:**

- typescript_files: `0`
- javascript_files: `3`
- typescript_ratio: `0.0`

---

### CLI framework: Typer

**ID:** `python.conventions.cli_framework`  
**Category:** cli  
**Language:** python  
**Confidence:** 90%

Uses Typer for CLI.

**Statistics:**

- frameworks: `['typer']`
- primary_framework: `typer`
- framework_details: `{'typer': {'name': 'Typer', 'import_count': 14}}`

**Evidence:**

1. `scripts/translate.py:8-14`

```
from typing import Annotated

import git
import typer
import yaml
from github import Github
from pydantic_ai import Agent
```

2. `scripts/translation_fixer.py:3-9`

```
from pathlib import Path
from typing import Annotated

import typer

from scripts.doc_parsing_utils import check_translation

```

3. `scripts/docs.py:11-17`

```
from typing import Any, Optional, Union

import mkdocs.utils
import typer
import yaml
from jinja2 import Template
from ruff.__main__ import find_ruff_bin
```

---

### Import sorting: Ruff (isort rules)

**ID:** `python.conventions.import_sorting`  
**Category:** tooling  
**Language:** python  
**Confidence:** 90%

Uses Ruff (isort rules) for import organization.

**Statistics:**

- sorters: `['ruff']`
- primary_sorter: `ruff`
- sorter_details: `{'ruff': {'name': 'Ruff (isort rules)', 'config_file': 'pyproject.toml'}}`

---

### Centralized pytest fixtures in conftest.py

**ID:** `python.conventions.testing_fixtures`  
**Category:** testing  
**Language:** python  
**Confidence:** 90%

Uses pytest fixtures with 1 conftest.py file(s). Found 186 fixture definitions.

**Statistics:**

- fixture_count: `186`
- conftest_count: `1`
- async_fixture_count: `0`

**Evidence:**

1. `tests/test_union_body_discriminator_annotated.py:7-17`

```
from fastapi.testclient import TestClient
from inline_snapshot import snapshot
from pydantic import BaseModel


@pytest.fixture(name="client")
def client_fixture() -> TestClient:
    from fastapi import Body
    from pydantic import Discriminator, Tag

```

2. `tests/test_computed_fields.py:1-11`

```
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture(name="client")
def get_client(request):
    separate_input_output_schemas = request.param
    app = FastAPI(separate_input_output_schemas=separate_input_output_schemas)

```

3. `tests/test_schema_ref_pydantic_v2.py:5-15`

```
from fastapi.testclient import TestClient
from inline_snapshot import snapshot
from pydantic import BaseModel, ConfigDict, Field


@pytest.fixture(name="client")
def get_client():
    app = FastAPI()

    class ModelWithRef(BaseModel):
```

---

### Uses unittest.mock for mocking

**ID:** `python.conventions.testing_mocking`  
**Category:** testing  
**Language:** python  
**Confidence:** 90%

Exclusively uses unittest.mock. Found 14 usages.

**Statistics:**

- mock_library_counts: `{'unittest_mock': 14}`
- primary_mock_library: `unittest_mock`

**Evidence:**

1. `tests/test_fastapi_cli.py:1-7`

```
import os
import subprocess
import sys
from unittest.mock import patch

import fastapi.cli
import pytest
```

2. `tests/test_tutorial/test_generate_clients/test_tutorial004.py:1-7`

```
import importlib
import json
import pathlib
from unittest.mock import patch

from docs_src.generate_clients import tutorial003_py39

```

3. `tests/test_tutorial/test_python_types/test_tutorial008.py:1-4`

```
from unittest.mock import patch

from docs_src.python_types.tutorial008_py39 import process_items

```

---

### Async-first API design

**ID:** `python.conventions.async_style`  
**Category:** concurrency  
**Language:** python  
**Confidence:** 90%

API endpoints are predominantly async. 12/12 endpoint functions are async. Uses asyncio concurrency patterns (1 usages).

**Statistics:**

- async_count: `12`
- sync_count: `0`
- async_ratio: `1.0`
- asyncio_patterns: `1`

**Evidence:**

1. `docs_src/bigger_applications/app_py39/routers/users.py:2-12`

```

router = APIRouter()


@router.get("/users/", tags=["users"])
async def read_users():
    return [{"username": "Rick"}, {"username": "Morty"}]


@router.get("/users/me", tags=["users"])
```

2. `docs_src/bigger_applications/app_py39/routers/users.py:7-17`

```
async def read_users():
    return [{"username": "Rick"}, {"username": "Morty"}]


@router.get("/users/me", tags=["users"])
async def read_user_me():
    return {"username": "fakecurrentuser"}


@router.get("/users/{username}", tags=["users"])
```

---

### Background jobs with FastAPI BackgroundTasks

**ID:** `python.conventions.background_jobs`  
**Category:** concurrency  
**Language:** python  
**Confidence:** 90%

Uses FastAPI BackgroundTasks for background task processing. Found 10 usages.

**Statistics:**

- job_library_counts: `{'fastapi_background': 10}`
- primary_library: `fastapi_background`
- task_decorators: `0`

**Evidence:**

1. `tests/test_dependency_contextmanager.py:1-9`

```
import json

import pytest
from fastapi import BackgroundTasks, Depends, FastAPI
from fastapi.responses import StreamingResponse
from fastapi.testclient import TestClient

app = FastAPI()
state = {
```

2. `fastapi/background.py:1-9`

```
from typing import Annotated, Any, Callable

from annotated_doc import Doc
from starlette.background import BackgroundTasks as StarletteBackgroundTasks
from typing_extensions import ParamSpec

P = ParamSpec("P")


```

3. `fastapi/__init__.py:3-13`

```
__version__ = "0.128.0"

from starlette import status as status

from .applications import FastAPI as FastAPI
from .background import BackgroundTasks as BackgroundTasks
from .datastructures import UploadFile as UploadFile
from .exceptions import HTTPException as HTTPException
from .exceptions import WebSocketException as WebSocketException
from .param_functions import Body as Body
```

---

### SQLAlchemy 2.0 select() style

**ID:** `python.conventions.db_query_style`  
**Category:** database  
**Language:** python  
**Confidence:** 90%

Uses modern SQLAlchemy 2.0 select() syntax. 8/8 queries use select().

**Statistics:**

- legacy_query_count: `0`
- modern_select_count: `8`
- legacy_ratio: `0.0`
- modern_ratio: `1.0`

**Evidence:**

1. `docs_src/sql_databases/tutorial002_an_py310.py:66-76`

```
def read_heroes(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
):
    heroes = session.exec(select(Hero).offset(offset).limit(limit)).all()
    return heroes


@app.get("/heroes/{hero_id}", response_model=HeroPublic)
```

2. `docs_src/sql_databases/tutorial001_an_py39.py:49-59`

```
def read_heroes(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[Hero]:
    heroes = session.exec(select(Hero).offset(offset).limit(limit)).all()
    return heroes


@app.get("/heroes/{hero_id}")
```

3. `docs_src/sql_databases/tutorial001_py310.py:45-55`

```
def read_heroes(
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: int = Query(default=100, le=100),
) -> list[Hero]:
    heroes = session.exec(select(Hero).offset(offset).limit(limit)).all()
    return heroes


@app.get("/heroes/{hero_id}")
```

---

### Sphinx/reST style docstrings

**ID:** `python.conventions.docstring_style`  
**Category:** documentation  
**Language:** python  
**Confidence:** 90%

Docstrings follow Sphinx/reST style. 2/2 docstrings use this style.

**Statistics:**

- style_counts: `{'sphinx': 2}`
- primary_style: `sphinx`
- primary_ratio: `1.0`

**Evidence:**

1. `docs_src/path_operation_advanced_configuration/tutorial004_py39.py:10-26`

```
    name: str
    description: Union[str, None] = None
    price: float
    tax: Union[float, None] = None
    tags: set[str] = set()


@app.post("/items/", response_model=Item, summary="Create an item")
async def create_item(item: Item):
    """
```

2. `docs_src/path_operation_advanced_configuration/tutorial004_py310.py:8-24`

```
    name: str
    description: str | None = None
    price: float
    tax: float | None = None
    tags: set[str] = set()


@app.post("/items/", response_model=Item, summary="Create an item")
async def create_item(item: Item):
    """
```

---

### Linters: Ruff, mypy

**ID:** `python.conventions.linter`  
**Category:** tooling  
**Language:** python  
**Confidence:** 90%

Uses Ruff, mypy for code quality.

**Statistics:**

- linters: `['ruff', 'mypy']`
- primary_linter: `ruff`
- linter_details: `{'ruff': {'name': 'Ruff', 'config_file': 'pyproject.toml', 'features': ['custom rules', 'ignores configured']}, 'mypy': {'name': 'mypy', 'config_file': 'pyproject.toml'}}`

---

### Uses Python standard logging

**ID:** `python.conventions.logging_library`  
**Category:** logging  
**Language:** python  
**Confidence:** 90%

Exclusively uses Python standard logging for logging. Found 10 usages.

**Statistics:**

- library_counts: `{'stdlib_logging': 10}`
- primary_library: `stdlib_logging`
- primary_ratio: `1.0`

**Evidence:**

1. `fastapi/logger.py:1-3`

```
import logging

logger = logging.getLogger("fastapi")
```

2. `scripts/contributors.py:1-4`

```
import logging
import secrets
import subprocess
from collections import Counter
```

3. `scripts/label_approved.py:1-4`

```
import logging
from typing import Literal

from github import Github
```

---

### JWT-based authentication

**ID:** `python.conventions.auth_pattern`  
**Category:** security  
**Language:** python  
**Confidence:** 85%

Uses JWT tokens for authentication. JWT imports: 16.

**Statistics:**

- oauth2: `49`
- form_auth: `3`
- jwt: `16`
- dependency_auth: `53`

**Evidence:**

1. `docs_src/security/tutorial005_py39.py:1-9`

```
from datetime import datetime, timedelta, timezone
from typing import Union

import jwt
from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    SecurityScopes,
```

2. `docs_src/security/tutorial005_py39.py:6-16`

```
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    SecurityScopes,
)
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from pydantic import BaseModel, ValidationError

# to get a string like this run:
```

3. `docs_src/security/tutorial005_py39.py:1-9`

```
from datetime import datetime, timedelta, timezone
from typing import Union

import jwt
from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    SecurityScopes,
```

---

### FastAPI-style session dependency injection

**ID:** `python.conventions.db_session_lifecycle`  
**Category:** database  
**Language:** python  
**Confidence:** 85%

Uses get_db() dependency pattern with Depends() for session lifecycle. Found 3 get_db definitions.

**Statistics:**

- get_db: `3`
- Depends_injection: `357`

**Evidence:**

1. `tests/test_security_scopes.py:10-20`

```
    return {"count": 0}


@pytest.fixture(name="app")
def app_fixture(call_counter: dict[str, int]):
    def get_db():
        call_counter["count"] += 1
        return f"db_{call_counter['count']}"

    def get_user(db: Annotated[str, Depends(get_db)]):
```

2. `docs_src/dependencies/tutorial007_py39.py:1-6`

```
async def get_db():
    db = DBSession()
    try:
        yield db
    finally:
        db.close()
```

---

### Structured configuration with Pydantic Settings

**ID:** `python.conventions.secrets_access_style`  
**Category:** security  
**Language:** python  
**Confidence:** 85%

Uses Pydantic BaseSettings for configuration management. Found 38 Settings usages.

**Statistics:**

- os_environ: `1`
- pydantic_settings: `38`

**Evidence:**

1. `scripts/contributors.py:237-243`

```

def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = Settings()
    logging.info(f"Using config: {settings.model_dump_json()}")
    g = Github(settings.github_token.get_secret_value())
    repo = g.get_repo(settings.github_repository)
```

2. `scripts/label_approved.py:12-18`

```
    number: int


default_config = {"approved-2": LabelSettings(await_label="awaiting-review", number=2)}


class Settings(BaseSettings):
```

3. `scripts/label_approved.py:22-28`

```
    config: dict[str, LabelSettings] | Literal[""] = default_config


settings = Settings()
if settings.debug:
    logging.basicConfig(level=logging.DEBUG)
else:
```

---

### Primary schema library: Pydantic

**ID:** `python.conventions.schema_library`  
**Category:** api  
**Language:** python  
**Confidence:** 84%

Uses Pydantic as primary schema library (876/895 usages). Also uses: dataclasses.

**Statistics:**

- library_counts: `{'pydantic': 876, 'dataclasses': 19}`
- primary_library: `pydantic`

**Evidence:**

1. `tests/test_multi_body_errors.py:4-10`

```
from fastapi import FastAPI
from fastapi.testclient import TestClient
from inline_snapshot import snapshot
from pydantic import BaseModel, condecimal

app = FastAPI()

```

2. `tests/test_union_body_discriminator_annotated.py:6-12`

```
from fastapi import FastAPI
from fastapi.testclient import TestClient
from inline_snapshot import snapshot
from pydantic import BaseModel


@pytest.fixture(name="client")
```

3. `tests/test_union_body_discriminator_annotated.py:12-18`

```
@pytest.fixture(name="client")
def client_fixture() -> TestClient:
    from fastapi import Body
    from pydantic import Discriminator, Tag

    class Cat(BaseModel):
        pet_type: str = "cat"
```

---

### Primary API framework: FastAPI

**ID:** `python.conventions.api_framework`  
**Category:** api  
**Language:** python  
**Confidence:** 84%

Uses FastAPI as primary framework (2977/3072 usages). Also uses: Starlette, Flask.

**Statistics:**

- framework_counts: `{'fastapi': 2977, 'starlette': 92, 'flask': 3}`
- primary_framework: `fastapi`

**Evidence:**

1. `tests/test_datastructures.py:2-8`

```
from pathlib import Path

import pytest
from fastapi import FastAPI, UploadFile
from fastapi.datastructures import Default
from fastapi.testclient import TestClient

```

2. `tests/test_datastructures.py:3-9`

```

import pytest
from fastapi import FastAPI, UploadFile
from fastapi.datastructures import Default
from fastapi.testclient import TestClient


```

3. `tests/test_datastructures.py:4-10`

```
import pytest
from fastapi import FastAPI, UploadFile
from fastapi.datastructures import Default
from fastapi.testclient import TestClient


def test_upload_file_invalid_pydantic_v2():
```

---

### Caching: functools.lru_cache

**ID:** `python.conventions.caching`  
**Category:** performance  
**Language:** python  
**Confidence:** 80%

Uses functools.lru_cache for caching.

**Statistics:**

- caching_methods: `['lru_cache']`
- primary_method: `lru_cache`
- method_details: `{'lru_cache': {'name': 'functools.lru_cache', 'count': 8}}`

**Evidence:**

1. `fastapi/_compat/v2.py:476-482`

```


@lru_cache
def get_cached_model_fields(model: type[BaseModel]) -> list[ModelField]:
    return get_model_fields(model)  # type: ignore[return-value]


```

2. `scripts/translate.py:32-38`

```


@lru_cache
def get_langs() -> dict[str, str]:
    return yaml.safe_load(Path("docs/language_names.yml").read_text(encoding="utf-8"))


```

3. `scripts/mkdocs_hooks.py:20-26`

```


@lru_cache
def get_missing_translation_content(docs_dir: str) -> str:
    docs_dir_path = Path(docs_dir)
    missing_translation_path = docs_dir_path.parent.parent / "missing-translation.md"
    return missing_translation_path.read_text(encoding="utf-8")
```

---

### Structured logging with request/trace IDs

**ID:** `python.conventions.logging_fields`  
**Category:** logging  
**Language:** python  
**Confidence:** 80%

Structured logging includes request correlation fields. Common fields: requestBody, content, schema, name, format.

**Statistics:**

- top_fields: `{'requestBody': 3, 'content': 3, 'schema': 3, 'name': 3, 'format': 2, 'type': 2, 'examples': 2, 'description': 2, 'price': 2, 'tax': 2}`
- total_field_uses: `26`
- has_request_correlation: `True`

---

### CI/CD: GitHub Actions

**ID:** `generic.conventions.ci_platform`  
**Category:** ci_cd  
**Language:** generic  
**Confidence:** 80%

Uses GitHub Actions for CI/CD. 19 workflow(s) configured.

**Statistics:**

- platforms: `['github_actions']`
- platform_details: `{'github_actions': {'name': 'GitHub Actions', 'workflow_count': 19, 'files': ['smokeshow.yml', 'issue-manager.yml', 'deploy-docs.yml', 'publish.yml', 'labeler.yml']}}`

---

### Dependency updates: Dependabot

**ID:** `generic.conventions.dependency_updates`  
**Category:** dependencies  
**Language:** generic  
**Confidence:** 80%

Automated dependency updates via Dependabot for github-actions.

**Statistics:**

- tools: `['dependabot']`
- tool_details: `{'dependabot': {'name': 'Dependabot', 'ecosystems': ['github-actions']}}`

---

### Git hooks: pre-commit

**ID:** `generic.conventions.git_hooks`  
**Category:** git  
**Language:** generic  
**Confidence:** 80%

Uses pre-commit for Git hooks. Configured: whitespace, file validation, formatting.

**Statistics:**

- hooks_tools: `['pre-commit']`
- hooks_configured: `['whitespace', 'file validation', 'formatting']`
- has_pre_commit: `True`
- has_husky: `False`
- has_lefthook: `False`

---

### Primary database library: SQLModel

**ID:** `python.conventions.db_library`  
**Category:** database  
**Language:** python  
**Confidence:** 79%

Uses SQLModel as primary database library (14/17 imports). Also uses: SQLModel.

**Statistics:**

- library_counts: `{'sqlalchemy': 3, 'sqlmodel': 14}`
- primary_library: `sqlmodel`
- primary_ratio: `0.824`

**Evidence:**

1. `tests/test_tutorial/test_sql_databases/test_tutorial002.py:6-12`

```
from fastapi.testclient import TestClient
from inline_snapshot import Is, snapshot
from sqlalchemy import StaticPool
from sqlmodel import SQLModel, create_engine
from sqlmodel.main import default_registry

from tests.utils import needs_py310
```

2. `tests/test_tutorial/test_sql_databases/test_tutorial002.py:7-13`

```
from inline_snapshot import Is, snapshot
from sqlalchemy import StaticPool
from sqlmodel import SQLModel, create_engine
from sqlmodel.main import default_registry

from tests.utils import needs_py310

```

3. `tests/test_tutorial/test_sql_databases/test_tutorial001.py:6-12`

```
from fastapi.testclient import TestClient
from inline_snapshot import snapshot
from sqlalchemy import StaticPool
from sqlmodel import SQLModel, create_engine
from sqlmodel.main import default_registry

from tests.utils import needs_py310
```

---

### Partial JSDoc coverage

**ID:** `node.conventions.jsdoc`  
**Category:** documentation  
**Language:** node  
**Confidence:** 75%

Some JSDoc documentation present. JSDoc blocks: 12, functions: ~27.

**Statistics:**

- jsdoc_count: `12`
- param_tags: `18`
- returns_tags: `2`
- type_tags: `0`
- function_count: `27`
- jsdoc_ratio: `0.444`

**Evidence:**

1. `docs/en/docs/js/termynal.js:1-6`

```
/**
 * termynal.js
 * A lightweight, modern and extensible animated terminal window, using
 * async/await.
 *
 * @author Ines Montani <ines@ines.io>
```

2. `docs/en/docs/js/termynal.js:8-18`

```
 * @license MIT
 */

'use strict';

/** Generate a terminal widget. */
class Termynal {
    /**
     * Construct the widget's settings.
     * @param {(string|Node)=} container - Query selector or container element.
```

3. `docs/en/docs/js/termynal.js:10-20`

```

'use strict';

/** Generate a terminal widget. */
class Termynal {
    /**
     * Construct the widget's settings.
     * @param {(string|Node)=} container - Query selector or container element.
     * @param {Object=} options - Custom settings.
     * @param {string} options.prefix - Prefix to use for data attributes.
```

---

### Mixed DI patterns: FastAPI Depends dominant

**ID:** `python.conventions.di_style`  
**Category:** dependency_injection  
**Language:** python  
**Confidence:** 73%

Uses multiple DI patterns. Primary: FastAPI Depends (421/454). Also uses: Container-based DI.

**Statistics:**

- pattern_counts: `{'fastapi_depends': 421, 'container_di': 33}`
- dominant_pattern: `fastapi_depends`
- depends_count: `372`
- common_dependency_names: `{'get_current_user': 32, 'get_session': 10, 'get_settings': 4, 'get_db': 3}`

**Evidence:**

1. `tests/test_security_oauth2.py:26-36`

```
    return user


@app.post("/login")
# Here we use string annotations to test them
def login(form_data: "OAuth2PasswordRequestFormStrict" = Depends()):
    return form_data


@app.get("/users/me")
```

2. `tests/test_security_oauth2.py:32-42`

```
    return form_data


@app.get("/users/me")
# Here we use string annotations to test them
def read_current_user(current_user: "User" = Depends(get_current_user)):
    return current_user


client = TestClient(app)
```

3. `tests/test_param_in_path_and_dependency.py:6-16`

```

async def user_exists(user_id: int):
    return True


@app.get("/users/{user_id}", dependencies=[Depends(user_exists)])
async def read_users(user_id: int):
    pass


```

---

### Standard repository layout

**ID:** `generic.conventions.repo_layout`  
**Category:** structure  
**Language:** generic  
**Confidence:** 70%

Repository has standard directories: tests (tests), docs (documentation), scripts (scripts), .github (GitHub configuration)

**Statistics:**

- found_directories: `['tests', 'docs', 'scripts', '.github']`

---

### HTTP errors raised in service layer

**ID:** `python.conventions.error_handling_boundary`  
**Category:** error_handling  
**Language:** python  
**Confidence:** 70%

HTTPException is frequently raised outside the API layer. Service: 0, API: 4, Other: 132.

**Statistics:**

- total_http_exceptions: `136`
- by_role: `{'test': 10, 'other': 122, 'api': 4}`
- api_ratio: `0.029`

**Evidence:**

1. `tests/test_starlette_exception.py:8-18`

```


@app.get("/items/{item_id}")
async def read_item(item_id: str):
    if item_id not in items:
        raise HTTPException(
            status_code=404,
            detail="Item not found",
            headers={"X-Error": "Some custom header"},
        )
```

2. `tests/test_starlette_exception.py:18-28`

```
    return {"item": items[item_id]}


@app.get("/http-no-body-statuscode-exception")
async def no_body_status_code_exception():
    raise HTTPException(status_code=204)


@app.get("/http-no-body-statuscode-with-detail-exception")
async def no_body_status_code_with_detail_exception():
```

3. `tests/test_starlette_exception.py:23-33`

```
    raise HTTPException(status_code=204)


@app.get("/http-no-body-statuscode-with-detail-exception")
async def no_body_status_code_with_detail_exception():
    raise HTTPException(status_code=204, detail="I should just disappear!")


@app.get("/starlette-items/{item_id}")
async def read_starlette_item(item_id: str):
```

---

### Standard repository files

**ID:** `generic.conventions.standard_files`  
**Category:** structure  
**Language:** generic  
**Confidence:** 65%

Repository has standard files: README.md, LICENSE, CONTRIBUTING.md, .gitignore, .pre-commit-config.yaml

**Statistics:**

- found_files: `['README.md', 'LICENSE', 'CONTRIBUTING.md', '.gitignore', '.pre-commit-config.yaml']`

---

### Implicit transaction management

**ID:** `python.conventions.db_transactions`  
**Category:** database  
**Language:** python  
**Confidence:** 60%

Relies on autocommit or implicit transactions. Found 20 explicit commit calls.

**Statistics:**

- begin_count: `0`
- begin_nested_count: `0`
- commit_count: `20`

---

### Low docstring coverage

**ID:** `python.conventions.docstrings`  
**Category:** documentation  
**Language:** python  
**Confidence:** 60%

Few functions have docstrings. Only 82/1326 (6%).

**Statistics:**

- total_public_functions: `1326`
- documented_functions: `82`
- function_doc_ratio: `0.062`
- total_classes: `529`
- documented_classes: `29`
- class_doc_ratio: `0.055`

**Evidence:**

1. `fastapi/applications.py:1041-1051`

```
        app = self.router
        for cls, args, kwargs in reversed(middleware):
            app = cls(app, *args, **kwargs)
        return app

    def openapi(self) -> dict[str, Any]:
        """
        Generate the OpenAPI schema of the application. This is called by FastAPI
        internally.

```

2. `fastapi/applications.py:1266-1276`

```
            endpoint,
            name=name,
            dependencies=dependencies,
        )

    def websocket(
        self,
        path: Annotated[
            str,
            Doc(
```

3. `pdm_build.py:6-12`

```
TIANGOLO_BUILD_PACKAGE = os.getenv("TIANGOLO_BUILD_PACKAGE", "fastapi")


def pdm_build_initialize(context: Context) -> None:
    metadata = context.config.metadata
    # Get custom config for the current package, from the env var
    config: dict[str, Any] = context.config.data["tool"]["tiangolo"][
```

---

### Mixed exception naming conventions

**ID:** `python.conventions.error_taxonomy`  
**Category:** error_handling  
**Language:** python  
**Confidence:** 60%

Exception naming is mixed: 17 *Error, 4 *Exception out of 22 total.

**Statistics:**

- total_custom_exceptions: `22`
- error_suffix_count: `17`
- exception_suffix_count: `4`
- exception_names: `['CustomError', 'AsyncDependencyError', 'SyncDependencyError', 'OtherDependencyError', 'CustomError', 'HTTPException', 'WebSocketException', 'FastAPIError', 'DependencyScopeError', 'ValidationException', 'RequestValidationError', 'WebSocketRequestValidationError', 'ResponseValidationError', 'PydanticV1NotSupportedError', 'ErrorWrapper', 'InternalError', 'InternalError', 'OwnerError', 'InternalError', 'OwnerError']`
- consistency: `0.773`

**Evidence:**

1. `tests/test_ws_router.py:95-101`

```
    pass  # pragma: no cover


class CustomError(Exception):
    pass


```

2. `tests/test_dependency_contextmanager.py:24-30`

```
    return state


class AsyncDependencyError(Exception):
    pass


```

3. `tests/test_dependency_contextmanager.py:28-34`

```
    pass


class SyncDependencyError(Exception):
    pass


```

---

### Distributed exception handling

**ID:** `python.conventions.exception_handlers`  
**Category:** error_handling  
**Language:** python  
**Confidence:** 60%

Exception handlers are spread across 6 modules.

**Statistics:**

- total_handlers: `31`
- decorator_handlers: `12`
- call_handlers: `19`
- handler_files: `['docs_src/handling_errors/tutorial005_py39.py', 'docs_src/handling_errors/tutorial006_py39.py', 'docs_src/handling_errors/tutorial003_py39.py', 'fastapi/applications.py', 'tests/test_validation_error_context.py', 'docs_src/handling_errors/tutorial004_py39.py']`

**Evidence:**

1. `tests/test_validation_error_context.py:27-37`

```
captured_exception = ExceptionCapture()

app.mount(path="/sub", app=sub_app)


@app.exception_handler(RequestValidationError)
@sub_app.exception_handler(RequestValidationError)
async def request_validation_handler(request: Request, exc: RequestValidationError):
    captured_exception.capture(exc)
    raise exc
```

2. `tests/test_validation_error_context.py:28-38`

```

app.mount(path="/sub", app=sub_app)


@app.exception_handler(RequestValidationError)
@sub_app.exception_handler(RequestValidationError)
async def request_validation_handler(request: Request, exc: RequestValidationError):
    captured_exception.capture(exc)
    raise exc

```

3. `tests/test_validation_error_context.py:34-44`

```
async def request_validation_handler(request: Request, exc: RequestValidationError):
    captured_exception.capture(exc)
    raise exc


@app.exception_handler(ResponseValidationError)
@sub_app.exception_handler(ResponseValidationError)
async def response_validation_handler(_: Request, exc: ResponseValidationError):
    captured_exception.capture(exc)
    raise exc
```

---

### Infrequent timeout specification

**ID:** `python.conventions.timeouts`  
**Category:** resilience  
**Language:** python  
**Confidence:** 60%

Timeouts are rarely specified on external calls. Only 4 calls with explicit timeouts.

**Statistics:**

- timeout_indicators: `4`
- no_timeout_indicators: `207`
- timeout_ratio: `0.019`

**Evidence:**

1. `scripts/contributors.py:126-132`

```
) -> dict[str, Any]:
    headers = {"Authorization": f"token {settings.github_token.get_secret_value()}"}
    variables = {"after": after}
    response = httpx.post(
        github_graphql_url,
        headers=headers,
        timeout=settings.httpx_timeout,
```

2. `scripts/notify_translations.py:215-221`

```
        "comment_id": comment_id,
        "body": body,
    }
    response = httpx.post(
        github_graphql_url,
        headers=headers,
        timeout=settings.httpx_timeout,
```

3. `scripts/sponsors.py:97-103`

```
) -> dict[str, Any]:
    headers = {"Authorization": f"token {settings.sponsors_token.get_secret_value()}"}
    variables = {"after": after}
    response = httpx.post(
        github_graphql_url,
        headers=headers,
        timeout=settings.httpx_timeout,
```

---
