# Code Conventions Report

*Generated: 2026-01-24 21:05:01*

## Summary

- **Repository:** `/private/tmp/fastapi`
- **Languages:** node, python
- **Files scanned:** 1252
- **Conventions detected:** 53

## Detected Conventions

| ID | Title | Confidence | Evidence |
|:---|:------|:----------:|:--------:|
| `python.conventions.dependency_management` | Dependency management: uv | 95% | 0 |
| `python.conventions.graphql` | GraphQL: Strawberry | 95% | 2 |
| `python.conventions.naming` | PEP 8 snake_case naming | 95% | 0 |
| `python.conventions.path_handling` | Modern pathlib for path handling | 95% | 5 |
| `python.conventions.testing_framework` | pytest-based testing | 95% | 5 |
| `python.conventions.typing_coverage` | High type annotation coverage | 95% | 4 |
| `python.conventions.string_formatting` | Modern f-string formatting | 95% | 5 |
| `generic.conventions.ci_quality` | CI/CD best practices | 90% | 0 |
| `node.conventions.typescript` | JavaScript codebase | 90% | 0 |
| `python.conventions.cli_framework` | CLI framework: Typer | 90% | 5 |
| `python.conventions.context_managers` | Context manager usage | 90% | 2 |
| `python.conventions.decorator_caching` | Caching decorator pattern | 90% | 5 |
| `python.conventions.import_sorting` | Import sorting: Ruff (isort rules) | 90% | 0 |
| `python.test_conventions.fixtures` | pytest fixtures for test setup | 90% | 5 |
| `python.test_conventions.mocking` | Mocking with unittest.mock / Mock | 90% | 5 |
| `python.test_conventions.parametrized` | Parametrized tests | 90% | 5 |
| `python.conventions.db_query_style` | SQLAlchemy 2.0 select() style | 90% | 5 |
| `python.conventions.linter` | Linters: Ruff, mypy | 90% | 0 |
| `python.conventions.logging_library` | Uses Python standard logging | 90% | 5 |
| `python.test_conventions.assertions` | Plain assert statements | 89% | 5 |
| `python.conventions.class_style` | Data classes: Pydantic models | 86% | 5 |
| `python.conventions.auth_pattern` | JWT-based authentication | 85% | 5 |
| `python.conventions.db_session_lifecycle` | FastAPI-style session dependency injection | 85% | 2 |
| `python.conventions.secrets_access_style` | Structured configuration with Pydantic Settings | 85% | 5 |
| `python.conventions.test_naming` | Test naming: Simple style (test_feature) | 84% | 3 |
| `python.conventions.schema_library` | Primary schema library: Pydantic | 84% | 5 |
| `python.conventions.api_framework` | Primary API framework: FastAPI | 84% | 5 |
| `python.conventions.caching` | Caching: functools.lru_cache | 80% | 5 |
| `python.conventions.enum_usage` | Enum usage: Enum | 80% | 4 |
| `python.conventions.optional_usage` | Optional type annotations | 80% | 5 |
| `python.conventions.pagination_pattern` | Cursor-based pagination | 80% | 0 |
| `python.docs_conventions.example_structure` | Examples with main() entry point | 80% | 0 |
| `python.docs_conventions.organization` | Tutorial-style documentation | 80% | 0 |
| `generic.conventions.ci_platform` | CI/CD: GitHub Actions | 80% | 0 |
| `generic.conventions.dependency_updates` | Dependency updates: Dependabot | 80% | 0 |
| `generic.conventions.git_hooks` | Git hooks: pre-commit | 80% | 0 |
| `python.conventions.validation_style` | Pydantic validation | 78% | 5 |
| `node.conventions.jsdoc` | Partial JSDoc coverage | 75% | 5 |
| `python.conventions.background_jobs` | Background jobs with FastAPI BackgroundTasks | 72% | 4 |
| `generic.conventions.repo_layout` | Standard repository layout | 70% | 0 |
| `python.conventions.constant_naming` | lowercase constant naming | 70% | 5 |
| `python.conventions.error_handling_boundary` | HTTP errors raised in service layer | 70% | 5 |
| `python.conventions.import_style` | Absolute imports preferred | 70% | 5 |
| `python.conventions.response_envelope` | Response envelope classes | 70% | 5 |
| `python.conventions.test_structure` | Distributed test files | 70% | 0 |
| `python.docs_conventions.example_completeness` | Snippet-style examples | 70% | 0 |
| `generic.conventions.standard_files` | Standard repository files | 65% | 0 |
| `python.conventions.db_transactions` | Implicit transaction management | 60% | 0 |
| `python.conventions.docstrings` | Low docstring coverage | 60% | 4 |
| `python.conventions.error_taxonomy` | Mixed exception naming conventions | 60% | 5 |
| `python.conventions.exception_handlers` | Distributed exception handling | 60% | 5 |
| `python.conventions.timeouts` | Infrequent timeout specification | 60% | 4 |
| `python.conventions.error_wrapper` | Error wrapper pattern: time.sleep | 59% | 5 |

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

