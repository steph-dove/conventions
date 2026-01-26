# Conventions Review Report

*Generated: 2026-01-24 23:14:49*

## Score Legend

| Score | Rating |
|:-----:|:-------|
| 5 | Excellent |
| 4 | Good |
| 3 | Average |
| 2 | Below Average |
| 1 | Poor |

## Summary

- **Conventions Reviewed:** 61
- **Average Score:** 3.5/5 (Good)
- **Excellent (5):** 13
- **Good (4):** 16
- **Average (3):** 25
- **Below Average (2):** 3
- **Poor (1):** 4

## Scores Overview

| Convention | Score | Rating |
|:-----------|:-----:|:-------|
| Dependency updates: Dependabot | 5/5 | Excellent |
| Git hooks: pre-commit | 5/5 | Excellent |
| Async HTTP client: httpx (recommended) | 5/5 | Excellent |
| CLI framework: Typer | 5/5 | Excellent |
| Dependency management: uv | 5/5 | Excellent |
| GraphQL: Strawberry | 5/5 | Excellent |
| Linters: Ruff, mypy | 5/5 | Excellent |
| Lock file: uv.lock | 5/5 | Excellent |
| PEP 8 snake_case naming | 5/5 | Excellent |
| OpenAPI with FastAPI (customized) | 5/5 | Excellent |
| pytest-based testing | 5/5 | Excellent |
| Type checker: mypy (strict mode) | 5/5 | Excellent |
| High type annotation coverage | 5/5 | Excellent |
| CI/CD best practices | 4/5 | Good |
| Partial JSDoc coverage | 4/5 | Good |
| JavaScript codebase | 4/5 | Good |
| Primary API framework: FastAPI | 4/5 | Good |
| JWT-based authentication | 4/5 | Good |
| Caching: functools.lru_cache | 4/5 | Good |
| Context manager usage | 4/5 | Good |
| Caching decorator pattern | 4/5 | Good |
| Import sorting: Ruff (isort rules) | 4/5 | Good |
| Modern pathlib for path handling | 4/5 | Good |
| Primary schema library: Pydantic | 4/5 | Good |
| Structured configuration with Pydantic Settings | 4/5 | Good |
| Modern f-string formatting | 4/5 | Good |
| pytest fixtures for test setup | 4/5 | Good |
| Mocking with unittest.mock / Mock | 4/5 | Good |
| Parametrized tests | 4/5 | Good |
| CI/CD: GitHub Actions | 3/5 | Average |
| Standard repository layout | 3/5 | Average |
| URL-based API versioning | 3/5 | Average |
| Background jobs with FastAPI BackgroundTasks | 3/5 | Average |
| Data classes: Pydantic models | 3/5 | Average |
| lowercase constant naming | 3/5 | Average |
| Default connection pooling | 3/5 | Average |
| SQLAlchemy 2.0 select() style | 3/5 | Average |
| FastAPI-style session dependency injection | 3/5 | Average |
| Enum usage: Enum | 3/5 | Average |
| Mixed exception naming conventions | 3/5 | Average |
| Error wrapper pattern: time.sleep | 3/5 | Average |
| Absolute imports preferred | 3/5 | Average |
| JSON library: mixed | 3/5 | Average |
| Uses Python standard logging | 3/5 | Average |
| Optional type annotations | 3/5 | Average |
| Cursor-based pagination | 3/5 | Average |
| Response envelope classes | 3/5 | Average |
| Test naming: Simple style (test_feature) | 3/5 | Average |
| Distributed test files | 3/5 | Average |
| Pydantic validation | 3/5 | Average |
| Snippet-style examples | 3/5 | Average |
| Examples with main() entry point | 3/5 | Average |
| Tutorial-style documentation | 3/5 | Average |
| Plain assert statements | 3/5 | Average |
| Standard repository files | 2/5 | Below Average |
| Implicit transaction management | 2/5 | Below Average |
| Health check functions | 2/5 | Below Average |
| Low docstring coverage | 1/5 | Poor |
| HTTP errors raised in service layer | 1/5 | Poor |
| Distributed exception handling | 1/5 | Poor |
| Infrequent timeout specification | 1/5 | Poor |

## Detailed Reviews

### Excellent (5/5)

#### Dependency updates: Dependabot

**ID:** `generic.conventions.dependency_updates`  
**Score:** 5/5 (Excellent)

**Assessment:** Dependency updates: dependabot

---

#### Git hooks: pre-commit

**ID:** `generic.conventions.git_hooks`  
**Score:** 5/5 (Excellent)

**Assessment:** Git hooks: pre-commit

---

#### Async HTTP client: httpx (recommended)

