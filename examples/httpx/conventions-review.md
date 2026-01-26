# Conventions Review Report

*Generated: 2026-01-24 23:15:11*

## Score Legend

| Score | Rating |
|:-----:|:-------|
| 5 | Excellent |
| 4 | Good |
| 3 | Average |
| 2 | Below Average |
| 1 | Poor |

## Summary

- **Conventions Reviewed:** 40
- **Average Score:** 3.3/5 (Average)
- **Excellent (5):** 8
- **Good (4):** 5
- **Average (3):** 20
- **Below Average (2):** 5
- **Poor (1):** 2

## Scores Overview

| Convention | Score | Rating |
|:-----------|:-----:|:-------|
| Dependency updates: Dependabot | 5/5 | Excellent |
| Async HTTP client: httpx (recommended) | 5/5 | Excellent |
| CLI framework: Click | 5/5 | Excellent |
| Linters: Ruff, mypy | 5/5 | Excellent |
| PEP 8 snake_case naming | 5/5 | Excellent |
| pytest-based testing | 5/5 | Excellent |
| Type checker: mypy (strict mode) | 5/5 | Excellent |
| High type annotation coverage | 5/5 | Excellent |
| Context manager usage | 4/5 | Good |
| Dependency management: pip (requirements.txt) | 4/5 | Good |
| Import sorting: Ruff (isort rules) | 4/5 | Good |
| Modern f-string formatting | 4/5 | Good |
| Parametrized tests | 4/5 | Good |
| CI/CD: GitHub Actions | 3/5 | Average |
| CI/CD best practices | 3/5 | Average |
| Standard repository layout | 3/5 | Average |
| Data classes: NamedTuple | 3/5 | Average |
| lowercase constant naming | 3/5 | Average |
| HTTP clients with context managers | 3/5 | Average |
| Custom decorator pattern: @click.option | 3/5 | Average |
| Mixed docstring styles | 3/5 | Average |
| Enum usage: Enum | 3/5 | Average |
| Absolute imports preferred | 3/5 | Average |
| JSON library: stdlib json | 3/5 | Average |
| Lock file: requirements.txt (pinned) | 3/5 | Average |
| Uses Python standard logging | 3/5 | Average |
| Mixed path handling (pathlib and os.path) | 3/5 | Average |
| Configuration via os.environ direct access | 3/5 | Average |
| Test naming: Simple style (test_feature) | 3/5 | Average |
| Single test directory: tests/ | 3/5 | Average |
| Manual validation (ValueError/TypeError) | 3/5 | Average |
| Plain assert statements | 3/5 | Average |
| pytest fixtures for test setup | 3/5 | Average |
| Standard repository files | 2/5 | Below Average |
| Partial docstring coverage | 2/5 | Below Average |
| Mixed exception naming conventions | 2/5 | Below Average |
| Error wrapper pattern: str | 2/5 | Below Average |
| Mocking with pytest monkeypatch fixture | 2/5 | Below Average |
| Password hashing: hashlib (not recommended) | 1/5 | Poor |
| Infrequent timeout specification | 1/5 | Poor |

## Detailed Reviews

### Excellent (5/5)

#### Dependency updates: Dependabot

**ID:** `generic.conventions.dependency_updates`  
**Score:** 5/5 (Excellent)

**Assessment:** Dependency updates: dependabot

---

#### Async HTTP client: httpx (recommended)

**ID:** `python.conventions.async_http_client`  
**Score:** 5/5 (Excellent)

**Assessment:** Uses httpx for HTTP requests

---

#### CLI framework: Click

**ID:** `python.conventions.cli_framework`  
**Score:** 5/5 (Excellent)

**Assessment:** CLI framework: click

---

#### Linters: Ruff, mypy

**ID:** `python.conventions.linter`  
**Score:** 5/5 (Excellent)

**Assessment:** Linters: Ruff, mypy

---

#### PEP 8 snake_case naming

**ID:** `python.conventions.naming`  
**Score:** 5/5 (Excellent)