Function names follow PEP 8 snake_case convention. 305/305 functions use snake_case. Found 21 module-level constants.

**Statistics:**

- snake_case_functions: `305`
- camel_case_functions: `0`
- snake_case_ratio: `1.0`
- module_constants: `21`

---

### Modern pathlib for path handling

**ID:** `python.conventions.path_handling`  
**Category:** code_style  
**Language:** python  
**Confidence:** 95%

Uses pathlib consistently for file paths. 66/66 (100%) use pathlib.

**Statistics:**

- pathlib_count: `66`
- ospath_count: `0`
- pathlib_ratio: `1.0`
- style: `pathlib`

**Evidence:**

1. `fastapi/__init__.py:15-21`

```
from .param_functions import File as File
from .param_functions import Form as Form
from .param_functions import Header as Header
from .param_functions import Path as Path
from .param_functions import Query as Query
from .param_functions import Security as Security
from .requests import Request as Request
```

2. `fastapi/encoders.py:11-17`

```
    IPv6Interface,
    IPv6Network,
)
from pathlib import Path, PurePath
from re import Pattern
from types import GeneratorType
from typing import Annotated, Any, Callable, Optional, Union
```

3. `scripts/contributors.py:3-9`

```
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
```

---

### pytest-based testing

**ID:** `python.conventions.testing_framework`  
**Category:** testing  
**Language:** python  
**Confidence:** 95%

Uses pytest as primary testing framework. Found 887 pytest usages across 465 test files.

**Statistics:**

- framework_counts: `{'pytest': 887, 'unittest': 1}`
- primary_framework: `pytest`
- test_file_count: `465`

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

Type annotations are commonly used in this codebase. 362/366 functions (99%) have at least one type annotation.

**Statistics:**

- total_functions: `366`
- annotated_functions: `362`
- fully_annotated_functions: `225`
- any_annotation_coverage: `0.989`
- full_annotation_coverage: `0.615`

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

### Modern f-string formatting

**ID:** `python.conventions.string_formatting`  
**Category:** code_style  
**Language:** python  
**Confidence:** 95%

Uses f-strings consistently for string formatting. 209/211 (99%) use f-strings.

**Statistics:**

- total_formats: `211`
- fstring_count: `209`
- format_method_count: `2`
- percent_count: `0`
- fstring_ratio: `0.991`
- dominant_style: `fstring`

**Evidence:**

1. `fastapi/params.py:132-138`

```
        super().__init__(**use_kwargs)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.default})"


class Path(Param):  # type: ignore[misc]
```

2. `fastapi/params.py:576-582`

```
        super().__init__(**use_kwargs)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.default})"


class Form(Body):  # type: ignore[misc]
```

3. `fastapi/applications.py:1100-1106`

```
                    oauth2_redirect_url = root_path + oauth2_redirect_url
                return get_swagger_ui_html(
                    openapi_url=openapi_url,
                    title=f"{self.title} - Swagger UI",
                    oauth2_redirect_url=oauth2_redirect_url,
                    init_oauth=self.swagger_ui_init_oauth,
                    swagger_ui_parameters=self.swagger_ui_parameters,
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

### Context manager usage

**ID:** `python.conventions.context_managers`  
**Category:** resource_management  
**Language:** python  
**Confidence:** 90%

Uses context managers for resource management. 25 with statements (17 sync, 8 async). Types: file_io (2).

**Statistics:**

- total_with_statements: `25`
- sync_count: `17`
- async_count: `8`
- context_types: `{'file_io': 2}`

**Evidence:**

1. `scripts/docs.py:460-466`

```
    in_code_block4 = False
    permalinks = set()

    with path.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