**ID:** `python.conventions.async_http_client`  
**Score:** 5/5 (Excellent)

**Assessment:** Uses httpx for HTTP requests

---

#### CLI framework: Typer

**ID:** `python.conventions.cli_framework`  
**Score:** 5/5 (Excellent)

**Assessment:** CLI framework: typer

---

#### Dependency management: uv

**ID:** `python.conventions.dependency_management`  
**Score:** 5/5 (Excellent)

**Assessment:** Dependencies: uv

---

#### GraphQL: Strawberry

**ID:** `python.conventions.graphql`  
**Score:** 5/5 (Excellent)

**Assessment:** GraphQL: strawberry

---

#### Linters: Ruff, mypy

**ID:** `python.conventions.linter`  
**Score:** 5/5 (Excellent)

**Assessment:** Linters: Ruff, mypy

---

#### Lock file: uv.lock

**ID:** `python.conventions.lock_file`  
**Score:** 5/5 (Excellent)

**Assessment:** Lock file: uv.lock

---

#### PEP 8 snake_case naming

**ID:** `python.conventions.naming`  
**Score:** 5/5 (Excellent)

**Assessment:** PEP 8 snake_case compliance is 100%

---

#### OpenAPI with FastAPI (customized)

**ID:** `python.conventions.openapi_docs`  
**Score:** 5/5 (Excellent)

**Assessment:** OpenAPI docs via FastAPI (customized)

---

#### pytest-based testing

**ID:** `python.conventions.testing_framework`  
**Score:** 5/5 (Excellent)

**Assessment:** Uses pytest with 465 test file(s)

---

#### Type checker: mypy (strict mode)

**ID:** `python.conventions.type_checker_strictness`  
**Score:** 5/5 (Excellent)

**Assessment:** mypy in strict mode

---

#### High type annotation coverage

**ID:** `python.conventions.typing_coverage`  
**Score:** 5/5 (Excellent)

**Assessment:** Type annotation coverage is 99%

---

### Good (4/5)

#### CI/CD best practices

**ID:** `generic.conventions.ci_quality`  
**Score:** 4/5 (Good)

**Assessment:** Convention detected with 90% confidence

---

#### Partial JSDoc coverage

**ID:** `node.conventions.jsdoc`  
**Score:** 4/5 (Good)

**Assessment:** JSDoc coverage: 12 blocks, 18 @param tags

**Suggestion:** Add JSDoc comments with @param and @returns for better documentation.

---

#### JavaScript codebase

**ID:** `node.conventions.typescript`  
**Score:** 4/5 (Good)

**Assessment:** Convention detected with 90% confidence

---

#### Primary API framework: FastAPI

**ID:** `python.conventions.api_framework`  
**Score:** 4/5 (Good)

**Assessment:** Uses FastAPI as primary API framework

**Suggestion:** Consolidate API frameworks to a single choice for consistency.

---

#### JWT-based authentication

**ID:** `python.conventions.auth_pattern`  
**Score:** 4/5 (Good)

**Assessment:** Authentication uses JWT, OAuth2, dependency injection

**Suggestion:** Use a dedicated password hashing library (passlib or bcrypt) for secure credential storage.

---

#### Caching: functools.lru_cache

**ID:** `python.conventions.caching`  
**Score:** 4/5 (Good)

**Assessment:** Caching with functools.lru_cache

**Suggestion:** Consider Redis for distributed caching in production environments.

---

#### Context manager usage

**ID:** `python.conventions.context_managers`  
**Score:** 4/5 (Good)

**Assessment:** Convention detected with 90% confidence

---

#### Caching decorator pattern

**ID:** `python.conventions.decorator_caching`  
**Score:** 4/5 (Good)

**Assessment:** Convention detected with 90% confidence

---

#### Import sorting: Ruff (isort rules)

**ID:** `python.conventions.import_sorting`  
**Score:** 4/5 (Good)

**Assessment:** Convention detected with 90% confidence

---

#### Modern pathlib for path handling

**ID:** `python.conventions.path_handling`  
**Score:** 4/5 (Good)

**Assessment:** Convention detected with 95% confidence

---

#### Primary schema library: Pydantic

**ID:** `python.conventions.schema_library`  
**Score:** 4/5 (Good)

**Assessment:** Uses Pydantic for schema validation

**Suggestion:** Ensure consistent schema library usage across the codebase.

---

#### Structured configuration with Pydantic Settings

**ID:** `python.conventions.secrets_access_style`  
**Score:** 4/5 (Good)

**Assessment:** Uses Pydantic Settings for configuration (os.environ: 1 direct accesses)