**Assessment:** PEP 8 snake_case compliance is 100%

---

#### pytest-based testing

**ID:** `python.conventions.testing_framework`  
**Score:** 5/5 (Excellent)

**Assessment:** Uses pytest with 32 test file(s)

---

#### Type checker: mypy (strict mode)

**ID:** `python.conventions.type_checker_strictness`  
**Score:** 5/5 (Excellent)

**Assessment:** mypy in strict mode

---

#### High type annotation coverage

**ID:** `python.conventions.typing_coverage`  
**Score:** 5/5 (Excellent)

**Assessment:** Type annotation coverage is 100%

---

### Good (4/5)

#### Context manager usage

**ID:** `python.conventions.context_managers`  
**Score:** 4/5 (Good)

**Assessment:** Convention detected with 90% confidence

---

#### Dependency management: pip (requirements.txt)

**ID:** `python.conventions.dependency_management`  
**Score:** 4/5 (Good)

**Assessment:** Dependencies: pip

**Suggestion:** Consider Poetry, uv, or PDM for modern dependency management.

---

#### Import sorting: Ruff (isort rules)

**ID:** `python.conventions.import_sorting`  
**Score:** 4/5 (Good)

**Assessment:** Convention detected with 90% confidence

---

#### Modern f-string formatting

**ID:** `python.conventions.string_formatting`  
**Score:** 4/5 (Good)

**Assessment:** Convention detected with 94% confidence

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

#### CI/CD best practices

**ID:** `generic.conventions.ci_quality`  
**Score:** 3/5 (Average)

**Assessment:** Convention detected with 70% confidence

**Suggestion:** Add automated testing, linting, and deployment steps to your CI/CD pipeline.

---

#### Standard repository layout

**ID:** `generic.conventions.repo_layout`  
**Score:** 3/5 (Average)

**Assessment:** Convention detected with 70% confidence

**Suggestion:** Review this convention and consider industry best practices for improvement.

---

#### Data classes: NamedTuple

**ID:** `python.conventions.class_style`  
**Score:** 3/5 (Average)

**Assessment:** Convention detected with 90% confidence

**Suggestion:** Review this convention and consider industry best practices for improvement.

---

#### lowercase constant naming

**ID:** `python.conventions.constant_naming`  
**Score:** 3/5 (Average)

**Assessment:** Convention detected with 70% confidence

**Suggestion:** Review this convention and consider industry best practices for improvement.

---

#### HTTP clients with context managers

**ID:** `python.conventions.context_http_client`  
**Score:** 3/5 (Average)

**Assessment:** Convention detected with 75% confidence

**Suggestion:** Review this convention and consider industry best practices for improvement.

---

#### Custom decorator pattern: @click.option

**ID:** `python.conventions.custom_decorators`  
**Score:** 3/5 (Average)

**Assessment:** Convention detected with 85% confidence

**Suggestion:** Review this convention and consider industry best practices for improvement.

---

#### Mixed docstring styles

**ID:** `python.conventions.docstring_style`  
**Score:** 3/5 (Average)

**Assessment:** Primary docstring style is google (67% consistency)

**Suggestion:** Standardize remaining docstrings to follow the primary style consistently.

---

#### Enum usage: Enum

**ID:** `python.conventions.enum_usage`  
**Score:** 3/5 (Average)

**Assessment:** Convention detected with 70% confidence

**Suggestion:** Review this convention and consider industry best practices for improvement.

---

#### Absolute imports preferred

**ID:** `python.conventions.import_style`  
**Score:** 3/5 (Average)

**Assessment:** Convention detected with 70% confidence

**Suggestion:** Review this convention and consider industry best practices for improvement.

---

#### JSON library: stdlib json

**ID:** `python.conventions.json_library`  
**Score:** 3/5 (Average)

**Assessment:** Uses stdlib json (21 usages)

**Suggestion:** Consider orjson for 10x faster JSON serialization with minimal API changes.

---

#### Lock file: requirements.txt (pinned)

**ID:** `python.conventions.lock_file`  
**Score:** 3/5 (Average)