```

2. `scripts/docs.py:496-502`

```

        updated_lines.append(line)

    with path.open("w", encoding="utf-8") as f:
        f.writelines(updated_lines)


```

---

### Caching decorator pattern

**ID:** `python.conventions.decorator_caching`  
**Category:** decorators  
**Language:** python  
**Confidence:** 90%

Uses caching decorators for memoization. Found 14 usages.

**Statistics:**

- usage_count: `14`
- top_decorator: `cached_property`
- category: `caching`

**Evidence:**

1. `fastapi/dependencies/models.py:48-58`

```
    parent_oauth_scopes: Optional[list[str]] = None
    use_cache: bool = True
    path: Optional[str] = None
    scope: Union[Literal["function", "request"], None] = None

    @cached_property
    def oauth_scopes(self) -> list[str]:
        scopes = self.parent_oauth_scopes.copy() if self.parent_oauth_scopes else []
        # This doesn't use a set to preserve order, just in case
        for scope in self.own_oauth_scopes or []:
```

2. `fastapi/dependencies/models.py:57-67`

```
        for scope in self.own_oauth_scopes or []:
            if scope not in scopes:
                scopes.append(scope)
        return scopes

    @cached_property
    def cache_key(self) -> DependencyCacheKey:
        scopes_for_cache = (
            tuple(sorted(set(self.oauth_scopes or []))) if self._uses_scopes else ()
        )
```

3. `fastapi/dependencies/models.py:68-78`

```
            self.call,
            scopes_for_cache,
            self.computed_scope or "",
        )

    @cached_property
    def _uses_scopes(self) -> bool:
        if self.own_oauth_scopes:
            return True
        if self.security_scopes_param_name is not None:
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

### pytest fixtures for test setup

**ID:** `python.test_conventions.fixtures`  
**Category:** testing  
**Language:** python  
**Confidence:** 90%

Uses pytest @fixture decorator for test setup. Found 186 fixtures. Uses 1 conftest.py file(s) for shared fixtures.

**Statistics:**

- fixture_counts: `{'pytest_fixture': 186}`
- conftest_files: `1`
- pattern: `pytest_fixture`

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

### Mocking with unittest.mock / Mock

**ID:** `python.test_conventions.mocking`  
**Category:** testing  
**Language:** python  
**Confidence:** 90%

Uses unittest.mock / Mock for test mocking. Found 14 usages. Also uses: pytest monkeypatch fixture, @patch decorator.

**Statistics:**

- mock_counts: `{'monkeypatch': 10, 'unittest_mock': 14, 'patch_decorator': 1}`
- primary_pattern: `unittest_mock`

**Evidence:**

1. `tests/test_fastapi_cli.py:1-9`

```
import os
import subprocess
import sys
from unittest.mock import patch

import fastapi.cli
import pytest


```

2. `tests/test_tutorial/test_generate_clients/test_tutorial004.py:1-9`

```
import importlib
import json
import pathlib
from unittest.mock import patch

from docs_src.generate_clients import tutorial003_py39


def test_remove_tags(tmp_path: pathlib.Path):
```

3. `tests/test_tutorial/test_python_types/test_tutorial008.py:1-6`

```
from unittest.mock import patch

from docs_src.python_types.tutorial008_py39 import process_items


def test_process_items():
```

---

### Parametrized tests

**ID:** `python.test_conventions.parametrized`  
**Category:** testing  
**Language:** python  
**Confidence:** 90%

Uses @pytest.mark.parametrize for data-driven tests. Found 442 parametrized test functions.

**Statistics:**

- parametrize_count: `442`

**Evidence:**

1. `tests/test_computed_fields.py:29-39`

```

    client = TestClient(app)
    return client


@pytest.mark.parametrize("client", [True, False], indirect=True)
@pytest.mark.parametrize("path", ["/", "/responses"])
def test_get(client: TestClient, path: str):
    response = client.get(path)
    assert response.status_code == 200, response.text
```

2. `tests/test_computed_fields.py:30-40`