**Suggestion:** Replace remaining os.environ accesses with Settings class properties.

---

#### Modern f-string formatting

**ID:** `python.conventions.string_formatting`  
**Score:** 4/5 (Good)

**Assessment:** Convention detected with 95% confidence

---

#### pytest fixtures for test setup

**ID:** `python.test_conventions.fixtures`  
**Score:** 4/5 (Good)

**Assessment:** Convention detected with 90% confidence

---

#### Mocking with unittest.mock / Mock

**ID:** `python.test_conventions.mocking`  
**Score:** 4/5 (Good)

**Assessment:** Convention detected with 90% confidence

---

#### Parametrized tests

**ID:** `python.test_conventions.parametrized`  
**Score:** 4/5 (Good)

**Assessment:** Convention detected with 90% confidence

---

### Average (3/5)

#### CI/CD: GitHub Actions

**ID:** `generic.conventions.ci_platform`  
**Score:** 3/5 (Average)

**Assessment:** Convention detected with 80% confidence

**Suggestion:** Add automated testing, linting, and deployment steps to your CI/CD pipeline.

---

#### Standard repository layout

**ID:** `generic.conventions.repo_layout`  
**Score:** 3/5 (Average)

**Assessment:** Convention detected with 70% confidence

**Suggestion:** Review this convention and consider industry best practices for improvement.

---

#### URL-based API versioning

**ID:** `python.conventions.api_versioning`  
**Score:** 3/5 (Average)

**Assessment:** URL-based API versioning (2 versioned routes)

**Suggestion:** Apply consistent versioning across all API routes.

---

#### Background jobs with FastAPI BackgroundTasks

**ID:** `python.conventions.background_jobs`  
**Score:** 3/5 (Average)

**Assessment:** Convention detected with 72% confidence

**Suggestion:** Use appropriate synchronization primitives and handle async errors properly.

---

#### Data classes: Pydantic models

**ID:** `python.conventions.class_style`  
**Score:** 3/5 (Average)

**Assessment:** Convention detected with 86% confidence

**Suggestion:** Review this convention and consider industry best practices for improvement.

---

#### lowercase constant naming

**ID:** `python.conventions.constant_naming`  
**Score:** 3/5 (Average)

**Assessment:** Convention detected with 70% confidence

**Suggestion:** Review this convention and consider industry best practices for improvement.

---

#### Default connection pooling

**ID:** `python.conventions.db_connection_pooling`  
**Score:** 3/5 (Average)

**Assessment:** Uses default connection pooling

**Suggestion:** Configure pool_size, max_overflow, and pool_pre_ping for production reliability.

---

#### SQLAlchemy 2.0 select() style

**ID:** `python.conventions.db_query_style`  
**Score:** 3/5 (Average)

**Assessment:** Convention detected with 90% confidence

**Suggestion:** Review this convention and consider industry best practices for improvement.

---

#### FastAPI-style session dependency injection

**ID:** `python.conventions.db_session_lifecycle`  
**Score:** 3/5 (Average)

**Assessment:** Convention detected with 85% confidence

**Suggestion:** Review this convention and consider industry best practices for improvement.

---

#### Enum usage: Enum

**ID:** `python.conventions.enum_usage`  
**Score:** 3/5 (Average)

**Assessment:** Convention detected with 80% confidence

**Suggestion:** Review this convention and consider industry best practices for improvement.

---

#### Mixed exception naming conventions

**ID:** `python.conventions.error_taxonomy`  
**Score:** 3/5 (Average)

**Assessment:** Exception naming is 77% consistent across 22 custom exceptions

**Suggestion:** Standardize exception naming to use *Error suffix consistently.

---

#### Error wrapper pattern: time.sleep

**ID:** `python.conventions.error_wrapper`  
**Score:** 3/5 (Average)

**Assessment:** Error wrapper 'time.sleep' used in 6/28 handlers (21%)

**Suggestion:** Consider using 'time.sleep' more consistently across all exception handlers.

---

#### Absolute imports preferred

**ID:** `python.conventions.import_style`  
**Score:** 3/5 (Average)

**Assessment:** Convention detected with 70% confidence

**Suggestion:** Review this convention and consider industry best practices for improvement.

---

#### JSON library: mixed

**ID:** `python.conventions.json_library`  
**Score:** 3/5 (Average)

**Assessment:** Uses stdlib json (41 usages)

**Suggestion:** Consider orjson for 10x faster JSON serialization with minimal API changes.

---

#### Uses Python standard logging

**ID:** `python.conventions.logging_library`  
**Score:** 3/5 (Average)

**Assessment:** Uses stdlib logging as primary logging library

