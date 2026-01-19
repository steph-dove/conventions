# Code Conventions Report

*Generated: 2026-01-19 15:47:14*

## Summary

- **Repository:** `/Users/stephaniedover/projects/code_conventions_finder`
- **Languages:** node, python
- **Files scanned:** 120
- **Conventions detected:** 18

## Detected Conventions

| ID | Title | Confidence | Evidence |
|:---|:------|:----------:|:--------:|
| `python.conventions.naming` | PEP 8 snake_case naming | 95% | 0 |
| `python.conventions.testing_framework` | pytest-based testing | 95% | 5 |
| `python.conventions.typing_coverage` | High type annotation coverage | 95% | 4 |
| `python.conventions.cli_framework` | CLI framework: Typer | 90% | 2 |
| `python.conventions.import_sorting` | Import sorting: Ruff (isort rules) | 90% | 0 |
| `python.conventions.testing_fixtures` | Centralized pytest fixtures in conftest.py | 90% | 5 |
| `python.conventions.docstring_style` | Google style docstrings | 90% | 5 |
| `python.conventions.linter` | Linters: Ruff, mypy | 90% | 0 |
| `python.conventions.docstrings` | High docstring coverage | 89% | 4 |
| `python.conventions.exception_handlers` | Centralized exception handling | 85% | 3 |
| `python.conventions.graphql` | GraphQL: graphql-core | 85% | 1 |
| `python.conventions.logging_library` | Uses Python standard logging | 78% | 4 |
| `node.conventions.framework` | Uses Express.js | 73% | 1 |
| `python.conventions.schema_library` | Primary schema library: dataclasses | 69% | 5 |
| `python.conventions.di_style` | Container-based dependency injection | 68% | 4 |
| `python.conventions.testing_mocking` | Uses unittest.mock for mocking | 66% | 2 |
| `generic.conventions.repo_layout` | Standard repository layout | 60% | 0 |
| `python.conventions.correlation_ids` | Request/correlation ID propagation | 60% | 2 |

## Convention Details

### PEP 8 snake_case naming

**ID:** `python.conventions.naming`  
**Category:** style  
**Language:** python  
**Confidence:** 95%

Function names follow PEP 8 snake_case convention. 193/193 functions use snake_case. Found 16 module-level constants.

**Statistics:**

- snake_case_functions: `193`
- camel_case_functions: `0`
- snake_case_ratio: `1.0`
- module_constants: `16`

---

### pytest-based testing

**ID:** `python.conventions.testing_framework`  
**Category:** testing  
**Language:** python  
**Confidence:** 95%

Uses pytest as primary testing framework. Found 41 pytest usages.

**Statistics:**

- framework_counts: `{'pytest': 41, 'unittest_style': 37}`
- primary_framework: `pytest`
- test_file_count: `18`

**Evidence:**

1. `tests/conftest.py:6-12`

```
from pathlib import Path
from typing import Any

import pytest

from conventions.config import ConventionsConfig
from conventions.detectors.base import DetectorContext
```

2. `tests/unit/test_ratings.py:1-7`

```
"""Tests for rating rules and scoring."""
from __future__ import annotations

import pytest

from conventions.ratings import (
    DEFAULT_RATING_RULE,
```

3. `tests/unit/test_config.py:4-10`

```
import json
from pathlib import Path

import pytest

from conventions.config import (
    CONFIG_FILE_NAMES,
```

---

### High type annotation coverage

**ID:** `python.conventions.typing_coverage`  
**Category:** typing  
**Language:** python  
**Confidence:** 95%

Type annotations are commonly used in this codebase. 199/201 functions (99%) have at least one type annotation.

**Statistics:**

- total_functions: `201`
- annotated_functions: `199`
- fully_annotated_functions: `45`
- any_annotation_coverage: `0.99`
- full_annotation_coverage: `0.224`

**Evidence:**

1. `src/conventions/plugins.py:46-56`

```


class PluginLoader:
    """Loads and registers plugins from Python files."""

    def __init__(self, progress_callback: Optional[Callable[[str], None]] = None):
        """Initialize the plugin loader.

        Args:
            progress_callback: Optional callback for progress messages
```

2. `src/conventions/plugins.py:60-70`

```
    def _log(self, message: str) -> None:
        """Log a message via callback if available."""
        if self.progress_callback:
            self.progress_callback(message)

    def load_from_path(self, path: str) -> dict[str, Any]:
        """Load a plugin from a Python file path.

        Args:
            path: Path to the plugin Python file
```