```
    client = TestClient(app)
    return client


@pytest.mark.parametrize("client", [True, False], indirect=True)
@pytest.mark.parametrize("path", ["/", "/responses"])
def test_get(client: TestClient, path: str):
    response = client.get(path)
    assert response.status_code == 200, response.text
    assert response.json() == {"width": 3, "length": 4, "area": 12}
```

3. `tests/test_computed_fields.py:37-47`

```
    response = client.get(path)
    assert response.status_code == 200, response.text
    assert response.json() == {"width": 3, "length": 4, "area": 12}


@pytest.mark.parametrize("client", [True, False], indirect=True)
def test_openapi_schema(client: TestClient):
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == {
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

### Plain assert statements

**ID:** `python.test_conventions.assertions`  
**Category:** testing  
**Language:** python  
**Confidence:** 89%

Uses plain Python assert statements for test assertions. 4113 assert statements. Uses pytest.raises for exception testing (94 usages).

**Statistics:**

- assertion_counts: `{'plain_assert': 4113, 'pytest_raises': 94, 'pytest_warns': 15}`
- style: `plain_assert`

**Evidence:**

1. `tests/test_datastructures.py:8-14`

```


def test_upload_file_invalid_pydantic_v2():
    with pytest.raises(ValueError):
        UploadFile._validate("not a Starlette UploadFile", {})


```

2. `tests/test_openapi_schema_type.py:22-26`

```

def test_invalid_type_value() -> None:
    """Test that Schema raises ValueError for invalid type values."""
    with pytest.raises(ValueError, match="2 validation errors for Schema"):
        Schema(type=True)  # type: ignore[arg-type]
```

3. `tests/test_response_model_invalid.py:8-14`

```


def test_invalid_response_model_raises():
    with pytest.raises(FastAPIError):
        app = FastAPI()

        @app.get("/", response_model=NonPydanticModel)
```

---

### Data classes: Pydantic models

**ID:** `python.conventions.class_style`  
**Category:** code_style  
**Language:** python  
**Confidence:** 86%

Uses Pydantic models for structured data. 84/98 structured classes use this pattern.

**Statistics:**

- dataclass_count: `6`
- pydantic_count: `84`
- attrs_count: `0`
- namedtuple_count: `8`
- plain_count: `58`
- dominant_style: `pydantic`

**Evidence:**

1. `fastapi/security/http.py:11-21`

```
from pydantic import BaseModel
from starlette.requests import Request
from starlette.status import HTTP_401_UNAUTHORIZED


class HTTPBasicCredentials(BaseModel):
    """
    The HTTP Basic credentials given as the result of using `HTTPBasic` in a
    dependency.

```

2. `fastapi/security/http.py:24-34`

```

    username: Annotated[str, Doc("The HTTP Basic username.")]
    password: Annotated[str, Doc("The HTTP Basic password.")]


class HTTPAuthorizationCredentials(BaseModel):
    """
    The HTTP authorization credentials in the result of using `HTTPBearer` or
    `HTTPDigest` in a dependency.

```

3. `fastapi/openapi/models.py:52-62`

```
            cls, source: type[Any], handler: Callable[[Any], Mapping[str, Any]]
        ) -> Mapping[str, Any]:
            return with_info_plain_validator_function(cls._validate)


class BaseModelWithConfig(BaseModel):
    model_config = {"extra": "allow"}


class Contact(BaseModelWithConfig):
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

### Test naming: Simple style (test_feature)

**ID:** `python.conventions.test_naming`  
**Category:** testing  
**Language:** python  
**Confidence:** 84%

Uses Simple style (test_feature) naming. 2006/2047 (98%) test functions.

**Statistics:**

- total_test_functions: `2047`
- pattern_counts: `{'simple': 2006, 'action_result': 41}`
- test_class_count: `0`
- dominant_pattern: `simple`

**Evidence:**

1. `tests/test_datastructures.py:7-13`

```
from fastapi.testclient import TestClient


def test_upload_file_invalid_pydantic_v2():
    with pytest.raises(ValueError):
        UploadFile._validate("not a Starlette UploadFile", {})

```

2. `tests/test_datastructures.py:12-18`

```
        UploadFile._validate("not a Starlette UploadFile", {})


def test_default_placeholder_equals():
    placeholder_1 = Default("a")
    placeholder_2 = Default("a")
    assert placeholder_1 == placeholder_2
```

3. `tests/test_datastructures.py:19-25`