**Assessment:** Lock file: requirements.txt (pinned)

**Suggestion:** Consider uv or poetry for better dependency resolution and lock file management.

---

#### Uses Python standard logging

**ID:** `python.conventions.logging_library`  
**Score:** 3/5 (Average)

**Assessment:** Uses stdlib logging as primary logging library

**Suggestion:** Consider adopting structlog or Loguru for structured logging with better context propagation.

---

#### Mixed path handling (pathlib and os.path)

**ID:** `python.conventions.path_handling`  
**Score:** 3/5 (Average)

**Assessment:** Convention detected with 70% confidence

**Suggestion:** Review this convention and consider industry best practices for improvement.

---

#### Configuration via os.environ direct access

**ID:** `python.conventions.secrets_access_style`  
**Score:** 3/5 (Average)

**Assessment:** Uses os.environ for configuration (2 direct accesses)

**Suggestion:** Adopt Pydantic BaseSettings for type-safe configuration with validation and environment variable parsing.

---

#### Test naming: Simple style (test_feature)

**ID:** `python.conventions.test_naming`  
**Score:** 3/5 (Average)

**Assessment:** Convention detected with 84% confidence

**Suggestion:** Add more test cases and increase coverage of edge cases and error paths.

---

#### Single test directory: tests/

**ID:** `python.conventions.test_structure`  
**Score:** 3/5 (Average)

**Assessment:** Convention detected with 80% confidence

**Suggestion:** Add more test cases and increase coverage of edge cases and error paths.

---

#### Manual validation (ValueError/TypeError)

**ID:** `python.conventions.validation_style`  
**Score:** 3/5 (Average)

**Assessment:** Convention detected with 90% confidence

**Suggestion:** Review this convention and consider industry best practices for improvement.

---

#### Plain assert statements

**ID:** `python.test_conventions.assertions`  
**Score:** 3/5 (Average)

**Assessment:** Convention detected with 86% confidence

**Suggestion:** Add more test cases and increase coverage of edge cases and error paths.

---

#### pytest fixtures for test setup

**ID:** `python.test_conventions.fixtures`  
**Score:** 3/5 (Average)

**Assessment:** Convention detected with 85% confidence

**Suggestion:** Add more test cases and increase coverage of edge cases and error paths.

---

### Below Average (2/5)

#### Standard repository files

**ID:** `generic.conventions.standard_files`  
**Score:** 2/5 (Below Average)

**Assessment:** Convention detected with 60% confidence

**Suggestion:** Review this convention and consider industry best practices for improvement.

---

#### Partial docstring coverage

**ID:** `python.conventions.docstrings`  
**Score:** 2/5 (Below Average)

**Assessment:** Docstring coverage is 34% of public functions

**Suggestion:** Add docstrings to public functions and classes. Focus on explaining the 'why' and documenting parameters/return values.

---

#### Mixed exception naming conventions

**ID:** `python.conventions.error_taxonomy`  
**Score:** 2/5 (Below Average)

**Assessment:** Exception naming is 54% consistent across 28 custom exceptions

**Suggestion:** Standardize exception naming to use *Error suffix consistently.

---

#### Error wrapper pattern: str

**ID:** `python.conventions.error_wrapper`  
**Score:** 2/5 (Below Average)

**Assessment:** Error wrapper 'str' used in 8/55 handlers (14%)

**Suggestion:** Consider using 'str' more consistently across all exception handlers.

---

#### Mocking with pytest monkeypatch fixture

**ID:** `python.test_conventions.mocking`  
**Score:** 2/5 (Below Average)

**Assessment:** Convention detected with 65% confidence

**Suggestion:** Add more test cases and increase coverage of edge cases and error paths.

---

### Poor (1/5)

#### Password hashing: hashlib (not recommended)

**ID:** `python.conventions.password_hashing`  
**Score:** 1/5 (Poor)

**Assessment:** Uses hashlib for password hashing

**Suggestion:** CRITICAL: hashlib is not suitable for passwords. Use argon2-cffi or bcrypt immediately.