**Suggestion:** Consider adopting structlog or Loguru for structured logging with better context propagation.

---

#### Optional type annotations

**ID:** `python.conventions.optional_usage`  
**Score:** 3/5 (Average)

**Assessment:** Convention detected with 80% confidence

**Suggestion:** Add type annotations to function parameters and return types. Start with public APIs.

---

#### Cursor-based pagination

**ID:** `python.conventions.pagination_pattern`  
**Score:** 3/5 (Average)

**Assessment:** Convention detected with 80% confidence

**Suggestion:** Review this convention and consider industry best practices for improvement.

---

#### Response envelope classes

**ID:** `python.conventions.response_envelope`  
**Score:** 3/5 (Average)

**Assessment:** Convention detected with 70% confidence

**Suggestion:** Review this convention and consider industry best practices for improvement.

---

#### Test naming: Simple style (test_feature)

**ID:** `python.conventions.test_naming`  
**Score:** 3/5 (Average)

**Assessment:** Convention detected with 84% confidence

**Suggestion:** Add more test cases and increase coverage of edge cases and error paths.

---

#### Distributed test files

**ID:** `python.conventions.test_structure`  
**Score:** 3/5 (Average)

**Assessment:** Convention detected with 70% confidence

**Suggestion:** Add more test cases and increase coverage of edge cases and error paths.

---

#### Pydantic validation

**ID:** `python.conventions.validation_style`  
**Score:** 3/5 (Average)

**Assessment:** Convention detected with 78% confidence

**Suggestion:** Review this convention and consider industry best practices for improvement.

---

#### Snippet-style examples

**ID:** `python.docs_conventions.example_completeness`  
**Score:** 3/5 (Average)

**Assessment:** Convention detected with 70% confidence

**Suggestion:** Add docstrings to public functions and classes explaining purpose and parameters.

---

#### Examples with main() entry point

**ID:** `python.docs_conventions.example_structure`  
**Score:** 3/5 (Average)

**Assessment:** Convention detected with 80% confidence

**Suggestion:** Add docstrings to public functions and classes explaining purpose and parameters.

---

#### Tutorial-style documentation

**ID:** `python.docs_conventions.organization`  
**Score:** 3/5 (Average)

**Assessment:** Convention detected with 80% confidence

**Suggestion:** Add docstrings to public functions and classes explaining purpose and parameters.

---

#### Plain assert statements

**ID:** `python.test_conventions.assertions`  
**Score:** 3/5 (Average)

**Assessment:** Convention detected with 89% confidence

**Suggestion:** Add more test cases and increase coverage of edge cases and error paths.

---

### Below Average (2/5)

#### Standard repository files

**ID:** `generic.conventions.standard_files`  
**Score:** 2/5 (Below Average)

**Assessment:** Convention detected with 65% confidence

**Suggestion:** Review this convention and consider industry best practices for improvement.

---

#### Implicit transaction management

**ID:** `python.conventions.db_transactions`  
**Score:** 2/5 (Below Average)

**Assessment:** Convention detected with 60% confidence

**Suggestion:** Review this convention and consider industry best practices for improvement.

---

#### Health check functions

**ID:** `python.conventions.health_checks`  
**Score:** 2/5 (Below Average)

**Assessment:** Health checks: liveness

**Suggestion:** Add a /ready endpoint to signal when the service is ready to accept traffic.

---

### Poor (1/5)

#### Low docstring coverage

**ID:** `python.conventions.docstrings`  
**Score:** 1/5 (Poor)

**Assessment:** Docstring coverage is 20% of public functions

**Suggestion:** Add docstrings to public functions and classes. Focus on explaining the 'why' and documenting parameters/return values.

---

#### HTTP errors raised in service layer

**ID:** `python.conventions.error_handling_boundary`  
**Score:** 1/5 (Poor)

**Assessment:** HTTPException raised in API layer 0% of the time

**Suggestion:** Ensure HTTP errors are raised only at the API boundary layer.

---

#### Distributed exception handling

**ID:** `python.conventions.exception_handlers`  
**Score:** 1/5 (Poor)

**Assessment:** Exception handlers spread across 6 module(s) (31 handlers)

**Suggestion:** Consolidate exception handlers into a single module (currently in 6 files).

---

#### Infrequent timeout specification

**ID:** `python.conventions.timeouts`  
**Score:** 1/5 (Poor)

**Assessment:** Timeout coverage is 2% (4 with, 207 without)

**Suggestion:** Add explicit timeouts to HTTP client calls. Found 207 calls without timeouts.

---

## Improvement Priorities

Conventions sorted by priority (lowest scores first):