```
    assert placeholder_1.value == placeholder_2.value


def test_default_placeholder_bool():
    placeholder_a = Default("a")
    placeholder_b = Default("")
    assert placeholder_a
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

### Enum usage: Enum

**ID:** `python.conventions.enum_usage`  
**Category:** code_style  
**Language:** python  
**Confidence:** 80%

Uses Python enums for categorical values. Found 4 enum class(es).

**Statistics:**

- enum_count: `4`
- enum_types: `{'Enum': 4}`
- enum_names: `['ParamTypes', 'ParameterInType', 'SecuritySchemeType', 'APIKeyIn']`

**Evidence:**

1. `fastapi/params.py:15-25`

```
)

_Unset: Any = Undefined


class ParamTypes(Enum):
    query = "query"
    header = "header"
    path = "path"
    cookie = "cookie"
```

2. `fastapi/openapi/models.py:219-229`

```
    externalValue: Optional[AnyUrl]

    __pydantic_config__ = {"extra": "allow"}  # type: ignore[misc]


class ParameterInType(Enum):
    query = "query"
    header = "header"
    path = "path"
    cookie = "cookie"
```

3. `fastapi/openapi/models.py:319-329`

```
    trace: Optional[Operation] = None
    servers: Optional[list[Server]] = None
    parameters: Optional[list[Union[Parameter, Reference]]] = None


class SecuritySchemeType(Enum):
    apiKey = "apiKey"
    http = "http"
    oauth2 = "oauth2"
    openIdConnect = "openIdConnect"
```

---

### Optional type annotations

**ID:** `python.conventions.optional_usage`  
**Category:** typing  
**Language:** python  
**Confidence:** 80%

Uses Optional type hint for nullable values. Found 20 imports of Optional.

**Statistics:**

- optional_imports: `20`

**Evidence:**

1. `fastapi/params.py:2-8`

```
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Annotated, Any, Callable, Optional, Union

from fastapi.exceptions import FastAPIDeprecationWarning
from fastapi.openapi.models import Example
```

2. `fastapi/applications.py:1-6`

```
from collections.abc import Awaitable, Coroutine, Sequence
from enum import Enum
from typing import (
    Annotated,
    Any,
    Callable,
```

3. `fastapi/encoders.py:14-20`

```
from pathlib import Path, PurePath
from re import Pattern
from types import GeneratorType
from typing import Annotated, Any, Callable, Optional, Union
from uuid import UUID

from annotated_doc import Doc
```

---

### Cursor-based pagination

**ID:** `python.conventions.pagination_pattern`  
**Category:** api  
**Language:** python  
**Confidence:** 80%

Uses cursor-based pagination. 8 cursor/after/before usages.

**Statistics:**

- offset_count: `0`
- cursor_count: `8`
- page_count: `0`
- pattern: `cursor`

---

### Examples with main() entry point

**ID:** `python.docs_conventions.example_structure`  
**Category:** documentation  
**Language:** python  
**Confidence:** 80%

Examples use main() function as entry point. Found 14 examples with main().

**Statistics:**

- total_example_files: `622`
- standalone_count: `1`
- main_function_count: `14`
- example_directories: `{'docs_src': 622}`
- topics: `{}`
- pattern: `main_function`

---

### Tutorial-style documentation

**ID:** `python.docs_conventions.organization`  
**Category:** documentation  
**Language:** python  
**Confidence:** 80%

Documentation organized as tutorials. Found 496 tutorial files. Common types: tutorial.

**Statistics:**

- total_files: `622`
- file_prefixes: `{'tutorial': 496}`
- dir_structure: `{'depth_2': 567, 'depth_3': 45, 'depth_4': 10}`
- style: `tutorials`

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
- primary_tool: `dependabot`

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
- hook_tool: `pre-commit`
- has_pre_commit: `True`
- has_husky: `False`
- has_lefthook: `False`

---

### Pydantic validation

**ID:** `python.conventions.validation_style`  
**Category:** validation  
**Language:** python  
**Confidence:** 78%

Uses Pydantic validation for input validation. 17/28 (61%) validation patterns use this approach.

**Statistics:**

- validation_counts: `{'pydantic': 17, 'manual': 11}`
- dominant_style: `pydantic`
- dominant_ratio: `0.607`

**Evidence:**

1. `fastapi/encoders.py:20-26`

```
from annotated_doc import Doc
from fastapi.exceptions import PydanticV1NotSupportedError
from fastapi.types import IncEx
from pydantic import BaseModel
from pydantic.color import Color
from pydantic.networks import AnyUrl, NameEmail
from pydantic.types import SecretBytes, SecretStr
```

2. `fastapi/types.py:2-8`

```
from enum import Enum
from typing import Any, Callable, Optional, TypeVar, Union

from pydantic import BaseModel

DecoratedCallable = TypeVar("DecoratedCallable", bound=Callable[..., Any])
UnionType = getattr(types, "UnionType", Union)
```

3. `fastapi/utils.py:21-27`

```
)
from fastapi.datastructures import DefaultPlaceholder, DefaultType
from fastapi.exceptions import FastAPIDeprecationWarning, PydanticV1NotSupportedError
from pydantic import BaseModel
from pydantic.fields import FieldInfo
from typing_extensions import Literal

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

