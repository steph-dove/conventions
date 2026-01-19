# Conventions Review Report

*Generated: 2026-01-19 15:47:14*

## Score Legend

| Score | Rating |
|:-----:|:-------|
| 5 | Excellent |
| 4 | Good |
| 3 | Average |
| 2 | Below Average |
| 1 | Poor |

## Summary

- **Conventions Reviewed:** 18
- **Average Score:** 3.9/5 (Good)
- **Excellent (5):** 9
- **Good (4):** 2
- **Average (3):** 3
- **Below Average (2):** 4
- **Poor (1):** 0

## Scores Overview

| Convention | Score | Rating |
|:-----------|:-----:|:-------|
| CLI framework: Typer | 5/5 | Excellent |
| Google style docstrings | 5/5 | Excellent |
| High docstring coverage | 5/5 | Excellent |
| Centralized exception handling | 5/5 | Excellent |
| Linters: Ruff, mypy | 5/5 | Excellent |
| PEP 8 snake_case naming | 5/5 | Excellent |
| Centralized pytest fixtures in conftest.py | 5/5 | Excellent |
| pytest-based testing | 5/5 | Excellent |
| High type annotation coverage | 5/5 | Excellent |
| GraphQL: graphql-core | 4/5 | Good |
| Primary schema library: dataclasses | 4/5 | Good |
| Uses Express.js | 3/5 | Average |
| Import sorting: Ruff (isort rules) | 3/5 | Average |
| Uses Python standard logging | 3/5 | Average |
| Standard repository layout | 2/5 | Below Average |
| Request/correlation ID propagation | 2/5 | Below Average |
| Container-based dependency injection | 2/5 | Below Average |
| Uses unittest.mock for mocking | 2/5 | Below Average |

## Detailed Reviews

### Excellent (5/5)

#### CLI framework: Typer

**ID:** `python.conventions.cli_framework`  
**Score:** 5/5 (Excellent)

**Assessment:** CLI framework: typer

---

#### Google style docstrings

**ID:** `python.conventions.docstring_style`  
**Score:** 5/5 (Excellent)

**Assessment:** Primary docstring style is google (100% consistency)

---

#### High docstring coverage

**ID:** `python.conventions.docstrings`  
**Score:** 5/5 (Excellent)

**Assessment:** Docstring coverage is 96% of public functions

---

#### Centralized exception handling

**ID:** `python.conventions.exception_handlers`  
**Score:** 5/5 (Excellent)

**Assessment:** Exception handlers spread across 1 module(s) (3 handlers)

---

#### Linters: Ruff, mypy

**ID:** `python.conventions.linter`  
**Score:** 5/5 (Excellent)

**Assessment:** Linter: ruff

---

#### PEP 8 snake_case naming

**ID:** `python.conventions.naming`  
**Score:** 5/5 (Excellent)

**Assessment:** PEP 8 snake_case compliance is 100%

---

#### Centralized pytest fixtures in conftest.py

**ID:** `python.conventions.testing_fixtures`  
**Score:** 5/5 (Excellent)

**Assessment:** Found 24 fixtures, 1 conftest.py file(s)

---

#### pytest-based testing

**ID:** `python.conventions.testing_framework`  
**Score:** 5/5 (Excellent)

**Assessment:** Uses pytest with 18 test file(s)

---

#### High type annotation coverage

**ID:** `python.conventions.typing_coverage`  
**Score:** 5/5 (Excellent)

**Assessment:** Type annotation coverage is 99%

---

### Good (4/5)

#### GraphQL: graphql-core

**ID:** `python.conventions.graphql`  
**Score:** 4/5 (Good)

**Assessment:** GraphQL: graphql_core

**Suggestion:** Use Strawberry for type-safe GraphQL with Python.

---

#### Primary schema library: dataclasses

**ID:** `python.conventions.schema_library`  
**Score:** 4/5 (Good)

**Assessment:** Uses dataclasses for schema validation

**Suggestion:** Ensure consistent schema library usage across the codebase.

---

### Average (3/5)

#### Uses Express.js

**ID:** `node.conventions.framework`  
**Score:** 3/5 (Average)

**Assessment:** Convention detected with 73% confidence

**Suggestion:** Review this convention and consider industry best practices for improvement.

---

#### Import sorting: Ruff (isort rules)

**ID:** `python.conventions.import_sorting`  
**Score:** 3/5 (Average)

**Assessment:** Import sorting: none

**Suggestion:** Use isort or Ruff for consistent import ordering.

---

#### Uses Python standard logging

**ID:** `python.conventions.logging_library`  
**Score:** 3/5 (Average)

**Assessment:** Uses stdlib logging as primary logging library

**Suggestion:** Consider adopting structlog or Loguru for structured logging with better context propagation.

---

### Below Average (2/5)

#### Standard repository layout

**ID:** `generic.conventions.repo_layout`  
**Score:** 2/5 (Below Average)

**Assessment:** Convention detected with 60% confidence

**Suggestion:** Review this convention and consider industry best practices for improvement.

---

#### Request/correlation ID propagation

**ID:** `python.conventions.correlation_ids`  
**Score:** 2/5 (Below Average)

**Assessment:** Convention detected with 60% confidence

**Suggestion:** Review this convention and consider industry best practices for improvement.

---

#### Container-based dependency injection

**ID:** `python.conventions.di_style`  
**Score:** 2/5 (Below Average)

**Assessment:** Convention detected with 68% confidence

**Suggestion:** Review this convention and consider industry best practices for improvement.

---

#### Uses unittest.mock for mocking

**ID:** `python.conventions.testing_mocking`  
**Score:** 2/5 (Below Average)

**Assessment:** Primary mocking library is unittest_mock, using 1 library/libraries

**Suggestion:** Consider using pytest-mock for cleaner fixture-based mocking syntax.

---

## Improvement Priorities

Conventions sorted by priority (lowest scores first):

1. **Standard repository layout** (Score: 2/5)
   - Review this convention and consider industry best practices for improvement.

2. **Request/correlation ID propagation** (Score: 2/5)
   - Review this convention and consider industry best practices for improvement.

3. **Container-based dependency injection** (Score: 2/5)
   - Review this convention and consider industry best practices for improvement.

4. **Uses unittest.mock for mocking** (Score: 2/5)
   - Consider using pytest-mock for cleaner fixture-based mocking syntax.

5. **Uses Express.js** (Score: 3/5)
   - Review this convention and consider industry best practices for improvement.

6. **Import sorting: Ruff (isort rules)** (Score: 3/5)
   - Use isort or Ruff for consistent import ordering.

7. **Uses Python standard logging** (Score: 3/5)
   - Consider adopting structlog or Loguru for structured logging with better context propagation.

8. **GraphQL: graphql-core** (Score: 4/5)
   - Use Strawberry for type-safe GraphQL with Python.

9. **Primary schema library: dataclasses** (Score: 4/5)
   - Ensure consistent schema library usage across the codebase.