1. **Low docstring coverage** (Score: 1/5)
   - Add docstrings to public functions and classes. Focus on explaining the 'why' and documenting parameters/return values.

2. **HTTP errors raised in service layer** (Score: 1/5)
   - Ensure HTTP errors are raised only at the API boundary layer.

3. **Distributed exception handling** (Score: 1/5)
   - Consolidate exception handlers into a single module (currently in 6 files).

4. **Infrequent timeout specification** (Score: 1/5)
   - Add explicit timeouts to HTTP client calls. Found 207 calls without timeouts.

5. **Standard repository files** (Score: 2/5)
   - Review this convention and consider industry best practices for improvement.

6. **Implicit transaction management** (Score: 2/5)
   - Review this convention and consider industry best practices for improvement.

7. **Health check functions** (Score: 2/5)
   - Add a /ready endpoint to signal when the service is ready to accept traffic.

8. **CI/CD: GitHub Actions** (Score: 3/5)
   - Add automated testing, linting, and deployment steps to your CI/CD pipeline.

9. **Standard repository layout** (Score: 3/5)
   - Review this convention and consider industry best practices for improvement.

10. **URL-based API versioning** (Score: 3/5)
   - Apply consistent versioning across all API routes.

11. **Background jobs with FastAPI BackgroundTasks** (Score: 3/5)
   - Use appropriate synchronization primitives and handle async errors properly.

12. **Data classes: Pydantic models** (Score: 3/5)
   - Review this convention and consider industry best practices for improvement.

13. **lowercase constant naming** (Score: 3/5)
   - Review this convention and consider industry best practices for improvement.

14. **Default connection pooling** (Score: 3/5)
   - Configure pool_size, max_overflow, and pool_pre_ping for production reliability.

15. **SQLAlchemy 2.0 select() style** (Score: 3/5)
   - Review this convention and consider industry best practices for improvement.

16. **FastAPI-style session dependency injection** (Score: 3/5)
   - Review this convention and consider industry best practices for improvement.

17. **Enum usage: Enum** (Score: 3/5)
   - Review this convention and consider industry best practices for improvement.

18. **Mixed exception naming conventions** (Score: 3/5)
   - Standardize exception naming to use *Error suffix consistently.

19. **Error wrapper pattern: time.sleep** (Score: 3/5)
   - Consider using 'time.sleep' more consistently across all exception handlers.

20. **Absolute imports preferred** (Score: 3/5)
   - Review this convention and consider industry best practices for improvement.

21. **JSON library: mixed** (Score: 3/5)
   - Consider orjson for 10x faster JSON serialization with minimal API changes.

22. **Uses Python standard logging** (Score: 3/5)
   - Consider adopting structlog or Loguru for structured logging with better context propagation.

23. **Optional type annotations** (Score: 3/5)
   - Add type annotations to function parameters and return types. Start with public APIs.

24. **Cursor-based pagination** (Score: 3/5)
   - Review this convention and consider industry best practices for improvement.

25. **Response envelope classes** (Score: 3/5)
   - Review this convention and consider industry best practices for improvement.

26. **Test naming: Simple style (test_feature)** (Score: 3/5)
   - Add more test cases and increase coverage of edge cases and error paths.

27. **Distributed test files** (Score: 3/5)
   - Add more test cases and increase coverage of edge cases and error paths.

28. **Pydantic validation** (Score: 3/5)
   - Review this convention and consider industry best practices for improvement.

29. **Snippet-style examples** (Score: 3/5)
   - Add docstrings to public functions and classes explaining purpose and parameters.

30. **Examples with main() entry point** (Score: 3/5)
   - Add docstrings to public functions and classes explaining purpose and parameters.

31. **Tutorial-style documentation** (Score: 3/5)
   - Add docstrings to public functions and classes explaining purpose and parameters.

32. **Plain assert statements** (Score: 3/5)
   - Add more test cases and increase coverage of edge cases and error paths.

33. **Partial JSDoc coverage** (Score: 4/5)
   - Add JSDoc comments with @param and @returns for better documentation.

34. **Primary API framework: FastAPI** (Score: 4/5)
   - Consolidate API frameworks to a single choice for consistency.

35. **JWT-based authentication** (Score: 4/5)
   - Use a dedicated password hashing library (passlib or bcrypt) for secure credential storage.

36. **Caching: functools.lru_cache** (Score: 4/5)
   - Consider Redis for distributed caching in production environments.

37. **Primary schema library: Pydantic** (Score: 4/5)
   - Ensure consistent schema library usage across the codebase.

38. **Structured configuration with Pydantic Settings** (Score: 4/5)
   - Replace remaining os.environ accesses with Settings class properties.