### Background jobs with FastAPI BackgroundTasks

**ID:** `python.conventions.background_jobs`  
**Category:** concurrency  
**Language:** python  
**Confidence:** 72%

Uses FastAPI BackgroundTasks for background task processing. Found 4 usages.

**Statistics:**

- job_library_counts: `{'fastapi_background': 4}`
- primary_library: `fastapi_background`
- task_decorators: `0`

**Evidence:**

1. `fastapi/background.py:1-9`

```
from typing import Annotated, Any, Callable

from annotated_doc import Doc
from starlette.background import BackgroundTasks as StarletteBackgroundTasks
from typing_extensions import ParamSpec

P = ParamSpec("P")


```

2. `fastapi/__init__.py:3-13`

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

3. `fastapi/dependencies/utils.py:38-48`

```
    lenient_issubclass,
    sequence_types,
    serialize_sequence_value,
    value_is_sequence,
)
from fastapi.background import BackgroundTasks
from fastapi.concurrency import (
    asynccontextmanager,
    contextmanager_in_threadpool,
)
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

### lowercase constant naming

**ID:** `python.conventions.constant_naming`  
**Category:** naming  
**Language:** python  
**Confidence:** 70%

Uses lowercase naming for module-level values. 87/91 use lowercase.

**Statistics:**

- all_caps_count: `4`
- lowercase_count: `87`
- all_caps_ratio: `0.044`
- style: `lowercase`

**Evidence:**

1. `fastapi/params.py:19-23`

```

class ParamTypes(Enum):
    query = "query"
    header = "header"
    path = "path"
```

2. `fastapi/params.py:20-24`

```
class ParamTypes(Enum):
    query = "query"
    header = "header"
    path = "path"
    cookie = "cookie"
```

3. `fastapi/params.py:21-25`

```
    query = "query"
    header = "header"
    path = "path"
    cookie = "cookie"

```

---

### HTTP errors raised in service layer

**ID:** `python.conventions.error_handling_boundary`  
**Category:** error_handling  
**Language:** python  
**Confidence:** 70%

HTTPException is frequently raised outside the API layer. Service: 0, API: 0, Other: 136.

**Statistics:**

- total_http_exceptions: `136`
- by_role: `{'test': 10, 'other': 5, 'docs': 121}`
- api_ratio: `0.0`

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

### Absolute imports preferred

**ID:** `python.conventions.import_style`  
**Category:** code_style  
**Language:** python  
**Confidence:** 70%

Prefers absolute imports. 74 relative vs 491 absolute imports.

**Statistics:**

- relative_count: `74`
- absolute_count: `491`
- relative_ratio: `0.131`
- style: `absolute`

**Evidence:**

1. `fastapi/params.py:10-16`

```
from pydantic.fields import FieldInfo
from typing_extensions import Literal, deprecated

from ._compat import (
    Undefined,
)

```

2. `fastapi/__init__.py:4-10`

```

from starlette import status as status

from .applications import FastAPI as FastAPI
from .background import BackgroundTasks as BackgroundTasks
from .datastructures import UploadFile as UploadFile
from .exceptions import HTTPException as HTTPException
```

3. `fastapi/__init__.py:5-11`

```
from starlette import status as status