3. `src/conventions/detectors/base.py:53-63`

```
    # Override in subclasses
    name: str = "base"
    description: str = "Base detector"
    languages: set[str] = set()  # Empty means language-agnostic

    def __init__(self):
        pass

    def should_run(self, ctx: DetectorContext) -> bool:
        """Check if this detector should run given the context."""
```

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
- framework_details: `{'typer': {'name': 'Typer', 'import_count': 2}}`

**Evidence:**

1. `tests/integration/test_cli.py:6-12`

```
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from conventions.cli import app

```

2. `src/conventions/cli.py:5-11`

```
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from .config import ConventionsConfig, load_config
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

Uses pytest fixtures with 1 conftest.py file(s). Found 24 fixture definitions.

**Statistics:**

- fixture_count: `24`
- conftest_count: `1`
- async_fixture_count: `0`

**Evidence:**

1. `tests/conftest.py:11-21`

```
from conventions.config import ConventionsConfig
from conventions.detectors.base import DetectorContext
from conventions.schemas import ConventionRule, ConventionsOutput, EvidenceSnippet, RepoMetadata


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    """Create a minimal repository structure for testing."""
    # Create basic structure
    (tmp_path / "src").mkdir()
```

2. `tests/conftest.py:25-35`

```
    (tmp_path / ".gitignore").write_text("*.pyc\n__pycache__/\n.venv/\n")

    return tmp_path