---

#### Infrequent timeout specification

**ID:** `python.conventions.timeouts`  
**Score:** 1/5 (Poor)

**Assessment:** Timeout coverage is 10% (52 with, 445 without)

**Suggestion:** Add explicit timeouts to HTTP client calls. Found 445 calls without timeouts.

---

## Improvement Priorities

Conventions sorted by priority (lowest scores first):

1. **Password hashing: hashlib (not recommended)** (Score: 1/5)
   - CRITICAL: hashlib is not suitable for passwords. Use argon2-cffi or bcrypt immediately.

2. **Infrequent timeout specification** (Score: 1/5)
   - Add explicit timeouts to HTTP client calls. Found 445 calls without timeouts.

3. **Standard repository files** (Score: 2/5)
   - Review this convention and consider industry best practices for improvement.

4. **Partial docstring coverage** (Score: 2/5)
   - Add docstrings to public functions and classes. Focus on explaining the 'why' and documenting parameters/return values.

5. **Mixed exception naming conventions** (Score: 2/5)
   - Standardize exception naming to use *Error suffix consistently.

6. **Error wrapper pattern: str** (Score: 2/5)
   - Consider using 'str' more consistently across all exception handlers.

7. **Mocking with pytest monkeypatch fixture** (Score: 2/5)
   - Add more test cases and increase coverage of edge cases and error paths.

8. **CI/CD: GitHub Actions** (Score: 3/5)
   - Add automated testing, linting, and deployment steps to your CI/CD pipeline.

9. **CI/CD best practices** (Score: 3/5)
   - Add automated testing, linting, and deployment steps to your CI/CD pipeline.

10. **Standard repository layout** (Score: 3/5)
   - Review this convention and consider industry best practices for improvement.

11. **Data classes: NamedTuple** (Score: 3/5)
   - Review this convention and consider industry best practices for improvement.

12. **lowercase constant naming** (Score: 3/5)
   - Review this convention and consider industry best practices for improvement.

13. **HTTP clients with context managers** (Score: 3/5)
   - Review this convention and consider industry best practices for improvement.

14. **Custom decorator pattern: @click.option** (Score: 3/5)
   - Review this convention and consider industry best practices for improvement.

15. **Mixed docstring styles** (Score: 3/5)
   - Standardize remaining docstrings to follow the primary style consistently.

16. **Enum usage: Enum** (Score: 3/5)
   - Review this convention and consider industry best practices for improvement.

17. **Absolute imports preferred** (Score: 3/5)
   - Review this convention and consider industry best practices for improvement.

18. **JSON library: stdlib json** (Score: 3/5)
   - Consider orjson for 10x faster JSON serialization with minimal API changes.

19. **Lock file: requirements.txt (pinned)** (Score: 3/5)
   - Consider uv or poetry for better dependency resolution and lock file management.

20. **Uses Python standard logging** (Score: 3/5)
   - Consider adopting structlog or Loguru for structured logging with better context propagation.

21. **Mixed path handling (pathlib and os.path)** (Score: 3/5)
   - Review this convention and consider industry best practices for improvement.

22. **Configuration via os.environ direct access** (Score: 3/5)
   - Adopt Pydantic BaseSettings for type-safe configuration with validation and environment variable parsing.

23. **Test naming: Simple style (test_feature)** (Score: 3/5)
   - Add more test cases and increase coverage of edge cases and error paths.

24. **Single test directory: tests/** (Score: 3/5)
   - Add more test cases and increase coverage of edge cases and error paths.

25. **Manual validation (ValueError/TypeError)** (Score: 3/5)
   - Review this convention and consider industry best practices for improvement.

26. **Plain assert statements** (Score: 3/5)
   - Add more test cases and increase coverage of edge cases and error paths.

27. **pytest fixtures for test setup** (Score: 3/5)
   - Add more test cases and increase coverage of edge cases and error paths.

28. **Dependency management: pip (requirements.txt)** (Score: 4/5)
   - Consider Poetry, uv, or PDM for modern dependency management.