from .applications import FastAPI as FastAPI
from .background import BackgroundTasks as BackgroundTasks
from .datastructures import UploadFile as UploadFile
from .exceptions import HTTPException as HTTPException
from .exceptions import WebSocketException as WebSocketException
```

---

### Response envelope classes

**ID:** `python.conventions.response_envelope`  
**Category:** api  
**Language:** python  
**Confidence:** 70%

Uses response envelope classes (5 found).

**Statistics:**

- envelope_classes: `5`
- field_counts: `{'errors': 4, 'message': 2, 'items': 5}`
- pattern: `class_based`

**Evidence:**

1. `fastapi/responses.py:18-28`

```
    import orjson
except ImportError:  # pragma: nocover
    orjson = None  # type: ignore


class UJSONResponse(JSONResponse):
    """
    JSON response using the high-performance ujson library to serialize data to JSON.

    Read more about it in the
```

2. `fastapi/responses.py:31-41`

```
    def render(self, content: Any) -> bytes:
        assert ujson is not None, "ujson must be installed to use UJSONResponse"
        return ujson.dumps(content, ensure_ascii=False).encode("utf-8")


class ORJSONResponse(JSONResponse):
    """
    JSON response using the high-performance orjson library to serialize data to JSON.

    Read more about it in the
```

3. `scripts/contributors.py:102-112`

```

class PRsRepository(BaseModel):
    pullRequests: PullRequests


class PRsResponseData(BaseModel):
    repository: PRsRepository


class PRsResponse(BaseModel):
```

---

### Distributed test files

**ID:** `python.conventions.test_structure`  
**Category:** testing  
**Language:** python  
**Confidence:** 70%

Test files spread across 2 directories. 465 total test files.

**Statistics:**

- test_file_count: `465`
- test_directories: `{'tests': 454, 'scripts': 11}`
- has_unit: `False`
- has_integration: `False`
- has_e2e: `False`
- structure: `distributed`
- categories: `[]`

---

### Snippet-style examples

**ID:** `python.docs_conventions.example_completeness`  
**Category:** documentation  
**Language:** python  
**Confidence:** 70%

Documentation uses code snippets (may require context from docs). Only 77/530 examples have all imports.

**Statistics:**

- complete_examples: `77`
- incomplete_examples: `453`
- complete_ratio: `0.145`
- style: `snippets`

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

Few functions have docstrings. Only 72/366 (20%).

**Statistics:**

- total_public_functions: `366`
- documented_functions: `72`
- function_doc_ratio: `0.197`
- total_classes: `170`
- documented_classes: `29`
- class_doc_ratio: `0.171`

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
- handler_files: `['docs_src/handling_errors/tutorial005_py39.py', 'tests/test_validation_error_context.py', 'docs_src/handling_errors/tutorial004_py39.py', 'docs_src/handling_errors/tutorial006_py39.py', 'docs_src/handling_errors/tutorial003_py39.py', 'fastapi/applications.py']`

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

### Error wrapper pattern: time.sleep

**ID:** `python.conventions.error_wrapper`  
**Category:** error_handling  
**Language:** python  
**Confidence:** 59%

Uses 'time.sleep' as a common error handler function. Called in 6/28 (21%) except blocks. Also uses: errors.append, RuntimeError.

**Statistics:**

- wrapper_function: `time.sleep`
- usage_count: `6`
- total_handlers: `28`
- usage_ratio: `0.214`
- other_wrappers: `['errors.append', 'RuntimeError']`

**Evidence:**

1. `scripts/playwright/cookie_param_models/image01.py:28-38`

```
)
try:
    for _ in range(3):
        try:
            response = httpx.get("http://localhost:8000/docs")
        except httpx.ConnectError:
            time.sleep(1)
            break
    with sync_playwright() as playwright:
        run(playwright)
```

2. `scripts/playwright/sql_databases/image01.py:26-36`

```
)
try:
    for _ in range(3):
        try:
            response = httpx.get("http://localhost:8000/docs")
        except httpx.ConnectError:
            time.sleep(1)
            break
    with sync_playwright() as playwright:
        run(playwright)
```

3. `scripts/playwright/sql_databases/image02.py:26-36`

```
)
try:
    for _ in range(3):
        try:
            response = httpx.get("http://localhost:8000/docs")
        except httpx.ConnectError:
            time.sleep(1)
            break
    with sync_playwright() as playwright:
        run(playwright)
```

---