@pytest.fixture
def sample_repo(tmp_repo: Path) -> Path:
    """Create a sample repository with Python files for testing."""
    # Create Python files
    typed_py = '''"""Typed module example."""
```

3. `tests/conftest.py:129-139`

```
    (tmp_repo / "tests" / "conftest.py").write_text(conftest)

    return tmp_repo


@pytest.fixture
def node_sample_repo(tmp_repo: Path) -> Path:
    """Create a sample repository with TypeScript files for testing."""
    (tmp_repo / "src").mkdir(exist_ok=True)

```

---

### Google style docstrings

**ID:** `python.conventions.docstring_style`  
**Category:** documentation  
**Language:** python  
**Confidence:** 90%

Docstrings follow Google style. 26/26 docstrings use this style.

**Statistics:**

- style_counts: `{'google': 26}`
- primary_style: `google`
- primary_ratio: `1.0`

**Evidence:**

1. `src/conventions/plugins.py:43-59`

```
class PluginError(Exception):
    """Error loading or validating a plugin."""
    pass


class PluginLoader:
    """Loads and registers plugins from Python files."""

    def __init__(self, progress_callback: Optional[Callable[[str], None]] = None):
        """Initialize the plugin loader.
```

2. `src/conventions/plugins.py:57-73`

```
        self.progress_callback = progress_callback
        self.loaded_plugins: list[str] = []

    def _log(self, message: str) -> None:
        """Log a message via callback if available."""
        if self.progress_callback:
            self.progress_callback(message)

    def load_from_path(self, path: str) -> dict[str, Any]:
        """Load a plugin from a Python file path.
```

3. `src/conventions/plugins.py:136-152`

```
                        "Must be a RatingRule instance."
                    )
                result["rating_rules"][rule_id] = rule
                self._log(f"  Found rating rule: {rule_id}")

        self.loaded_plugins.append(str(plugin_path))
        return result

    def register_detectors(self, detectors: list[Type[BaseDetector]]) -> None:
        """Register detector classes with the registry.
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

### High docstring coverage

**ID:** `python.conventions.docstrings`  
**Category:** documentation  
**Language:** python  
**Confidence:** 89%

Most public functions have docstrings. Functions: 192/201 (96%). Classes: 106/111.

**Statistics:**

- total_public_functions: `201`
- documented_functions: `192`
- function_doc_ratio: `0.955`
- total_classes: `111`
- documented_classes: `106`
- class_doc_ratio: `0.955`

**Evidence:**

1. `src/conventions/plugins.py:46-56`

```


class PluginLoader:
    """Loads and registers plugins from Python files."""

    def __init__(self, progress_callback: Optional[Callable[[str], None]] = None):
        """Initialize the plugin loader.

        Args:
            progress_callback: Optional callback for progress messages
```

2. `src/conventions/plugins.py:60-70`

```
    def _log(self, message: str) -> None:
        """Log a message via callback if available."""
        if self.progress_callback:
            self.progress_callback(message)

    def load_from_path(self, path: str) -> dict[str, Any]:
        """Load a plugin from a Python file path.

        Args:
            path: Path to the plugin Python file
```

3. `src/conventions/scan.py:28-34`

```
    """
    from .detectors.orchestrator import run_detectors

    def progress(msg: str) -> None:
        if verbose:
            print(f"  {msg}")

```

---

### Centralized exception handling

**ID:** `python.conventions.exception_handlers`  
**Category:** error_handling  
**Language:** python  
**Confidence:** 85%

Exception handlers are centralized in a single module. Found 3 handlers in src/conventions/detectors/python/errors.py.

**Statistics:**

- total_handlers: `3`
- decorator_handlers: `0`
- call_handlers: `3`
- handler_files: `['src/conventions/detectors/python/errors.py']`

**Evidence:**

1. `src/conventions/detectors/python/errors.py:31-41`

```

        # Detect custom exception taxonomy
        self._detect_exception_taxonomy(ctx, index, result)

        # Detect exception handler patterns
        self._detect_exception_handlers(ctx, index, result)

        return result

    def _detect_http_exception_boundary(
```

2. `src/conventions/detectors/python/errors.py:208-218`

```
        exception_handler_decorators = []
        exception_handler_calls = []

        for rel_path, dec in index.get_all_decorators():
            if "exception_handler" in dec.name.lower():
                exception_handler_decorators.append((rel_path, dec.line, dec.name))

        for rel_path, call in index.get_all_calls():
            if "add_exception_handler" in call.name or "exception_handler" in call.name.lower():
                exception_handler_calls.append((rel_path, call.line, call.name))
```

3. `src/conventions/detectors/python/errors.py:212-222`

```
            if "exception_handler" in dec.name.lower():
                exception_handler_decorators.append((rel_path, dec.line, dec.name))

        for rel_path, call in index.get_all_calls():
            if "add_exception_handler" in call.name or "exception_handler" in call.name.lower():
                exception_handler_calls.append((rel_path, call.line, call.name))

        total_handlers = len(exception_handler_decorators) + len(exception_handler_calls)

        if total_handlers < 2:
```

---

### GraphQL: graphql-core

**ID:** `python.conventions.graphql`  
**Category:** api  
**Language:** python  
**Confidence:** 85%

Uses graphql-core for GraphQL API. (low-level)

**Statistics:**

- libraries: `['graphql_core']`
- primary_library: `graphql_core`
- library_details: `{'graphql_core': {'name': 'graphql-core', 'import_count': 1, 'style': 'low-level'}}`

**Evidence:**

1. `src/conventions/detectors/python/__init__.py:21-27`

```
from .cli_patterns import PythonCLIPatternDetector
from .background_tasks import PythonBackgroundTaskDetector
from .caching import PythonCachingDetector
from .graphql import PythonGraphQLDetector

__all__ = [
    "PythonIndex",
```

---

### Uses Python standard logging

**ID:** `python.conventions.logging_library`  
**Category:** logging  
**Language:** python  
**Confidence:** 78%

Exclusively uses Python standard logging for logging. Found 4 usages.

**Statistics:**

- library_counts: `{'stdlib_logging': 4}`
- primary_library: `stdlib_logging`
- primary_ratio: `1.0`

**Evidence:**

1. `src/conventions/detectors/go/__init__.py:7-13`

```
from .conventions import GoConventionsDetector
from .documentation import GoDocumentationDetector
from .testing import GoTestingDetector
from .logging import GoLoggingDetector
from .errors import GoErrorHandlingDetector
from .security import GoSecurityDetector
from .concurrency import GoConcurrencyDetector
```

2. `src/conventions/detectors/python/__init__.py:6-12`

```
from .typing import PythonTypingConventionsDetector
from .documentation import PythonDocstringNamingConventionsDetector
from .testing import PythonTestingConventionsDetector
from .logging import PythonLoggingConventionsDetector
from .errors import PythonErrorConventionsDetector
from .security import PythonSecurityConventionsDetector
from .async_concurrency import PythonAsyncConventionsDetector
```

3. `src/conventions/detectors/rust/__init__.py:14-20`

```
from .documentation import RustDocumentationDetector
from .unsafe_code import RustUnsafeDetector
from .macros import RustMacrosDetector
from .logging import RustLoggingDetector
from .database import RustDatabaseDetector

__all__ = [
```

---

### Uses Express.js

**ID:** `node.conventions.framework`  
**Category:** api  
**Language:** node  
**Confidence:** 73%

Web application built with Express.js. Found 1 imports.

**Statistics:**

- framework_counts: `{'express': 1}`
- primary_framework: `express`

**Evidence:**

1. `tests/fixtures/node_typescript.ts:1-7`

```
/**
 * Example TypeScript file demonstrating conventions.
 */
import { Request, Response, NextFunction } from 'express';

interface User {
    id: number;
```

---

### Primary schema library: dataclasses

**ID:** `python.conventions.schema_library`  
**Category:** api  
**Language:** python  
**Confidence:** 69%

Uses dataclasses as primary schema library (8/15 usages). Also uses: Pydantic.

**Statistics:**

- library_counts: `{'pydantic': 7, 'dataclasses': 8}`
- primary_library: `dataclasses`

**Evidence:**

1. `src/conventions/config.py:3-9`

```
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

```

2. `src/conventions/cache.py:8-14`

```

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
```

3. `src/conventions/ratings.py:2-8`

```

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .schemas import ConventionRule
```

---

### Container-based dependency injection

**ID:** `python.conventions.di_style`  
**Category:** dependency_injection  
**Language:** python  
**Confidence:** 68%

Uses a DI container library for dependency management. Found 4 usages.

**Statistics:**

- pattern_counts: `{'container_di': 4}`
- dominant_pattern: `container_di`
- depends_count: `0`
- common_dependency_names: `{}`

**Evidence:**

1. `src/conventions/detectors/go/__init__.py:15-25`

```
from .api import GoAPIDetector
from .patterns import GoPatternsDetector
from .modules import GoModulesDetector
from .cli import GoCLIDetector
from .migrations import GoMigrationsDetector
from .di import GoDIDetector
from .grpc import GoGRPCDetector
from .codegen import GoCodegenDetector

__all__ = [
```

2. `src/conventions/detectors/python/__init__.py:10-20`

```
from .errors import PythonErrorConventionsDetector
from .security import PythonSecurityConventionsDetector
from .async_concurrency import PythonAsyncConventionsDetector
from .architecture import PythonLayeringConventionsDetector
from .api_schema import PythonAPISchemaConventionsDetector
from .di_patterns import PythonDIConventionsDetector
from .db import PythonDBConventionsDetector
from .observability import PythonObservabilityConventionsDetector
from .resilience import PythonRetriesTimeoutsConventionsDetector
from .tooling import PythonToolingDetector
```

3. `src/conventions/detectors/generic/__init__.py:4-14`

```
from .ci_cd import CICDDetector
from .git_conventions import GitConventionsDetector
from .dependency_updates import DependencyUpdatesDetector
from .api_docs import APIDocumentationDetector
from .containerization import ContainerizationDetector
from .editor_config import EditorConfigDetector

__all__ = [
    "GenericRepoLayoutDetector",
    "CICDDetector",
```

---

### Uses unittest.mock for mocking

**ID:** `python.conventions.testing_mocking`  
**Category:** testing  
**Language:** python  
**Confidence:** 66%

Exclusively uses unittest.mock. Found 2 usages.

**Statistics:**

- mock_library_counts: `{'unittest_mock': 2}`
- primary_mock_library: `unittest_mock`

**Evidence:**

1. `tests/integration/test_cli.py:3-9`

```

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner
```

2. `tests/fixtures/python_pytest.py:1-6`

```
"""Example pytest test file."""
import pytest
from unittest.mock import Mock, patch


@pytest.fixture
```

---

### Standard repository layout

**ID:** `generic.conventions.repo_layout`  
**Category:** structure  
**Language:** generic  
**Confidence:** 60%

Repository has standard directories: src (source code), tests (tests)

**Statistics:**

- found_directories: `['src', 'tests']`

---

### Request/correlation ID propagation

**ID:** `python.conventions.correlation_ids`  
**Category:** observability  
**Language:** python  
**Confidence:** 60%

Uses request or correlation IDs for tracing. Found 2 correlation ID references.

**Statistics:**

- correlation_id_references: `2`
- uuid_generation_count: `0`

**Evidence:**

1. `src/conventions/detectors/python/logging.py:144-150`

```

        # Common fields we're looking for
        common_fields = {
            "user_id", "request_id", "trace_id", "correlation_id",
            "session_id", "order_id", "customer_id", "transaction_id",
            "action", "event", "status", "duration", "error", "exception",
            "method", "path", "url", "ip", "user_agent",
```

2. `src/conventions/detectors/python/observability.py:264-270`

```

        # Common correlation ID patterns
        correlation_patterns = [
            "request_id",
            "correlation_id",
            "trace_id",
            "x_request_id",
```

---
