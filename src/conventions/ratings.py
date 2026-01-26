"""Rating rules and criteria for convention evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .schemas import ConventionRule


@dataclass
class RatingRule:
    """Rule for rating a convention."""

    score_func: Callable[[ConventionRule], int]  # Returns 1-5
    reason_func: Callable[[ConventionRule, int], str]  # Returns reason for score
    suggestion_func: Callable[[ConventionRule, int], str | None]  # Returns suggestion or None


# Category-specific suggestions for better actionable feedback
CATEGORY_SUGGESTIONS: dict[str, str] = {
    "typing": "Add type annotations to function parameters and return types. Start with public APIs.",
    "testing": "Add more test cases and increase coverage of edge cases and error paths.",
    "documentation": "Add docstrings to public functions and classes explaining purpose and parameters.",
    "logging": "Use structured logging with consistent field names for better observability.",
    "error_handling": "Define custom exception types for domain-specific errors and handle them at appropriate layers.",
    "security": "Review for OWASP top 10 vulnerabilities and ensure input validation at boundaries.",
    "architecture": "Ensure clear separation between layers (API, service, data) with appropriate dependency direction.",
    "ci_cd": "Add automated testing, linting, and deployment steps to your CI/CD pipeline.",
    "tooling": "Configure development tools (formatters, linters) for consistent code quality.",
    "concurrency": "Use appropriate synchronization primitives and handle async errors properly.",
    "patterns": "Apply consistent design patterns across the codebase for maintainability.",
}


def _get_stat(rule: ConventionRule, key: str, default: float = 0.0) -> float:
    """Safely get a stat value from a rule."""
    return float(rule.stats.get(key, default))


def _make_actionable_suggestion(rule: ConventionRule, base_suggestion: str) -> str:
    """Enhance suggestion with stats-based actionable details."""
    stats = rule.stats

    # Add specific numbers when available
    if "untyped_functions" in stats:
        count = stats["untyped_functions"]
        coverage = stats.get("any_annotation_coverage", 0) * 100
        return f"Add type hints to the {count} untyped functions (currently {coverage:.0f}% coverage)."

    if "missing_docstrings" in stats:
        count = stats["missing_docstrings"]
        return f"Add docstrings to {count} public functions/classes missing documentation."

    if "test_file_count" in stats and stats["test_file_count"] < 3:
        return f"Add more test files (currently {stats['test_file_count']}). Aim for comprehensive coverage."

    if "raw_sql_count" in stats:
        count = stats["raw_sql_count"]
        return f"Replace {count} raw SQL execution(s) with parameterized queries or ORM methods."

    if "fixture_count" in stats and stats.get("conftest_count", 0) == 0:
        return f"Create a conftest.py to centralize the {stats['fixture_count']} fixtures across test files."

    if "api_to_db" in stats and stats["api_to_db"] > 0:
        return f"Remove {stats['api_to_db']} direct API-to-DB import(s). Route through the service layer."

    if "violations_by_type" in stats:
        violations = stats["violations_by_type"]
        if violations:
            details = ", ".join(f"{k}: {v}" for k, v in violations.items())
            return f"Fix layer boundary violations: {details}."

    return base_suggestion


# Python typing coverage rating
def _typing_score(r: ConventionRule) -> int:
    coverage = _get_stat(r, "any_annotation_coverage", 0)
    if coverage >= 0.9:
        return 5
    if coverage >= 0.7:
        return 4
    if coverage >= 0.5:
        return 3
    if coverage >= 0.3:
        return 2
    return 1


def _typing_reason(r: ConventionRule, _score: int) -> str:
    coverage = _get_stat(r, "any_annotation_coverage", 0)
    return f"Type annotation coverage is {coverage * 100:.0f}%"


def _typing_suggestion(_r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    if score <= 2:
        return "Add type hints to function signatures, starting with public APIs. Consider using mypy or pyright for type checking."
    return "Continue adding type hints to remaining functions. Focus on return types and complex function signatures."


# Docstring coverage rating
def _docstring_score(r: ConventionRule) -> int:
    ratio = _get_stat(r, "function_doc_ratio", 0)
    if ratio >= 0.8:
        return 5
    if ratio >= 0.6:
        return 4
    if ratio >= 0.4:
        return 3
    if ratio >= 0.2:
        return 2
    return 1


def _docstring_reason(r: ConventionRule, _score: int) -> str:
    ratio = _get_stat(r, "function_doc_ratio", 0)
    return f"Docstring coverage is {ratio * 100:.0f}% of public functions"


def _docstring_suggestion(_r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    if score <= 2:
        return "Add docstrings to public functions and classes. Focus on explaining the 'why' and documenting parameters/return values."
    return "Continue adding docstrings to remaining public functions. Consider using a consistent docstring style (Google, NumPy, or Sphinx)."


# Docstring style rating
def _docstring_style_score(r: ConventionRule) -> int:
    ratio = _get_stat(r, "primary_ratio", 0)
    primary = r.stats.get("primary_style", "")
    # Prefer Google or NumPy style as more readable
    is_modern_style = primary in ("google", "numpy")
    if ratio >= 0.9 and is_modern_style:
        return 5
    if ratio >= 0.8:
        return 4
    if ratio >= 0.6:
        return 3
    if ratio >= 0.4:
        return 2
    return 1


def _docstring_style_reason(r: ConventionRule, _score: int) -> str:
    ratio = _get_stat(r, "primary_ratio", 0)
    primary = r.stats.get("primary_style", "unknown")
    return f"Primary docstring style is {primary} ({ratio * 100:.0f}% consistency)"


def _docstring_style_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    primary = r.stats.get("primary_style", "")
    if score <= 2:
        return "Adopt a consistent docstring style (Google or NumPy recommended). Use tools like pydocstyle to enforce consistency."
    if primary not in ("google", "numpy"):
        return f"Consider migrating to Google or NumPy docstring style for better readability. Currently using {primary}."
    return "Standardize remaining docstrings to follow the primary style consistently."


# Naming conventions rating
def _naming_score(r: ConventionRule) -> int:
    ratio = _get_stat(r, "snake_case_ratio", 0)
    if ratio >= 1.0:
        return 5
    if ratio >= 0.95:
        return 4
    if ratio >= 0.8:
        return 3
    if ratio >= 0.6:
        return 2
    return 1


def _naming_reason(r: ConventionRule, _score: int) -> str:
    ratio = _get_stat(r, "snake_case_ratio", 0)
    return f"PEP 8 snake_case compliance is {ratio * 100:.0f}%"


def _naming_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    camel = r.stats.get("camel_case_functions", 0)
    if camel > 0:
        return f"Rename {camel} camelCase function(s) to snake_case to follow PEP 8 conventions."
    return "Review function names to ensure consistent snake_case naming per PEP 8."


# Testing framework rating
def _testing_framework_score(r: ConventionRule) -> int:
    primary = r.stats.get("primary_framework", "")
    test_files = r.stats.get("test_file_count", 0)

    # pytest is preferred
    if primary == "pytest" and test_files >= 5:
        return 5
    if primary == "pytest":
        return 4
    if primary == "unittest" and test_files >= 5:
        return 3
    if test_files >= 1:
        return 2
    return 1


def _testing_framework_reason(r: ConventionRule, _score: int) -> str:
    primary = r.stats.get("primary_framework", "unknown")
    test_files = r.stats.get("test_file_count", 0)
    return f"Uses {primary} with {test_files} test file(s)"


def _testing_framework_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    primary = r.stats.get("primary_framework", "")
    if primary != "pytest":
        return "Consider migrating to pytest for better fixture support, parametrization, and plugin ecosystem."
    return "Add more test files to improve test coverage."


# Testing fixtures rating
def _testing_fixtures_score(r: ConventionRule) -> int:
    fixtures = r.stats.get("fixture_count", 0)
    conftest = r.stats.get("conftest_count", 0)

    if conftest > 0 and fixtures >= 10:
        return 5
    if conftest > 0 and fixtures >= 5:
        return 4
    if fixtures >= 5:
        return 3
    if fixtures >= 2:
        return 2
    return 1


def _testing_fixtures_reason(r: ConventionRule, _score: int) -> str:
    fixtures = r.stats.get("fixture_count", 0)
    conftest = r.stats.get("conftest_count", 0)
    return f"Found {fixtures} fixtures, {conftest} conftest.py file(s)"


def _testing_fixtures_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    conftest = r.stats.get("conftest_count", 0)
    if conftest == 0:
        return "Create a conftest.py to centralize shared fixtures and improve test organization."
    return "Extract common setup logic into reusable fixtures to reduce test code duplication."


# Testing mocking rating
def _testing_mocking_score(r: ConventionRule) -> int:
    libs = r.stats.get("mock_library_counts", {})
    primary = r.stats.get("primary_mock_library", "")
    total = sum(libs.values())

    # Prefer pytest-mock over unittest.mock
    if primary == "pytest_mock" and len(libs) == 1:
        return 5
    if primary in ("pytest_mock", "unittest_mock") and total >= 5:
        return 4
    if total >= 3:
        return 3
    if total >= 1:
        return 2
    return 1


def _testing_mocking_reason(r: ConventionRule, _score: int) -> str:
    primary = r.stats.get("primary_mock_library", "unknown")
    libs = r.stats.get("mock_library_counts", {})
    return f"Primary mocking library is {primary}, using {len(libs)} library/libraries"


def _testing_mocking_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    primary = r.stats.get("primary_mock_library", "")
    libs = r.stats.get("mock_library_counts", {})
    if len(libs) > 2:
        return "Consolidate mocking libraries to reduce cognitive overhead. Consider standardizing on pytest-mock."
    if primary == "unittest_mock":
        return "Consider using pytest-mock for cleaner fixture-based mocking syntax."
    return "Ensure mocking patterns are consistent across the test suite."


# Logging library rating
def _logging_library_score(r: ConventionRule) -> int:
    primary = r.stats.get("primary_library", "")
    ratio = _get_stat(r, "primary_ratio", 0)

    # structlog and loguru are preferred for structured logging
    if primary in ("structlog", "loguru") and ratio >= 0.9:
        return 5
    if primary in ("structlog", "loguru"):
        return 4
    if primary == "stdlib_logging" and ratio >= 0.9:
        return 3
    if primary == "stdlib_logging":
        return 2
    return 1


def _logging_library_reason(r: ConventionRule, _score: int) -> str:
    primary = r.stats.get("primary_library", "unknown")
    lib_names = {"stdlib_logging": "stdlib logging", "structlog": "structlog", "loguru": "Loguru"}
    return f"Uses {lib_names.get(primary, primary)} as primary logging library"


def _logging_library_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    primary = r.stats.get("primary_library", "")
    if primary == "stdlib_logging":
        return "Consider adopting structlog or Loguru for structured logging with better context propagation."
    return "Standardize logging library usage across the codebase."


# Logging fields rating
def _logging_fields_score(r: ConventionRule) -> int:
    has_correlation = r.stats.get("has_request_correlation", False)
    total = r.stats.get("total_field_uses", 0)

    if has_correlation and total >= 20:
        return 5
    if has_correlation:
        return 4
    if total >= 10:
        return 3
    if total >= 5:
        return 2
    return 1


def _logging_fields_reason(r: ConventionRule, _score: int) -> str:
    has_correlation = r.stats.get("has_request_correlation", False)
    total = r.stats.get("total_field_uses", 0)
    if has_correlation:
        return f"Structured logging with request correlation ({total} field uses)"
    return f"Structured logging with {total} field uses"


def _logging_fields_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    has_correlation = r.stats.get("has_request_correlation", False)
    if not has_correlation:
        return "Add request/trace IDs to log context for better observability and debugging."
    return "Continue enriching log context with relevant fields (user_id, action, etc.)."


# Error handling boundary rating
def _error_boundary_score(r: ConventionRule) -> int:
    ratio = _get_stat(r, "api_ratio", 0)

    if ratio >= 0.95:
        return 5
    if ratio >= 0.8:
        return 4
    if ratio >= 0.6:
        return 3
    if ratio >= 0.4:
        return 2
    return 1


def _error_boundary_reason(r: ConventionRule, _score: int) -> str:
    ratio = _get_stat(r, "api_ratio", 0)
    return f"HTTPException raised in API layer {ratio * 100:.0f}% of the time"


def _error_boundary_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    by_role = r.stats.get("by_role", {})
    service_count = by_role.get("service", 0)
    if service_count > 0:
        return f"Move {service_count} HTTPException raise(s) from service layer to API layer. Services should raise domain exceptions."
    return "Ensure HTTP errors are raised only at the API boundary layer."


# Error taxonomy rating
def _error_taxonomy_score(r: ConventionRule) -> int:
    consistency = _get_stat(r, "consistency", 0)
    total = r.stats.get("total_custom_exceptions", 0)

    if consistency >= 0.9 and total >= 5:
        return 5
    if consistency >= 0.8:
        return 4
    if consistency >= 0.6:
        return 3
    if consistency >= 0.4:
        return 2
    return 1


def _error_taxonomy_reason(r: ConventionRule, _score: int) -> str:
    consistency = _get_stat(r, "consistency", 0)
    total = r.stats.get("total_custom_exceptions", 0)
    return f"Exception naming is {consistency * 100:.0f}% consistent across {total} custom exceptions"


def _error_taxonomy_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    error_count = r.stats.get("error_suffix_count", 0)
    exc_count = r.stats.get("exception_suffix_count", 0)
    preferred = "*Error" if error_count >= exc_count else "*Exception"
    return f"Standardize exception naming to use {preferred} suffix consistently."


# Exception handlers rating
def _exception_handlers_score(r: ConventionRule) -> int:
    files = r.stats.get("handler_files", [])
    total = r.stats.get("total_handlers", 0)

    if len(files) == 1 and total >= 3:
        return 5
    if len(files) <= 2:
        return 4
    if len(files) <= 3:
        return 3
    if len(files) <= 5:
        return 2
    return 1


def _exception_handlers_reason(r: ConventionRule, _score: int) -> str:
    files = r.stats.get("handler_files", [])
    total = r.stats.get("total_handlers", 0)
    return f"Exception handlers spread across {len(files)} module(s) ({total} handlers)"


def _exception_handlers_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    files = r.stats.get("handler_files", [])
    if len(files) > 3:
        return f"Consolidate exception handlers into a single module (currently in {len(files)} files)."
    return "Consider centralizing exception handlers for easier maintenance."


# Error wrapper pattern rating
def _error_wrapper_score(r: ConventionRule) -> int:
    """Score custom error wrapper patterns."""
    ratio = r.stats.get("usage_ratio", 0)
    count = r.stats.get("usage_count", 0)

    # High consistency in error handling is good
    if ratio >= 0.5 and count >= 10:
        return 5  # Very consistent error handling
    if ratio >= 0.3 and count >= 5:
        return 4  # Good consistency
    if ratio >= 0.15 and count >= 3:
        return 3  # Some pattern emerging
    return 2  # Pattern exists but not widely adopted


def _error_wrapper_reason(r: ConventionRule, _score: int) -> str:
    wrapper = r.stats.get("wrapper_function", "unknown")
    count = r.stats.get("usage_count", 0)
    total = r.stats.get("total_handlers", 0)
    ratio = r.stats.get("usage_ratio", 0)
    return f"Error wrapper '{wrapper}' used in {count}/{total} handlers ({ratio:.0%})"


def _error_wrapper_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    ratio = r.stats.get("usage_ratio", 0)
    wrapper = r.stats.get("wrapper_function", "")
    if ratio < 0.3:
        return f"Consider using '{wrapper}' more consistently across all exception handlers."
    return "Document the error wrapper pattern in your codebase guidelines."


# Error transformation pattern rating
def _error_transform_score(r: ConventionRule) -> int:
    """Score error transformation patterns."""
    ratio = r.stats.get("usage_ratio", 0)
    count = r.stats.get("usage_count", 0)

    # Consistent transformation to a custom exception is good
    if ratio >= 0.4 and count >= 8:
        return 5
    if ratio >= 0.25 and count >= 5:
        return 4
    if ratio >= 0.15 and count >= 3:
        return 3
    return 2


def _error_transform_reason(r: ConventionRule, _score: int) -> str:
    target = r.stats.get("target_exception", "unknown")
    count = r.stats.get("usage_count", 0)
    total = r.stats.get("total_handlers", 0)
    ratio = r.stats.get("usage_ratio", 0)
    return f"Transforms errors to '{target}' in {count}/{total} handlers ({ratio:.0%})"


def _error_transform_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    target = r.stats.get("target_exception", "")
    return f"Consider transforming more exceptions to '{target}' for consistent client error responses."


# Standardized error response pattern rating
def _error_response_score(r: ConventionRule) -> int:
    """Score standardized error response patterns."""
    ratio = r.stats.get("usage_ratio", 0)
    count = r.stats.get("usage_count", 0)

    if ratio >= 0.4 and count >= 5:
        return 5
    if ratio >= 0.25 and count >= 3:
        return 4
    if ratio >= 0.15:
        return 3
    return 2


def _error_response_reason(r: ConventionRule, _score: int) -> str:
    func = r.stats.get("response_function", "unknown")
    count = r.stats.get("usage_count", 0)
    total = r.stats.get("total_handlers", 0)
    ratio = r.stats.get("usage_ratio", 0)
    return f"Standardized error response via '{func}' in {count}/{total} handlers ({ratio:.0%})"


def _error_response_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    func = r.stats.get("response_function", "")
    return f"Use '{func}' in more exception handlers for consistent error responses to clients."


# Raw SQL usage rating (inverse - lower is better)
def _raw_sql_score(r: ConventionRule) -> int:
    count = r.stats.get("raw_sql_count", 0)

    if count == 0:
        return 5
    if count <= 2:
        return 3
    if count <= 5:
        return 2
    return 1


def _raw_sql_reason(r: ConventionRule, _score: int) -> str:
    count = r.stats.get("raw_sql_count", 0)
    return f"Found {count} instance(s) of raw SQL execution"


def _raw_sql_suggestion(_r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    return "Replace raw SQL with ORM queries or use parameterized queries to prevent SQL injection vulnerabilities."


# Async style rating
def _async_style_score(r: ConventionRule) -> int:
    ratio = _get_stat(r, "async_ratio", 0)
    asyncio_patterns = r.stats.get("asyncio_patterns", 0)
    is_async_framework = r.stats.get("is_async_framework", False)

    # For async-first frameworks (FastAPI/Starlette), prefer async endpoints
    if is_async_framework:
        if ratio >= 0.8:
            return 5
        if ratio >= 0.5:
            return 4
        return 3  # Sync in async framework is suboptimal

    # For other frameworks, consistency is good (either all async or all sync)
    consistency = max(ratio, 1 - ratio)

    if consistency >= 0.9 and asyncio_patterns > 0:
        return 5
    if consistency >= 0.9:
        return 4
    if consistency >= 0.7:
        return 3
    if consistency >= 0.5:
        return 2
    return 1


def _async_style_reason(r: ConventionRule, _score: int) -> str:
    ratio = _get_stat(r, "async_ratio", 0)
    async_count = r.stats.get("async_count", 0)
    sync_count = r.stats.get("sync_count", 0)
    is_async_framework = r.stats.get("is_async_framework", False)
    framework_note = " (async framework)" if is_async_framework else ""
    return f"API style: {async_count} async, {sync_count} sync ({ratio * 100:.0f}% async){framework_note}"


def _async_style_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    ratio = _get_stat(r, "async_ratio", 0)
    is_async_framework = r.stats.get("is_async_framework", False)

    if is_async_framework and ratio < 0.8:
        return "FastAPI/Starlette are async-first. Use async endpoints for better performance."
    if 0.3 <= ratio <= 0.7:
        return "Standardize API endpoints to be consistently async or sync to reduce cognitive overhead."
    return "Consider whether a consistent async-first or sync-first approach better suits your use case."


# Layering direction rating
def _layering_score(r: ConventionRule) -> int:
    api_to_db = r.stats.get("api_to_db", 0)
    api_to_service = r.stats.get("api_to_service", 0)
    service_to_db = r.stats.get("service_to_db", 0)

    # Strict layering: API -> Service -> DB with no shortcuts
    if api_to_service > 0 and service_to_db > 0 and api_to_db == 0:
        return 5
    if api_to_service > api_to_db and service_to_db > 0:
        return 4
    if api_to_db == 0:
        return 3
    if api_to_db <= api_to_service:
        return 2
    return 1


def _layering_reason(r: ConventionRule, _score: int) -> str:
    api_to_db = r.stats.get("api_to_db", 0)
    api_to_service = r.stats.get("api_to_service", 0)
    service_to_db = r.stats.get("service_to_db", 0)
    return f"API->Service: {api_to_service}, Service->DB: {service_to_db}, API->DB: {api_to_db}"


def _layering_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    api_to_db = r.stats.get("api_to_db", 0)
    if api_to_db > 0:
        return f"Remove {api_to_db} direct API->DB import(s). Route database access through the service layer."
    return "Enforce strict layering: API should only import from Service, Service from DB."


# Forbidden imports (boundary violations) rating
def _forbidden_imports_score(r: ConventionRule) -> int:
    total = r.stats.get("total_violations", 0)

    if total == 0:
        return 5
    if total <= 2:
        return 4
    if total <= 5:
        return 3
    if total <= 10:
        return 2
    return 1


def _forbidden_imports_reason(r: ConventionRule, _score: int) -> str:
    total = r.stats.get("total_violations", 0)
    return f"Found {total} layer boundary violation(s)"


def _forbidden_imports_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    violations = r.stats.get("violations_by_type", {})
    details = ", ".join(f"{k}: {v}" for k, v in violations.items())
    return f"Fix boundary violations: {details}. Consider using dependency inversion."


# Schema library rating
def _schema_library_score(r: ConventionRule) -> int:
    primary = r.stats.get("primary_library", "")
    libs = r.stats.get("library_counts", {})

    # Pydantic is preferred for FastAPI projects
    if primary == "pydantic" and len(libs) == 1:
        return 5
    if primary == "pydantic":
        return 4
    if primary in ("attrs", "dataclasses", "msgspec"):
        return 4
    if primary == "marshmallow":
        return 3
    if len(libs) > 0:
        return 2
    return 1


def _schema_library_reason(r: ConventionRule, _score: int) -> str:
    primary = r.stats.get("primary_library", "unknown")
    lib_names = {"pydantic": "Pydantic", "dataclasses": "dataclasses", "attrs": "attrs", "marshmallow": "Marshmallow", "msgspec": "msgspec"}
    return f"Uses {lib_names.get(primary, primary)} for schema validation"


def _schema_library_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    primary = r.stats.get("primary_library", "")
    libs = r.stats.get("library_counts", {})
    if len(libs) > 2:
        return "Consolidate schema libraries. For FastAPI, standardize on Pydantic."
    if primary == "marshmallow":
        return "Consider migrating to Pydantic for better FastAPI integration and type checking support."
    return "Ensure consistent schema library usage across the codebase."


# API framework rating
def _api_framework_score(r: ConventionRule) -> int:
    primary = r.stats.get("primary_framework", "")
    frameworks = r.stats.get("framework_counts", {})

    # Async-first frameworks always score 5 (opinionated for async)
    if primary in ("fastapi", "litestar"):
        return 5

    # Good sync-first frameworks score 4
    if primary in ("flask", "django", "starlette"):
        return 4

    # Other known frameworks
    if primary in ("aiohttp", "falcon"):
        return 4

    # Multiple frameworks or unknown
    if len(frameworks) == 1:
        return 3
    return 2


def _api_framework_reason(r: ConventionRule, _score: int) -> str:
    primary = r.stats.get("primary_framework", "unknown")
    framework_names = {"fastapi": "FastAPI", "flask": "Flask", "django": "Django", "starlette": "Starlette", "litestar": "Litestar"}
    return f"Uses {framework_names.get(primary, primary)} as primary API framework"


def _api_framework_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    primary = r.stats.get("primary_framework", "")
    frameworks = r.stats.get("framework_counts", {})

    if len(frameworks) > 1:
        return "Consolidate API frameworks to a single choice for consistency."
    if primary in ("flask", "django"):
        return "For new async-first projects, consider FastAPI or Litestar."
    return None


# Auth pattern rating
def _auth_pattern_score(r: ConventionRule) -> int:
    has_jwt = r.stats.get("jwt", 0) > 0
    has_oauth2 = r.stats.get("oauth2", 0) > 0
    has_dependency = r.stats.get("dependency_auth", 0) > 0
    has_passlib = r.stats.get("passlib", 0) > 0 or r.stats.get("bcrypt", 0) > 0

    if (has_jwt or has_oauth2) and has_dependency and has_passlib:
        return 5
    if (has_jwt or has_oauth2) and has_dependency:
        return 4
    if has_jwt or has_oauth2:
        return 3
    if has_dependency:
        return 3
    return 2


def _auth_pattern_reason(r: ConventionRule, _score: int) -> str:
    patterns = []
    if r.stats.get("jwt", 0) > 0:
        patterns.append("JWT")
    if r.stats.get("oauth2", 0) > 0:
        patterns.append("OAuth2")
    if r.stats.get("dependency_auth", 0) > 0:
        patterns.append("dependency injection")
    return f"Authentication uses {', '.join(patterns) if patterns else 'custom pattern'}"


def _auth_pattern_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    has_passlib = r.stats.get("passlib", 0) > 0 or r.stats.get("bcrypt", 0) > 0
    if not has_passlib:
        return "Use a dedicated password hashing library (passlib or bcrypt) for secure credential storage."
    return "Ensure authentication is consistently applied via dependency injection for all protected endpoints."


# Secrets access style rating
def _secrets_style_score(r: ConventionRule) -> int:
    has_pydantic = r.stats.get("pydantic_settings", 0) > 0
    os_environ = r.stats.get("os_environ", 0)

    if has_pydantic and os_environ == 0:
        return 5
    if has_pydantic:
        return 4
    if os_environ <= 5:
        return 3
    if os_environ <= 10:
        return 2
    return 1


def _secrets_style_reason(r: ConventionRule, _score: int) -> str:
    has_pydantic = r.stats.get("pydantic_settings", 0) > 0
    os_environ = r.stats.get("os_environ", 0)
    if has_pydantic:
        return f"Uses Pydantic Settings for configuration (os.environ: {os_environ} direct accesses)"
    return f"Uses os.environ for configuration ({os_environ} direct accesses)"


def _secrets_style_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    has_pydantic = r.stats.get("pydantic_settings", 0) > 0
    if not has_pydantic:
        return "Adopt Pydantic BaseSettings for type-safe configuration with validation and environment variable parsing."
    return "Replace remaining os.environ accesses with Settings class properties."


# Generic fallback rating for unknown conventions
def _generic_score(r: ConventionRule) -> int:
    # Use confidence as a rough proxy
    if r.confidence >= 0.9:
        return 4
    if r.confidence >= 0.7:
        return 3
    if r.confidence >= 0.5:
        return 2
    return 1


def _generic_reason(r: ConventionRule, _score: int) -> str:
    return f"Convention detected with {r.confidence * 100:.0f}% confidence"


def _generic_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 4:
        return None

    # Try to provide category-specific suggestion
    category = r.category.lower()
    if category in CATEGORY_SUGGESTIONS:
        base = CATEGORY_SUGGESTIONS[category]
        return _make_actionable_suggestion(r, base)

    # Map common category variations
    category_mapping = {
        "type_coverage": "typing",
        "typing_coverage": "typing",
        "docstrings": "documentation",
        "docstring": "documentation",
        "test": "testing",
        "tests": "testing",
        "log": "logging",
        "logs": "logging",
        "error": "error_handling",
        "errors": "error_handling",
        "exception": "error_handling",
        "security": "security",
        "auth": "security",
        "architecture": "architecture",
        "layer": "architecture",
        "ci": "ci_cd",
        "cd": "ci_cd",
        "pipeline": "ci_cd",
    }

    for key, mapped_category in category_mapping.items():
        if key in category:
            if mapped_category in CATEGORY_SUGGESTIONS:
                base = CATEGORY_SUGGESTIONS[mapped_category]
                return _make_actionable_suggestion(r, base)

    return "Review this convention and consider industry best practices for improvement."


# ============================================
# Python Resilience Ratings
# ============================================


# Retries rating (best-practice based)
def _retries_score(r: ConventionRule) -> int:
    """Score retry library usage - tenacity is the gold standard."""
    libs = r.stats.get("retry_library_counts", {})
    primary = r.stats.get("primary_library", "")

    # tenacity is the only library used
    if primary == "tenacity" and len(libs) == 1:
        return 5
    # tenacity or backoff (both good)
    if primary in ("tenacity", "backoff"):
        return 4
    # retrying (older library)
    if primary == "retrying":
        return 3
    # urllib3 Retry only (limited scope)
    if primary == "urllib3_retry":
        return 2
    # No retry library
    return 1


def _retries_reason(r: ConventionRule, _score: int) -> str:
    primary = r.stats.get("primary_library", "none")
    libs = r.stats.get("retry_library_counts", {})
    lib_names = {
        "tenacity": "tenacity",
        "backoff": "backoff",
        "retrying": "retrying",
        "urllib3_retry": "urllib3 Retry",
    }
    if not libs:
        return "No retry library detected"
    return f"Uses {lib_names.get(primary, primary)} for retry logic"


def _retries_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    primary = r.stats.get("primary_library", "")
    if score == 1:
        return "Add retry logic using tenacity for exponential backoff, jitter, and async support."
    if primary == "urllib3_retry":
        return "Consider using tenacity for application-level retries with more control over backoff strategies."
    if primary == "retrying":
        return "Consider migrating to tenacity - it's more actively maintained with better async support."
    return "Standardize on tenacity for retry logic across the codebase."


# Timeouts rating (coverage based)
def _timeouts_score(r: ConventionRule) -> int:
    """Score timeout usage - all external calls should have explicit timeouts."""
    ratio = _get_stat(r, "timeout_ratio", 0)

    if ratio >= 0.8:
        return 5
    if ratio >= 0.6:
        return 4
    if ratio >= 0.4:
        return 3
    if ratio >= 0.2:
        return 2
    return 1


def _timeouts_reason(r: ConventionRule, _score: int) -> str:
    ratio = _get_stat(r, "timeout_ratio", 0)
    with_timeout = r.stats.get("timeout_indicators", 0)
    without_timeout = r.stats.get("no_timeout_indicators", 0)
    return f"Timeout coverage is {ratio * 100:.0f}% ({with_timeout} with, {without_timeout} without)"


def _timeouts_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    without_timeout = r.stats.get("no_timeout_indicators", 0)
    if score <= 2:
        return f"Add explicit timeouts to HTTP client calls. Found {without_timeout} calls without timeouts."
    return "Continue adding explicit timeouts to remaining HTTP client calls to prevent hanging requests."


# Circuit breakers rating (best-practice based)
def _circuit_breaker_score(r: ConventionRule) -> int:
    """Score circuit breaker usage."""
    libs = r.stats.get("circuit_breaker_library_counts", {})
    primary = r.stats.get("primary_library", "")
    breaker_count = r.stats.get("circuit_breaker_count", 0)

    # pybreaker or aiobreaker with multiple breakers
    if primary in ("pybreaker", "aiobreaker") and breaker_count >= 3:
        return 5
    # Any circuit breaker library with usage
    if libs and breaker_count >= 1:
        return 4
    # Single circuit breaker
    if breaker_count == 1:
        return 3
    # Library imported but no usage
    if libs:
        return 2
    # No circuit breaker
    return 1


def _circuit_breaker_reason(r: ConventionRule, _score: int) -> str:
    primary = r.stats.get("primary_library", "none")
    breaker_count = r.stats.get("circuit_breaker_count", 0)
    lib_names = {
        "pybreaker": "pybreaker",
        "circuitbreaker": "circuitbreaker",
        "aiobreaker": "aiobreaker",
    }
    if breaker_count == 0:
        if primary and primary != "none":
            return f"Imports {lib_names.get(primary, primary)} but no circuit breakers defined"
        return "No circuit breaker pattern detected"
    return f"Uses {lib_names.get(primary, primary)} with {breaker_count} circuit breaker(s)"


def _circuit_breaker_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    breaker_count = r.stats.get("circuit_breaker_count", 0)
    has_external_apis = r.stats.get("has_external_apis", False)
    http_client_count = r.stats.get("http_client_count", 0)

    if score == 1 and has_external_apis:
        return f"STRONGLY RECOMMENDED: Add circuit breakers for external API calls. Found {http_client_count} HTTP client imports without protection."
    if score == 1:
        return "Add circuit breakers using pybreaker to protect against cascading failures from unreliable dependencies."
    if score == 2:
        return "Define circuit breakers for external service calls to prevent cascading failures."
    if breaker_count < 3 and has_external_apis:
        return "Consider adding circuit breakers to more external service integrations."
    return None


# Health checks rating
def _health_check_score(r: ConventionRule) -> int:
    """Score health check endpoint coverage."""
    has_readiness = r.stats.get("has_readiness", False)
    has_liveness = r.stats.get("has_liveness", False)
    health_count = r.stats.get("health_endpoint_count", 0)

    # Both readiness AND liveness endpoints
    if has_readiness and has_liveness:
        return 5
    # Health endpoint + either readiness or liveness
    if health_count > 0 and (has_readiness or has_liveness):
        return 4
    # Single health endpoint
    if health_count > 0:
        return 3
    # Health-related function but no endpoint
    if r.stats.get("health_function_count", 0) > 0:
        return 2
    # No health checks
    return 1


def _health_check_reason(r: ConventionRule, _score: int) -> str:
    has_readiness = r.stats.get("has_readiness", False)
    has_liveness = r.stats.get("has_liveness", False)
    health_count = r.stats.get("health_endpoint_count", 0)

    parts = []
    if health_count > 0:
        parts.append(f"{health_count} health endpoint(s)")
    if has_readiness:
        parts.append("readiness")
    if has_liveness:
        parts.append("liveness")

    if not parts:
        return "No health check endpoints detected"
    return f"Health checks: {', '.join(parts)}"


def _health_check_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    has_readiness = r.stats.get("has_readiness", False)
    has_liveness = r.stats.get("has_liveness", False)

    if score == 1:
        return "Add health check endpoints (/health, /ready, /live) for container orchestration and load balancer integration."
    if not has_readiness and not has_liveness:
        return "Add separate /ready (readiness) and /live (liveness) endpoints for Kubernetes deployments."
    if not has_readiness:
        return "Add a /ready endpoint to signal when the service is ready to accept traffic."
    if not has_liveness:
        return "Add a /live endpoint to signal when the service is running (for restart detection)."
    return None


# ============================================
# Python Observability Ratings
# ============================================


# Tracing rating (best-practice based)
def _tracing_score(r: ConventionRule) -> int:
    """Score tracing implementation - OpenTelemetry is the industry standard."""
    libs = r.stats.get("tracing_library_counts", {})
    primary = r.stats.get("primary_library", "")
    spans = r.stats.get("spans_created", 0)

    # OpenTelemetry with active span creation
    if primary == "opentelemetry" and spans > 0:
        return 5
    # OpenTelemetry (imports only) or OpenTracing with spans
    if primary == "opentelemetry" or (primary == "opentracing" and spans > 0):
        return 4
    # Vendor SDK (Sentry, Datadog, Jaeger) with spans
    if primary in ("sentry", "datadog", "jaeger") and spans > 0:
        return 3
    # Vendor SDK (imports only)
    if primary in ("sentry", "datadog", "jaeger"):
        return 2
    # No tracing
    return 1


def _tracing_reason(r: ConventionRule, _score: int) -> str:
    primary = r.stats.get("primary_library", "none")
    spans = r.stats.get("spans_created", 0)
    lib_names = {
        "opentelemetry": "OpenTelemetry",
        "opentracing": "OpenTracing",
        "jaeger": "Jaeger",
        "sentry": "Sentry",
        "datadog": "Datadog",
    }
    if primary == "none" or not primary:
        return "No distributed tracing detected"
    name = lib_names.get(primary, primary)
    if spans > 0:
        return f"Uses {name} with {spans} span creation(s)"
    return f"Imports {name} tracing library"


def _tracing_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    primary = r.stats.get("primary_library", "")
    spans = r.stats.get("spans_created", 0)

    if score == 1:
        return "Add distributed tracing using OpenTelemetry for end-to-end request visibility."
    if primary in ("sentry", "datadog", "jaeger"):
        return "Consider migrating to OpenTelemetry for vendor-neutral distributed tracing."
    if spans == 0:
        return "Add span creation to instrument key operations and service boundaries."
    return "Continue instrumenting critical paths with custom spans for better observability."


# Metrics rating (best-practice based)
def _metrics_score(r: ConventionRule) -> int:
    """Score metrics implementation - Prometheus is widely supported."""
    libs = r.stats.get("metrics_library_counts", {})
    primary = r.stats.get("primary_library", "")
    metric_defs = r.stats.get("metric_definitions", 0)

    # Prometheus with multiple metric definitions
    if primary == "prometheus" and metric_defs >= 5:
        return 5
    # Prometheus or OpenTelemetry Metrics
    if primary in ("prometheus", "opentelemetry_metrics", "aioprometheus"):
        return 4
    # StatsD/Datadog with definitions
    if primary == "statsd" and metric_defs > 0:
        return 3
    # Any metrics library (imports only)
    if libs:
        return 2
    # No metrics
    return 1


def _metrics_reason(r: ConventionRule, _score: int) -> str:
    primary = r.stats.get("primary_library", "none")
    metric_defs = r.stats.get("metric_definitions", 0)
    lib_names = {
        "prometheus": "Prometheus",
        "statsd": "StatsD/Datadog",
        "opentelemetry_metrics": "OpenTelemetry Metrics",
        "aioprometheus": "aioprometheus",
    }
    if primary == "none" or not primary:
        return "No application metrics detected"
    name = lib_names.get(primary, primary)
    if metric_defs > 0:
        return f"Uses {name} with {metric_defs} metric definition(s)"
    return f"Imports {name} metrics library"


def _metrics_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    primary = r.stats.get("primary_library", "")
    metric_defs = r.stats.get("metric_definitions", 0)

    if score == 1:
        return "Add application metrics using Prometheus for standardized monitoring and alerting."
    if primary == "statsd":
        return "Consider migrating to Prometheus for pull-based metrics with better querying capabilities."
    if metric_defs == 0:
        return "Define metrics (Counter, Gauge, Histogram) for key business and operational indicators."
    if metric_defs < 5:
        return "Add more metric definitions to track request latency, error rates, and business KPIs."
    return None


# Correlation IDs rating (usage based)
def _correlation_ids_score(r: ConventionRule) -> int:
    """Score correlation ID usage - more consistent usage is better."""
    refs = r.stats.get("correlation_id_references", 0)

    if refs >= 10:
        return 5
    if refs >= 5:
        return 4
    if refs >= 3:
        return 3
    if refs >= 2:
        return 2
    return 1


def _correlation_ids_reason(r: ConventionRule, _score: int) -> str:
    refs = r.stats.get("correlation_id_references", 0)
    uuid_count = r.stats.get("uuid_generation_count", 0)
    if refs == 0:
        return "No correlation ID pattern detected"
    msg = f"Found {refs} correlation ID reference(s)"
    if uuid_count > 0:
        msg += f" with {uuid_count} UUID generation(s)"
    return msg


def _correlation_ids_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    refs = r.stats.get("correlation_id_references", 0)

    if score == 1:
        return "Add request/correlation IDs to track requests across service boundaries for debugging."
    if refs < 5:
        return "Propagate correlation IDs more consistently through logging and downstream service calls."
    return "Continue propagating correlation IDs through all service calls and log entries."


# ============================================
# Python Background Tasks & Caching Ratings
# ============================================


# Background tasks / task queue rating
def _task_queue_score(r: ConventionRule) -> int:
    """Score task queue library - modern async-first libraries preferred."""
    primary = r.stats.get("primary_library", "")
    libraries = r.stats.get("libraries", [])

    # Modern async-first task queues
    if primary in ("dramatiq", "arq"):
        return 5
    # Celery with good setup
    if primary == "celery" and len(libraries) == 1:
        return 4
    # Multiple task queue libraries or older ones
    if primary in ("celery", "huey", "rq"):
        return 4
    # APScheduler (scheduling, not task queue)
    if primary == "apscheduler":
        return 3
    return 3


def _task_queue_reason(r: ConventionRule, _score: int) -> str:
    primary = r.stats.get("primary_library", "unknown")
    lib_names = {
        "celery": "Celery",
        "dramatiq": "Dramatiq",
        "arq": "arq",
        "rq": "RQ",
        "huey": "Huey",
        "apscheduler": "APScheduler",
    }
    return f"Uses {lib_names.get(primary, primary)} for background tasks"


def _task_queue_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    primary = r.stats.get("primary_library", "")
    if primary == "celery":
        return "Celery is solid. For async-native code, consider Dramatiq or arq for better asyncio integration."
    if primary == "apscheduler":
        return "APScheduler is good for scheduling. For distributed task queues, consider Celery or Dramatiq."
    return None


# Caching rating
def _caching_score(r: ConventionRule) -> int:
    """Score caching implementation - distributed caching preferred for production."""
    methods = r.stats.get("caching_methods", [])
    primary = r.stats.get("primary_method", "")

    # Redis or aiocache (distributed, production-ready)
    if "redis" in methods or "aiocache" in methods or primary == "redis" or primary == "aiocache":
        return 5
    # cachetools (more sophisticated than lru_cache)
    if "cachetools" in methods or primary == "cachetools":
        return 4
    # functools.cache/lru_cache (simple, in-memory)
    if primary in ("lru_cache", "cache") or "lru_cache" in methods or "cache" in methods:
        return 4
    # diskcache
    if "diskcache" in methods or primary == "diskcache":
        return 3
    return 3


def _caching_reason(r: ConventionRule, _score: int) -> str:
    methods = r.stats.get("caching_methods", [])
    if not methods:
        return "No caching detected"
    method_names = {
        "lru_cache": "functools.lru_cache",
        "cache": "functools.cache",
        "redis": "Redis",
        "cachetools": "cachetools",
        "aiocache": "aiocache",
        "diskcache": "diskcache",
    }
    names = [method_names.get(m, m) for m in methods]
    return f"Caching with {', '.join(names)}"


def _caching_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    methods = r.stats.get("caching_methods", [])
    if "redis" not in methods and "aiocache" not in methods:
        return "Consider Redis for distributed caching in production environments."
    return None


# ============================================
# Python Database Extended Ratings
# ============================================


# Database migrations rating
def _db_migrations_score(r: ConventionRule) -> int:
    """Score database migration tools."""
    primary = r.stats.get("primary_tool", "")

    # Alembic is the standard for SQLAlchemy
    if primary == "alembic":
        return 5
    # Django migrations (good for Django)
    if primary == "django_migrations":
        return 5
    # Aerich for Tortoise ORM
    if primary == "aerich":
        return 4
    # yoyo (simpler, less featured)
    if primary == "yoyo":
        return 3
    return 3


def _db_migrations_reason(r: ConventionRule, _score: int) -> str:
    primary = r.stats.get("primary_tool", "unknown")
    tool_names = {
        "alembic": "Alembic",
        "django_migrations": "Django Migrations",
        "yoyo": "yoyo-migrations",
        "aerich": "Aerich",
    }
    return f"Uses {tool_names.get(primary, primary)} for database migrations"


def _db_migrations_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    primary = r.stats.get("primary_tool", "")
    if primary == "yoyo":
        return "Consider Alembic for more powerful migration features like autogenerate."
    return None


# Connection pooling rating
def _db_connection_pooling_score(r: ConventionRule) -> int:
    """Score database connection pooling configuration."""
    stats = r.stats

    # Explicitly configured pool with limits
    if stats.get("configured_pool", 0) > 0:
        return 5
    # asyncpg pool (good for async)
    if stats.get("asyncpg_pool", 0) > 0:
        return 5
    # QueuePool explicitly (good awareness)
    if stats.get("queue_pool", 0) > 0:
        return 4
    # NullPool for serverless (appropriate choice)
    if stats.get("null_pool", 0) > 0:
        return 4
    # Default pooling
    if stats.get("default_pool", 0) > 0:
        return 3
    return 3


def _db_connection_pooling_reason(r: ConventionRule, _score: int) -> str:
    stats = r.stats
    if stats.get("configured_pool", 0) > 0:
        return "Connection pooling is explicitly configured"
    if stats.get("null_pool", 0) > 0:
        return "Uses NullPool for serverless environments"
    if stats.get("asyncpg_pool", 0) > 0:
        return "Uses asyncpg connection pooling"
    return "Uses default connection pooling"


def _db_connection_pooling_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    if score <= 3:
        return "Configure pool_size, max_overflow, and pool_pre_ping for production reliability."
    return None


# ============================================
# Python Security Extended Ratings
# ============================================


# Rate limiting rating
def _rate_limiting_score(r: ConventionRule) -> int:
    """Score rate limiting implementation."""
    primary = r.stats.get("primary_library", "")
    decorator_count = r.stats.get("decorator_usage_count", 0)

    # Active rate limiting with decorators
    if decorator_count >= 5:
        return 5
    if decorator_count >= 2:
        return 4
    # Library imported
    if primary:
        return 3
    return 2


def _rate_limiting_reason(r: ConventionRule, _score: int) -> str:
    primary = r.stats.get("primary_library", "unknown")
    decorator_count = r.stats.get("decorator_usage_count", 0)
    lib_names = {
        "slowapi": "SlowAPI",
        "flask_limiter": "Flask-Limiter",
        "django_ratelimit": "django-ratelimit",
        "limits": "limits",
    }
    msg = f"Uses {lib_names.get(primary, primary)} for rate limiting"
    if decorator_count > 0:
        msg += f" ({decorator_count} endpoints)"
    return msg


def _rate_limiting_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    decorator_count = r.stats.get("decorator_usage_count", 0)
    if decorator_count == 0:
        return "Apply rate limiting decorators to API endpoints to prevent abuse."
    return "Consider adding rate limits to more endpoints, especially authentication routes."


# Password hashing rating
def _password_hashing_score(r: ConventionRule) -> int:
    """Score password hashing - argon2 is the gold standard."""
    quality = r.stats.get("quality", "unknown")
    primary = r.stats.get("primary_library", "")

    if quality == "excellent" or primary == "argon2":
        return 5
    if quality == "good" or primary in ("bcrypt", "passlib_cryptcontext", "passlib"):
        return 4
    if quality == "weak" or primary == "hashlib":
        return 1
    return 3


def _password_hashing_reason(r: ConventionRule, _score: int) -> str:
    primary = r.stats.get("primary_library", "unknown")
    lib_names = {
        "argon2": "argon2-cffi",
        "bcrypt": "bcrypt",
        "passlib": "passlib",
        "passlib_cryptcontext": "passlib CryptContext",
        "hashlib": "hashlib",
    }
    return f"Uses {lib_names.get(primary, primary)} for password hashing"


def _password_hashing_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    primary = r.stats.get("primary_library", "")
    if primary == "hashlib":
        return "CRITICAL: hashlib is not suitable for passwords. Use argon2-cffi or bcrypt immediately."
    if primary == "passlib":
        return "Consider using passlib's CryptContext with argon2 or bcrypt schemes."
    if score <= 3:
        return "Consider upgrading to argon2-cffi for the most secure password hashing."
    return None


# ============================================
# Python API Extended Ratings
# ============================================


# API versioning rating
def _api_versioning_score(r: ConventionRule) -> int:
    """Score API versioning implementation."""
    patterns = r.stats.get("versioning_patterns", {})
    primary = r.stats.get("primary_pattern", "")

    # URL versioning (clear and RESTful)
    if primary == "url_versioning":
        count = patterns.get("url_versioning", 0)
        if count >= 10:
            return 5
        if count >= 5:
            return 4
        return 3
    # Header versioning (valid but less discoverable)
    if primary == "header_versioning":
        return 3
    return 3


def _api_versioning_reason(r: ConventionRule, _score: int) -> str:
    primary = r.stats.get("primary_pattern", "unknown")
    patterns = r.stats.get("versioning_patterns", {})

    if primary == "url_versioning":
        count = patterns.get("url_versioning", 0)
        return f"URL-based API versioning ({count} versioned routes)"
    if primary == "header_versioning":
        return "Header-based API versioning"
    return "API versioning detected"


def _api_versioning_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    primary = r.stats.get("primary_pattern", "")
    if primary == "header_versioning":
        return "URL versioning (/v1/, /v2/) is more discoverable than header versioning."
    return "Apply consistent versioning across all API routes."


# OpenAPI documentation rating
def _openapi_docs_score(r: ConventionRule) -> int:
    """Score OpenAPI documentation."""
    primary = r.stats.get("primary_tool", "")

    # Customized FastAPI or dedicated OpenAPI tools
    if primary in ("fastapi_customized", "drf_spectacular"):
        return 5
    # Default FastAPI (good but could be customized)
    if primary == "fastapi_builtin":
        return 4
    # Other OpenAPI tools
    if primary in ("flasgger", "flask_openapi3", "apispec", "spectree"):
        return 4
    return 3


def _openapi_docs_reason(r: ConventionRule, _score: int) -> str:
    primary = r.stats.get("primary_tool", "unknown")
    tool_names = {
        "fastapi_builtin": "FastAPI (default)",
        "fastapi_customized": "FastAPI (customized)",
        "drf_spectacular": "drf-spectacular",
        "flasgger": "Flasgger",
        "flask_openapi3": "flask-openapi3",
        "apispec": "apispec",
        "spectree": "SpecTree",
    }
    return f"OpenAPI docs via {tool_names.get(primary, primary)}"


def _openapi_docs_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    primary = r.stats.get("primary_tool", "")
    if primary == "fastapi_builtin":
        return "Customize OpenAPI metadata with tags, descriptions, and examples for better docs."
    return None


# ============================================
# Python Messaging & Async Ratings
# ============================================


# Message broker rating
def _message_broker_score(r: ConventionRule) -> int:
    """Score message broker choice."""
    primary = r.stats.get("primary_broker", "")

    # Kafka, NATS (highly scalable)
    if primary in ("kafka", "nats"):
        return 5
    # RabbitMQ (reliable, feature-rich)
    if primary == "rabbitmq":
        return 5
    # Redis pub/sub (simpler, less durable)
    if primary == "redis_pubsub":
        return 4
    # AWS SQS
    if primary == "aws_sqs":
        return 4
    # ZeroMQ (lower level)
    if primary == "zeromq":
        return 3
    return 3


def _message_broker_reason(r: ConventionRule, _score: int) -> str:
    primary = r.stats.get("primary_broker", "unknown")
    broker_names = {
        "kafka": "Apache Kafka",
        "rabbitmq": "RabbitMQ",
        "redis_pubsub": "Redis Pub/Sub",
        "nats": "NATS",
        "zeromq": "ZeroMQ",
        "aws_sqs": "AWS SQS",
    }
    return f"Uses {broker_names.get(primary, primary)} for messaging"


def _message_broker_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    primary = r.stats.get("primary_broker", "")
    if primary == "redis_pubsub":
        return "Redis Pub/Sub is good for simple cases. For durability, consider RabbitMQ or Kafka."
    if primary == "zeromq":
        return "ZeroMQ is powerful but low-level. Consider RabbitMQ for easier message patterns."
    return None


# Async HTTP client rating
def _async_http_client_score(r: ConventionRule) -> int:
    """Score async HTTP client choice - httpx is the modern standard."""
    primary = r.stats.get("primary_client", "")
    quality = r.stats.get("quality", "")

    if quality == "excellent" or primary == "httpx":
        return 5
    if quality == "good" or primary == "aiohttp":
        return 4
    if quality == "poor" or primary == "requests":
        return 2
    return 3


def _async_http_client_reason(r: ConventionRule, _score: int) -> str:
    primary = r.stats.get("primary_client", "unknown")
    client_names = {
        "httpx": "httpx",
        "aiohttp": "aiohttp",
        "requests": "requests (sync)",
        "asks": "asks",
    }
    return f"Uses {client_names.get(primary, primary)} for HTTP requests"


def _async_http_client_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    primary = r.stats.get("primary_client", "")
    if primary == "requests":
        return "requests is sync-only. Use httpx for async/await support and connection pooling."
    if primary == "aiohttp":
        return "aiohttp is good. httpx offers a cleaner API with both sync and async support."
    return None


# Feature flags rating
def _feature_flags_score(r: ConventionRule) -> int:
    """Score feature flag implementation."""
    primary = r.stats.get("primary_library", "")
    quality = r.stats.get("quality", "")

    # Managed services (most mature)
    if quality == "managed" or primary in ("launchdarkly", "split", "flagsmith"):
        return 5
    # Self-hosted solutions
    if quality == "self_hosted" or primary in ("unleash", "growthbook", "flipper"):
        return 4
    # Simple libraries
    if quality == "library":
        return 3
    # Environment variables
    if quality == "basic" or primary == "env_flags":
        return 2
    return 3


def _feature_flags_reason(r: ConventionRule, _score: int) -> str:
    primary = r.stats.get("primary_library", "unknown")
    lib_names = {
        "launchdarkly": "LaunchDarkly",
        "flagsmith": "Flagsmith",
        "unleash": "Unleash",
        "split": "Split.io",
        "flipper": "Flipper",
        "growthbook": "GrowthBook",
        "env_flags": "environment variables",
    }
    return f"Feature flags via {lib_names.get(primary, primary)}"


def _feature_flags_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    primary = r.stats.get("primary_library", "")
    if primary == "env_flags":
        return "Environment variable flags are basic. Consider Unleash or Flagsmith for targeting and analytics."
    if score <= 3:
        return "Consider a feature flag service for gradual rollouts, A/B testing, and kill switches."
    return None


# ============================================
# Python Serialization & Tooling Ratings
# ============================================


# JSON library rating
def _json_library_score(r: ConventionRule) -> int:
    """Score JSON library choice - orjson is fastest."""
    primary = r.stats.get("primary_library", "")

    if primary == "orjson":
        return 5
    if primary == "ujson":
        return 4
    if primary == "rapidjson":
        return 4
    if primary == "simplejson":
        return 3
    if primary == "json":
        return 3
    return 3


def _json_library_reason(r: ConventionRule, _score: int) -> str:
    primary = r.stats.get("primary_library", "unknown")
    total = r.stats.get("total_usages", 0)
    lib_names = {
        "orjson": "orjson (fastest)",
        "ujson": "ujson (fast)",
        "rapidjson": "python-rapidjson",
        "simplejson": "simplejson",
        "json": "stdlib json",
    }
    return f"Uses {lib_names.get(primary, primary)} ({total} usages)"


def _json_library_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    primary = r.stats.get("primary_library", "")
    if primary == "json":
        return "Consider orjson for 10x faster JSON serialization with minimal API changes."
    if primary in ("ujson", "simplejson"):
        return "Consider orjson - it's faster and handles more edge cases correctly."
    return None


# Type checker strictness rating
def _type_checker_strictness_score(r: ConventionRule) -> int:
    """Score type checker strictness - strict mode catches more bugs."""
    strictness = r.stats.get("strictness", "unknown")
    strict_options = r.stats.get("strict_options", [])

    if strictness == "strict":
        return 5
    if strictness == "mostly_strict" or len(strict_options) >= 5:
        return 4
    if strictness == "moderate" or len(strict_options) >= 2:
        return 3
    if strictness == "basic" or strict_options:
        return 2
    return 2


def _type_checker_strictness_reason(r: ConventionRule, _score: int) -> str:
    type_checker = r.stats.get("type_checker", "unknown")
    strictness = r.stats.get("strictness", "unknown")
    strict_options = r.stats.get("strict_options", [])

    if strictness == "strict":
        return f"{type_checker} in strict mode"
    if strict_options:
        return f"{type_checker} with {len(strict_options)} strict options"
    return f"{type_checker} ({strictness} mode)"


def _type_checker_strictness_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    type_checker = r.stats.get("type_checker", "mypy")
    strictness = r.stats.get("strictness", "")

    if score <= 2:
        return f"Enable strict mode in {type_checker} to catch more type errors at development time."
    if score == 3:
        return f"Consider enabling more strict options in {type_checker} (disallow_untyped_defs, warn_return_any)."
    return f"Enable remaining strict options in {type_checker} for maximum type safety."


# Lock file rating
def _lock_file_score(r: ConventionRule) -> int:
    """Score lock file presence and quality."""
    quality = r.stats.get("quality", "none")
    primary = r.stats.get("primary_lock", "")

    if quality == "modern" or primary in ("uv", "poetry"):
        return 5
    if quality == "good" or primary in ("pdm", "pipenv", "pip_hashes"):
        return 4
    if quality == "basic" or primary == "pip_pinned":
        return 3
    if quality == "partial":
        return 2
    # No lock file
    return 1


def _lock_file_reason(r: ConventionRule, _score: int) -> str:
    primary = r.stats.get("primary_lock", "none")
    lock_files = r.stats.get("lock_files", {})

    if not lock_files:
        return "No lock file for reproducible builds"

    lock_names = {
        "uv": "uv.lock",
        "poetry": "poetry.lock",
        "pdm": "pdm.lock",
        "pipenv": "Pipfile.lock",
        "pip_hashes": "requirements.txt with hashes",
        "pip_pinned": "requirements.txt (pinned)",
        "pip_mostly_pinned": "requirements.txt (mostly pinned)",
    }
    return f"Lock file: {lock_names.get(primary, primary)}"


def _lock_file_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    primary = r.stats.get("primary_lock", "")

    if score == 1:
        return "Add a lock file (uv.lock or poetry.lock) for reproducible dependency installation."
    if primary in ("pip_pinned", "pip_mostly_pinned"):
        return "Consider uv or poetry for better dependency resolution and lock file management."
    if primary == "pipenv":
        return "Pipenv works, but uv or poetry offer faster, more modern dependency management."
    return None


# Linter choice rating
def _linter_score(r: ConventionRule) -> int:
    """Score linter choice - ruff is the modern standard."""
    linters = r.stats.get("linters", [])

    # Ruff is fastest and most comprehensive
    if "ruff" in linters:
        if "mypy" in linters or "pyright" in linters:
            return 5  # Ruff + type checker
        return 4
    # Type checker alone
    if "mypy" in linters or "pyright" in linters:
        if "flake8" in linters:
            return 4
        return 3
    # Legacy linters
    if "flake8" in linters:
        return 3
    if "pylint" in linters:
        return 3
    return 2


def _linter_reason(r: ConventionRule, _score: int) -> str:
    linters = r.stats.get("linters", [])
    if not linters:
        return "No linter configured"
    linter_details = r.stats.get("linter_details", {})
    names = [linter_details.get(l, {}).get("name", l) for l in linters]
    return f"Linters: {', '.join(names)}"


def _linter_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    linters = r.stats.get("linters", [])

    if "ruff" not in linters:
        return "Consider Ruff - it's 10-100x faster than flake8/pylint and includes isort, pyupgrade, and more."
    if "mypy" not in linters and "pyright" not in linters:
        return "Add mypy or pyright for static type checking alongside Ruff."
    return None


# Formatter choice rating
def _formatter_score(r: ConventionRule) -> int:
    """Score formatter choice - ruff format or black are the standards."""
    formatters = r.stats.get("formatters", [])
    primary = r.stats.get("primary_formatter", "")

    if primary in ("ruff", "black"):
        return 5
    if primary == "yapf":
        return 3
    if primary == "autopep8":
        return 2
    return 2


def _formatter_reason(r: ConventionRule, _score: int) -> str:
    primary = r.stats.get("primary_formatter", "none")
    formatter_names = {
        "ruff": "Ruff format",
        "black": "Black",
        "yapf": "YAPF",
        "autopep8": "autopep8",
    }
    return f"Formatter: {formatter_names.get(primary, primary)}"


def _formatter_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    primary = r.stats.get("primary_formatter", "")

    if primary in ("autopep8", "yapf"):
        return "Consider Black or Ruff format for consistent, opinionated formatting."
    if not primary:
        return "Add a code formatter (Black or Ruff) for consistent code style."
    return None


# Line length rating (opinionated for 88)
def _line_length_score(r: ConventionRule) -> int:
    """Score line length configuration - opinionated for 88 (Black default)."""
    length = r.stats.get("configured_length", 0)
    is_88 = r.stats.get("is_88", False)

    if is_88:
        return 5
    if length in (100, 120):
        return 4
    if length == 79:
        return 3  # PEP 8 strict, but less modern
    if length > 0:
        return 3
    return 2


def _line_length_reason(r: ConventionRule, _score: int) -> str:
    length = r.stats.get("configured_length", 0)
    source = r.stats.get("source", "unknown")
    return f"Line length: {length} ({source})"


def _line_length_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    length = r.stats.get("configured_length", 0)
    if length == 79:
        return "Consider 88 (Black default) for slightly more code per line while maintaining readability."
    if length > 120:
        return "Consider reducing to 88-120 for better readability."
    return "Set line-length = 88 in pyproject.toml for Black/Ruff default."


# String quotes rating (opinionated for double)
def _string_quotes_score(r: ConventionRule) -> int:
    """Score string quote style - opinionated for double quotes."""
    style = r.stats.get("configured_style", "")

    if style == "double":
        return 5
    if style == "single":
        return 4
    return 3


def _string_quotes_reason(r: ConventionRule, _score: int) -> str:
    style = r.stats.get("configured_style", "unset")
    return f"Quote style: {style}"


def _string_quotes_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    return "Use double quotes for consistency with Black/Ruff defaults and JSON."


# Test coverage threshold rating
def _coverage_threshold_score(r: ConventionRule) -> int:
    """Score test coverage threshold - opinionated for >= 80%."""
    threshold = r.stats.get("threshold", 0)

    if threshold >= 80:
        return 5
    if threshold >= 70:
        return 4
    if threshold >= 50:
        return 3
    if threshold > 0:
        return 2
    return 1


def _coverage_threshold_reason(r: ConventionRule, _score: int) -> str:
    threshold = r.stats.get("threshold", 0)
    return f"Coverage threshold: {threshold}%"


def _coverage_threshold_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    threshold = r.stats.get("threshold", 0)
    if threshold == 0:
        return "Configure fail_under in coverage.report to enforce minimum coverage."
    if threshold < 80:
        return f"Increase coverage threshold from {threshold}% to 80%+."
    return None


# Pre-commit hooks rating (opinionated for ruff + mypy)
def _pre_commit_hooks_score(r: ConventionRule) -> int:
    """Score pre-commit hooks - opinionated for ruff + type checker."""
    has_ruff = r.stats.get("has_ruff", False)
    has_type_checker = r.stats.get("has_type_checker", False)
    hooks = r.stats.get("hooks", [])

    if has_ruff and has_type_checker:
        return 5
    if has_ruff:
        return 4
    if r.stats.get("has_black") and has_type_checker:
        return 4
    if len(hooks) >= 3:
        return 3
    if len(hooks) >= 1:
        return 2
    return 1


def _pre_commit_hooks_reason(r: ConventionRule, _score: int) -> str:
    hooks = r.stats.get("hooks", [])
    return f"{len(hooks)} pre-commit hooks configured"


def _pre_commit_hooks_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    has_ruff = r.stats.get("has_ruff", False)
    has_type_checker = r.stats.get("has_type_checker", False)

    if not r.stats.get("has_pre_commit"):
        return "Add .pre-commit-config.yaml with ruff and mypy/pyright."
    if not has_ruff:
        return "Add ruff to pre-commit for fast linting and formatting."
    if not has_type_checker:
        return "Add mypy or pyright to pre-commit for type checking."
    return None


# Container local dev rating
def _container_local_dev_score(r: ConventionRule) -> int:
    """Score containerized local development setup."""
    has_compose = r.stats.get("has_compose", False)
    has_devcontainer = r.stats.get("has_devcontainer", False)

    if has_devcontainer and has_compose:
        return 5
    if has_devcontainer:
        return 4
    if has_compose:
        return 3
    return 2


def _container_local_dev_reason(r: ConventionRule, _score: int) -> str:
    has_compose = r.stats.get("has_compose", False)
    has_devcontainer = r.stats.get("has_devcontainer", False)

    if has_devcontainer and has_compose:
        return "Devcontainer + docker-compose"
    if has_devcontainer:
        return "VS Code devcontainer"
    if has_compose:
        return "Docker Compose"
    return "No containerized dev"


def _container_local_dev_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    has_compose = r.stats.get("has_compose", False)
    has_devcontainer = r.stats.get("has_devcontainer", False)

    if not has_devcontainer and not has_compose:
        return "Add docker-compose.yml for consistent local development environments."
    if has_compose and not has_devcontainer:
        return "Consider adding .devcontainer for VS Code integration."
    return None


# Async ORM rating
def _async_orm_score(r: ConventionRule) -> int:
    """Score async ORM usage - opinionated for async in async frameworks."""
    async_orm = r.stats.get("async_orm")
    is_async_framework = r.stats.get("is_async_framework", False)

    if async_orm and is_async_framework:
        return 5
    if async_orm:
        return 4
    if is_async_framework and not async_orm:
        return 3  # Mismatch - sync ORM in async framework
    return 2


def _async_orm_reason(r: ConventionRule, _score: int) -> str:
    async_orm = r.stats.get("async_orm", "none")
    orm_names = {
        "sqlalchemy_async": "SQLAlchemy AsyncIO",
        "tortoise": "Tortoise ORM",
        "databases": "encode/databases",
    }
    return f"Async ORM: {orm_names.get(async_orm, async_orm)}"


def _async_orm_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    is_async_framework = r.stats.get("is_async_framework", False)

    if is_async_framework and not r.stats.get("async_orm"):
        return "Use SQLAlchemy AsyncIO or Tortoise ORM with async frameworks for better performance."
    return None


# Data class style rating
def _data_class_style_score(r: ConventionRule) -> int:
    """Score data class style - appropriate tool per use case."""
    primary = r.stats.get("primary_style", "")
    style_counts = r.stats.get("style_counts", {})
    has_validation = r.stats.get("has_validation", False)

    # Pydantic for API + dataclasses for internal is ideal
    if "pydantic" in style_counts and "dataclass" in style_counts:
        return 5

    # Consistent modern choices
    if primary in ("pydantic", "attrs", "msgspec") and len(style_counts) == 1:
        return 5 if has_validation else 4

    # Consistent dataclass usage
    if primary == "dataclass" and len(style_counts) == 1:
        return 4

    # Mixed usage
    if len(style_counts) > 2:
        return 2

    return 3


def _data_class_style_reason(r: ConventionRule, _score: int) -> str:
    primary = r.stats.get("primary_style", "none")
    style_names = {
        "pydantic": "Pydantic",
        "dataclass": "dataclasses",
        "attrs": "attrs",
        "msgspec": "msgspec",
    }
    return f"Data class style: {style_names.get(primary, primary)}"


def _data_class_style_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    style_counts = r.stats.get("style_counts", {})

    if len(style_counts) > 2:
        return "Consolidate data class usage. Use Pydantic for API schemas, dataclasses for internal DTOs."
    return None


# Environment separation rating
def _env_separation_score(r: ConventionRule) -> int:
    """Score environment separation approach."""
    approach = r.stats.get("approach", "")
    has_env_files = r.stats.get("has_env_files", False)

    if approach == "dynaconf":
        return 5
    if approach == "pydantic_settings" and has_env_files:
        return 5
    if approach == "pydantic_settings":
        return 4
    if approach == "python_decouple":
        return 4
    if approach == "raw_environ":
        return 2
    return 2


def _env_separation_reason(r: ConventionRule, _score: int) -> str:
    approach = r.stats.get("approach", "none")
    approach_names = {
        "dynaconf": "Dynaconf",
        "pydantic_settings": "Pydantic Settings",
        "python_decouple": "python-decouple",
        "raw_environ": "os.environ",
    }
    return f"Config: {approach_names.get(approach, approach)}"


def _env_separation_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    approach = r.stats.get("approach", "")

    if approach == "raw_environ":
        return "Use Pydantic Settings or Dynaconf for type-safe, validated configuration."
    return None


# Secret management rating
def _secret_management_score(r: ConventionRule) -> int:
    """Score secret management - opinionated for managed solutions."""
    approach = r.stats.get("approach", "")
    has_production_secrets = r.stats.get("has_production_secrets", False)

    if approach in ("vault", "aws_secrets_manager", "gcp_secret_manager", "azure_keyvault"):
        return 5
    if approach == "dotenv" and has_production_secrets:
        return 4
    if approach in ("dotenv", "dotenv_file"):
        return 3
    return 2


def _secret_management_reason(r: ConventionRule, _score: int) -> str:
    approach = r.stats.get("approach", "none")
    approach_names = {
        "vault": "HashiCorp Vault",
        "aws_secrets_manager": "AWS Secrets Manager",
        "gcp_secret_manager": "GCP Secret Manager",
        "azure_keyvault": "Azure Key Vault",
        "dotenv": "python-dotenv",
        "dotenv_file": ".env file",
    }
    return f"Secrets: {approach_names.get(approach, approach)}"


def _secret_management_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    approach = r.stats.get("approach", "")

    if approach in ("dotenv", "dotenv_file"):
        return "For production, consider Vault, AWS Secrets Manager, or GCP Secret Manager."
    return "Configure secret management with python-dotenv for dev, managed service for prod."


# Exception chaining rating
def _exception_chaining_score(r: ConventionRule) -> int:
    """Score exception chaining - opinionated for chaining."""
    ratio = r.stats.get("chaining_ratio", 0)

    if ratio >= 0.8:
        return 5
    if ratio >= 0.6:
        return 4
    if ratio >= 0.4:
        return 3
    return 2


def _exception_chaining_reason(r: ConventionRule, _score: int) -> str:
    ratio = r.stats.get("chaining_ratio", 0)
    return f"Exception chaining: {ratio * 100:.0f}%"


def _exception_chaining_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    return "Use 'raise X from Y' for context or 'raise X from None' to suppress chain."


# String formatting rating
def _string_formatting_score(r: ConventionRule) -> int:
    """Score string formatting - opinionated for f-strings."""
    format_counts = r.stats.get("format_counts", {})
    total = sum(format_counts.values())
    fstring_count = format_counts.get("fstring", 0)

    if total == 0:
        return 3

    ratio = fstring_count / total
    if ratio >= 0.9:
        return 5
    if ratio >= 0.7:
        return 4
    if ratio >= 0.5:
        return 3
    return 2


def _string_formatting_reason(r: ConventionRule, _score: int) -> str:
    format_counts = r.stats.get("format_counts", {})
    total = sum(format_counts.values())
    fstring_count = format_counts.get("fstring", 0)
    ratio = fstring_count / total if total else 0
    return f"f-string usage: {ratio * 100:.0f}%"


def _string_formatting_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    return "Prefer f-strings for readability and performance over .format() or %."


# Import organization rating (enhanced)
def _import_organization_score(r: ConventionRule) -> int:
    """Score import organization - opinionated for ruff I rules with grouping."""
    primary = r.stats.get("primary_sorter", "")
    has_grouping = r.stats.get("has_grouping", False)
    profile = r.stats.get("profile")

    if primary == "ruff" and has_grouping:
        return 5
    if primary == "isort" and profile == "black" and has_grouping:
        return 5
    if primary in ("ruff", "isort"):
        return 4
    return 3


def _import_organization_reason(r: ConventionRule, _score: int) -> str:
    primary = r.stats.get("primary_sorter", "none")
    has_grouping = r.stats.get("has_grouping", False)
    result = f"Import sorting: {primary}"
    if has_grouping:
        result += " with grouping"
    return result


def _import_organization_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    has_grouping = r.stats.get("has_grouping", False)

    if not has_grouping:
        return "Configure known-first-party in ruff/isort for proper import grouping."
    return "Use Ruff I rules for fast, consistent import sorting."


# Dockerfile practices rating
def _dockerfile_score(r: ConventionRule) -> int:
    """Score Dockerfile best practices."""
    practices = r.stats.get("practices", {})
    count = r.stats.get("good_practice_count", 0)

    # Key practices
    has_multistage = practices.get("multi_stage", False)
    has_nonroot = practices.get("non_root_user", False)
    has_pinned = practices.get("pinned_version", False)

    if count >= 5:
        return 5
    if has_multistage and has_nonroot and has_pinned:
        return 5
    if count >= 3 or (has_multistage and has_nonroot):
        return 4
    if count >= 2:
        return 3
    if count >= 1:
        return 2
    return 2


def _dockerfile_reason(r: ConventionRule, _score: int) -> str:
    practices = r.stats.get("practices", {})
    good = [k for k, v in practices.items() if v]
    count = len(good)

    practice_names = {
        "multi_stage": "multi-stage",
        "non_root_user": "non-root",
        "healthcheck": "healthcheck",
        "dockerignore": ".dockerignore",
        "pinned_version": "pinned base",
        "layer_optimization": "layer caching",
    }

    if count >= 3:
        names = [practice_names.get(p, p) for p in good[:3]]
        return f"Dockerfile: {', '.join(names)}"
    return f"Dockerfile with {count}/6 best practices"


def _dockerfile_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    practices = r.stats.get("practices", {})

    missing = []
    if not practices.get("multi_stage"):
        missing.append("multi-stage builds to reduce image size")
    if not practices.get("non_root_user"):
        missing.append("non-root USER for security")
    if not practices.get("pinned_version"):
        missing.append("pinned base image version (avoid :latest)")
    if not practices.get("dockerignore"):
        missing.append(".dockerignore file")

    if missing:
        return f"Add {missing[0]}."
    return None


# Rating rules registry
RATING_RULES: dict[str, RatingRule] = {
    # Python typing and documentation
    "python.conventions.typing_coverage": RatingRule(
        score_func=_typing_score,
        reason_func=_typing_reason,
        suggestion_func=_typing_suggestion,
    ),
    "python.conventions.docstrings": RatingRule(
        score_func=_docstring_score,
        reason_func=_docstring_reason,
        suggestion_func=_docstring_suggestion,
    ),
    "python.conventions.docstring_style": RatingRule(
        score_func=_docstring_style_score,
        reason_func=_docstring_style_reason,
        suggestion_func=_docstring_style_suggestion,
    ),
    "python.conventions.naming": RatingRule(
        score_func=_naming_score,
        reason_func=_naming_reason,
        suggestion_func=_naming_suggestion,
    ),

    # Python testing
    "python.conventions.testing_framework": RatingRule(
        score_func=_testing_framework_score,
        reason_func=_testing_framework_reason,
        suggestion_func=_testing_framework_suggestion,
    ),
    "python.conventions.testing_fixtures": RatingRule(
        score_func=_testing_fixtures_score,
        reason_func=_testing_fixtures_reason,
        suggestion_func=_testing_fixtures_suggestion,
    ),
    "python.conventions.testing_mocking": RatingRule(
        score_func=_testing_mocking_score,
        reason_func=_testing_mocking_reason,
        suggestion_func=_testing_mocking_suggestion,
    ),

    # Python logging
    "python.conventions.logging_library": RatingRule(
        score_func=_logging_library_score,
        reason_func=_logging_library_reason,
        suggestion_func=_logging_library_suggestion,
    ),
    "python.conventions.logging_fields": RatingRule(
        score_func=_logging_fields_score,
        reason_func=_logging_fields_reason,
        suggestion_func=_logging_fields_suggestion,
    ),

    # Python error handling
    "python.conventions.error_handling_boundary": RatingRule(
        score_func=_error_boundary_score,
        reason_func=_error_boundary_reason,
        suggestion_func=_error_boundary_suggestion,
    ),
    "python.conventions.error_taxonomy": RatingRule(
        score_func=_error_taxonomy_score,
        reason_func=_error_taxonomy_reason,
        suggestion_func=_error_taxonomy_suggestion,
    ),
    "python.conventions.exception_handlers": RatingRule(
        score_func=_exception_handlers_score,
        reason_func=_exception_handlers_reason,
        suggestion_func=_exception_handlers_suggestion,
    ),
    "python.conventions.error_wrapper": RatingRule(
        score_func=_error_wrapper_score,
        reason_func=_error_wrapper_reason,
        suggestion_func=_error_wrapper_suggestion,
    ),
    "python.conventions.error_transformation": RatingRule(
        score_func=_error_transform_score,
        reason_func=_error_transform_reason,
        suggestion_func=_error_transform_suggestion,
    ),
    "python.conventions.error_response_pattern": RatingRule(
        score_func=_error_response_score,
        reason_func=_error_response_reason,
        suggestion_func=_error_response_suggestion,
    ),

    # Python security
    "python.conventions.raw_sql_usage": RatingRule(
        score_func=_raw_sql_score,
        reason_func=_raw_sql_reason,
        suggestion_func=_raw_sql_suggestion,
    ),
    "python.conventions.auth_pattern": RatingRule(
        score_func=_auth_pattern_score,
        reason_func=_auth_pattern_reason,
        suggestion_func=_auth_pattern_suggestion,
    ),
    "python.conventions.secrets_access_style": RatingRule(
        score_func=_secrets_style_score,
        reason_func=_secrets_style_reason,
        suggestion_func=_secrets_style_suggestion,
    ),

    # Python async/concurrency
    "python.conventions.async_style": RatingRule(
        score_func=_async_style_score,
        reason_func=_async_style_reason,
        suggestion_func=_async_style_suggestion,
    ),

    # Python architecture
    "python.conventions.layering_direction": RatingRule(
        score_func=_layering_score,
        reason_func=_layering_reason,
        suggestion_func=_layering_suggestion,
    ),
    "python.conventions.forbidden_imports": RatingRule(
        score_func=_forbidden_imports_score,
        reason_func=_forbidden_imports_reason,
        suggestion_func=_forbidden_imports_suggestion,
    ),

    # Python API/Schema
    "python.conventions.api_framework": RatingRule(
        score_func=_api_framework_score,
        reason_func=_api_framework_reason,
        suggestion_func=_api_framework_suggestion,
    ),
    "python.conventions.schema_library": RatingRule(
        score_func=_schema_library_score,
        reason_func=_schema_library_reason,
        suggestion_func=_schema_library_suggestion,
    ),

    # Python resilience
    "python.conventions.retries": RatingRule(
        score_func=_retries_score,
        reason_func=_retries_reason,
        suggestion_func=_retries_suggestion,
    ),
    "python.conventions.timeouts": RatingRule(
        score_func=_timeouts_score,
        reason_func=_timeouts_reason,
        suggestion_func=_timeouts_suggestion,
    ),
    "python.conventions.circuit_breakers": RatingRule(
        score_func=_circuit_breaker_score,
        reason_func=_circuit_breaker_reason,
        suggestion_func=_circuit_breaker_suggestion,
    ),
    "python.conventions.health_checks": RatingRule(
        score_func=_health_check_score,
        reason_func=_health_check_reason,
        suggestion_func=_health_check_suggestion,
    ),

    # Python observability
    "python.conventions.tracing": RatingRule(
        score_func=_tracing_score,
        reason_func=_tracing_reason,
        suggestion_func=_tracing_suggestion,
    ),
    "python.conventions.metrics": RatingRule(
        score_func=_metrics_score,
        reason_func=_metrics_reason,
        suggestion_func=_metrics_suggestion,
    ),
    "python.conventions.correlation_ids": RatingRule(
        score_func=_correlation_ids_score,
        reason_func=_correlation_ids_reason,
        suggestion_func=_correlation_ids_suggestion,
    ),

    # Python background tasks & caching
    "python.conventions.background_tasks": RatingRule(
        score_func=_task_queue_score,
        reason_func=_task_queue_reason,
        suggestion_func=_task_queue_suggestion,
    ),
    "python.conventions.caching": RatingRule(
        score_func=_caching_score,
        reason_func=_caching_reason,
        suggestion_func=_caching_suggestion,
    ),

    # Python database extended
    "python.conventions.db_migrations": RatingRule(
        score_func=_db_migrations_score,
        reason_func=_db_migrations_reason,
        suggestion_func=_db_migrations_suggestion,
    ),
    "python.conventions.db_connection_pooling": RatingRule(
        score_func=_db_connection_pooling_score,
        reason_func=_db_connection_pooling_reason,
        suggestion_func=_db_connection_pooling_suggestion,
    ),

    # Python security extended
    "python.conventions.rate_limiting": RatingRule(
        score_func=_rate_limiting_score,
        reason_func=_rate_limiting_reason,
        suggestion_func=_rate_limiting_suggestion,
    ),
    "python.conventions.password_hashing": RatingRule(
        score_func=_password_hashing_score,
        reason_func=_password_hashing_reason,
        suggestion_func=_password_hashing_suggestion,
    ),

    # Python API extended
    "python.conventions.api_versioning": RatingRule(
        score_func=_api_versioning_score,
        reason_func=_api_versioning_reason,
        suggestion_func=_api_versioning_suggestion,
    ),
    "python.conventions.openapi_docs": RatingRule(
        score_func=_openapi_docs_score,
        reason_func=_openapi_docs_reason,
        suggestion_func=_openapi_docs_suggestion,
    ),

    # Python messaging & async
    "python.conventions.message_broker": RatingRule(
        score_func=_message_broker_score,
        reason_func=_message_broker_reason,
        suggestion_func=_message_broker_suggestion,
    ),
    "python.conventions.async_http_client": RatingRule(
        score_func=_async_http_client_score,
        reason_func=_async_http_client_reason,
        suggestion_func=_async_http_client_suggestion,
    ),

    # Python feature flags
    "python.conventions.feature_flags": RatingRule(
        score_func=_feature_flags_score,
        reason_func=_feature_flags_reason,
        suggestion_func=_feature_flags_suggestion,
    ),

    # Python serialization & tooling
    "python.conventions.json_library": RatingRule(
        score_func=_json_library_score,
        reason_func=_json_library_reason,
        suggestion_func=_json_library_suggestion,
    ),
    "python.conventions.type_checker_strictness": RatingRule(
        score_func=_type_checker_strictness_score,
        reason_func=_type_checker_strictness_reason,
        suggestion_func=_type_checker_strictness_suggestion,
    ),
    "python.conventions.lock_file": RatingRule(
        score_func=_lock_file_score,
        reason_func=_lock_file_reason,
        suggestion_func=_lock_file_suggestion,
    ),
    "python.conventions.linter": RatingRule(
        score_func=_linter_score,
        reason_func=_linter_reason,
        suggestion_func=_linter_suggestion,
    ),
    "python.conventions.formatter": RatingRule(
        score_func=_formatter_score,
        reason_func=_formatter_reason,
        suggestion_func=_formatter_suggestion,
    ),

    # Python new tooling conventions
    "python.conventions.line_length": RatingRule(
        score_func=_line_length_score,
        reason_func=_line_length_reason,
        suggestion_func=_line_length_suggestion,
    ),
    "python.conventions.string_quotes": RatingRule(
        score_func=_string_quotes_score,
        reason_func=_string_quotes_reason,
        suggestion_func=_string_quotes_suggestion,
    ),
    "python.conventions.pre_commit_hooks": RatingRule(
        score_func=_pre_commit_hooks_score,
        reason_func=_pre_commit_hooks_reason,
        suggestion_func=_pre_commit_hooks_suggestion,
    ),
    "python.conventions.import_sorting": RatingRule(
        score_func=_import_organization_score,
        reason_func=_import_organization_reason,
        suggestion_func=_import_organization_suggestion,
    ),

    # Python testing new
    "python.conventions.test_coverage_threshold": RatingRule(
        score_func=_coverage_threshold_score,
        reason_func=_coverage_threshold_reason,
        suggestion_func=_coverage_threshold_suggestion,
    ),

    # Python database new
    "python.conventions.async_orm": RatingRule(
        score_func=_async_orm_score,
        reason_func=_async_orm_reason,
        suggestion_func=_async_orm_suggestion,
    ),

    # Python API new
    "python.conventions.data_class_style": RatingRule(
        score_func=_data_class_style_score,
        reason_func=_data_class_style_reason,
        suggestion_func=_data_class_style_suggestion,
    ),

    # Python security new
    "python.conventions.env_separation": RatingRule(
        score_func=_env_separation_score,
        reason_func=_env_separation_reason,
        suggestion_func=_env_separation_suggestion,
    ),
    "python.conventions.secret_management": RatingRule(
        score_func=_secret_management_score,
        reason_func=_secret_management_reason,
        suggestion_func=_secret_management_suggestion,
    ),

    # Python architecture new
    "python.conventions.container_local_dev": RatingRule(
        score_func=_container_local_dev_score,
        reason_func=_container_local_dev_reason,
        suggestion_func=_container_local_dev_suggestion,
    ),

    # Python error handling new
    "python.conventions.exception_chaining": RatingRule(
        score_func=_exception_chaining_score,
        reason_func=_exception_chaining_reason,
        suggestion_func=_exception_chaining_suggestion,
    ),

    # Python code style
    "python.conventions.string_formatting": RatingRule(
        score_func=_string_formatting_score,
        reason_func=_string_formatting_reason,
        suggestion_func=_string_formatting_suggestion,
    ),

    # Generic containerization
    "generic.conventions.dockerfile": RatingRule(
        score_func=_dockerfile_score,
        reason_func=_dockerfile_reason,
        suggestion_func=_dockerfile_suggestion,
    ),

    # ============================================
    # Go conventions
    # ============================================

    # Go documentation
    "go.conventions.doc_comments": RatingRule(
        score_func=lambda r: (
            5 if _get_stat(r, "doc_ratio", 0) >= 0.8 else
            4 if _get_stat(r, "doc_ratio", 0) >= 0.6 else
            3 if _get_stat(r, "doc_ratio", 0) >= 0.4 else
            2 if _get_stat(r, "doc_ratio", 0) >= 0.2 else 1
        ),
        reason_func=lambda r, _: f"Doc comment coverage is {_get_stat(r, 'doc_ratio', 0) * 100:.0f}%",
        suggestion_func=lambda r, s: None if s >= 5 else "Add doc comments to exported functions following Go conventions (// FunctionName ...).",
    ),
    "go.conventions.example_tests": RatingRule(
        score_func=lambda r: min(5, 3 + r.stats.get("example_count", 0) // 3),
        reason_func=lambda r, _: f"Found {r.stats.get('example_count', 0)} Example test functions",
        suggestion_func=lambda r, s: None if s >= 5 else "Add Example functions to document API usage in godoc.",
    ),

    # Go testing
    "go.conventions.table_driven_tests": RatingRule(
        score_func=lambda r: min(5, 3 + r.stats.get("table_test_count", 0) // 5),
        reason_func=lambda r, _: f"Found {r.stats.get('table_test_count', 0)} table-driven tests",
        suggestion_func=lambda r, s: None if s >= 5 else "Expand use of table-driven tests for comprehensive test coverage.",
    ),
    "go.conventions.test_helpers": RatingRule(
        score_func=lambda r: min(5, 3 + r.stats.get("helper_count", 0) // 3),
        reason_func=lambda r, _: f"Found {r.stats.get('helper_count', 0)} test helper functions using t.Helper()",
        suggestion_func=lambda r, s: None if s >= 5 else "Add t.Helper() to test helper functions for better failure messages.",
    ),
    "go.conventions.subtests": RatingRule(
        score_func=lambda r: min(5, 3 + r.stats.get("subtest_count", 0) // 10),
        reason_func=lambda r, _: f"Found {r.stats.get('subtest_count', 0)} t.Run() subtest calls",
        suggestion_func=lambda r, s: None if s >= 5 else "Use t.Run() subtests for better test organization and parallel execution.",
    ),
    "go.conventions.testing_framework": RatingRule(
        score_func=lambda r: 5 if r.stats.get("primary_framework") in ("testify", "gomega") else 4,
        reason_func=lambda r, _: f"Uses {r.stats.get('primary_framework', 'unknown')} testing framework",
        suggestion_func=lambda r, s: None if s >= 5 else "Consider using testify for assertions and mocking.",
    ),

    # Go logging
    "go.conventions.logging_library": RatingRule(
        score_func=lambda r: (
            5 if r.stats.get("primary_library") in ("zap", "zerolog", "slog") else
            4 if r.stats.get("primary_library") == "logrus" else
            2 if r.stats.get("primary_library") == "log" else 3
        ),
        reason_func=lambda r, _: f"Uses {r.stats.get('primary_library', 'unknown')} for logging",
        suggestion_func=lambda r, s: None if s >= 5 else "Consider using zap, zerolog, or slog for structured logging.",
    ),
    "go.conventions.structured_logging": RatingRule(
        score_func=lambda r: (
            5 if _get_stat(r, "structured_ratio", 0) >= 0.8 else
            4 if _get_stat(r, "structured_ratio", 0) >= 0.6 else
            3 if _get_stat(r, "structured_ratio", 0) >= 0.4 else 2
        ),
        reason_func=lambda r, _: f"Structured logging ratio is {_get_stat(r, 'structured_ratio', 0) * 100:.0f}%",
        suggestion_func=lambda r, s: None if s >= 5 else "Use structured logging with key-value pairs for better log analysis.",
    ),

    # Go error handling
    "go.conventions.error_types": RatingRule(
        score_func=lambda r: min(5, 3 + r.stats.get("custom_error_count", 0) // 3),
        reason_func=lambda r, _: f"Found {r.stats.get('custom_error_count', 0)} custom error types",
        suggestion_func=lambda r, s: None if s >= 5 else "Define custom error types for domain-specific errors.",
    ),
    "go.conventions.sentinel_errors": RatingRule(
        score_func=lambda r: min(5, 3 + r.stats.get("sentinel_count", 0) // 3),
        reason_func=lambda r, _: f"Found {r.stats.get('sentinel_count', 0)} sentinel errors (var ErrX = ...)",
        suggestion_func=lambda r, s: None if s >= 5 else "Use sentinel errors for expected error conditions.",
    ),
    "go.conventions.error_wrapping": RatingRule(
        score_func=lambda r: min(5, 3 + (r.stats.get("is_as_count", 0) + r.stats.get("wrap_count", 0)) // 5),
        reason_func=lambda r, _: f"Uses errors.Is/As: {r.stats.get('is_as_count', 0)}, %%w wrapping: {r.stats.get('wrap_count', 0)}",
        suggestion_func=lambda r, s: None if s >= 5 else "Use fmt.Errorf with %w and errors.Is/As for error chain inspection.",
    ),

    # Go security
    "go.conventions.sql_injection": RatingRule(
        score_func=lambda r: (
            5 if _get_stat(r, "safe_ratio", 1) >= 0.95 else
            4 if _get_stat(r, "safe_ratio", 1) >= 0.8 else
            3 if _get_stat(r, "safe_ratio", 1) >= 0.5 else 2
        ),
        reason_func=lambda r, _: f"Parameterized queries: {_get_stat(r, 'safe_ratio', 0) * 100:.0f}%",
        suggestion_func=lambda r, s: None if s >= 5 else "Replace string concatenation in SQL with parameterized queries.",
    ),
    "go.conventions.secrets_config": RatingRule(
        score_func=lambda r: 5 if r.stats.get("config_library") in ("viper", "envconfig", "koanf") else 3,
        reason_func=lambda r, _: f"Uses {r.stats.get('config_library', 'os.Getenv')} for configuration",
        suggestion_func=lambda r, s: None if s >= 5 else "Use a config library like Viper or envconfig for type-safe configuration.",
    ),
    "go.conventions.input_validation": RatingRule(
        score_func=lambda r: 5 if r.stats.get("validation_library") else 3,
        reason_func=lambda r, _: f"Uses {r.stats.get('validation_library', 'no library')} for validation",
        suggestion_func=lambda r, s: None if s >= 5 else "Use go-playground/validator for struct validation.",
    ),

    # Go concurrency
    "go.conventions.goroutine_patterns": RatingRule(
        score_func=lambda r: 5 if r.stats.get("uses_errgroup") else min(4, 3 + r.stats.get("goroutine_count", 0) // 10),
        reason_func=lambda r, _: f"Found {r.stats.get('goroutine_count', 0)} goroutines" + (" with errgroup" if r.stats.get("uses_errgroup") else ""),
        suggestion_func=lambda r, s: None if s >= 5 else "Use errgroup for goroutine error handling and cancellation.",
    ),
    "go.conventions.channel_usage": RatingRule(
        score_func=lambda r: min(5, 3 + (r.stats.get("channel_creation_count", 0) + r.stats.get("select_count", 0)) // 5),
        reason_func=lambda r, _: f"Channels: {r.stats.get('channel_creation_count', 0)}, select: {r.stats.get('select_count', 0)}",
        suggestion_func=lambda r, s: None if s >= 4 else "Use channels and select for goroutine coordination.",
    ),
    "go.conventions.context_usage": RatingRule(
        score_func=lambda r: min(5, 3 + r.stats.get("ctx_param_count", 0) // 10),
        reason_func=lambda r, _: f"Found {r.stats.get('ctx_param_count', 0)} functions with context.Context parameter",
        suggestion_func=lambda r, s: None if s >= 5 else "Propagate context.Context through function calls for cancellation and deadlines.",
    ),
    "go.conventions.sync_primitives": RatingRule(
        score_func=lambda r: min(5, 3 + (r.stats.get("mutex_count", 0) + r.stats.get("waitgroup_count", 0)) // 5),
        reason_func=lambda r, _: f"Mutex: {r.stats.get('mutex_count', 0)}, WaitGroup: {r.stats.get('waitgroup_count', 0)}",
        suggestion_func=lambda r, s: None if s >= 4 else "Use sync primitives appropriately for shared state protection.",
    ),

    # Go architecture
    "go.conventions.package_structure": RatingRule(
        score_func=lambda r: (
            5 if r.stats.get("has_cmd") and r.stats.get("has_internal") else
            4 if r.stats.get("has_internal") else
            3 if r.stats.get("has_cmd") or r.stats.get("has_pkg") else 2
        ),
        reason_func=lambda r, _: f"Uses {'cmd/, ' if r.stats.get('has_cmd') else ''}{'internal/, ' if r.stats.get('has_internal') else ''}{'pkg/' if r.stats.get('has_pkg') else ''}".rstrip(", ") or "flat structure",
        suggestion_func=lambda r, s: None if s >= 5 else "Adopt standard Go project layout with cmd/, internal/, pkg/ directories.",
    ),
    "go.conventions.interface_segregation": RatingRule(
        score_func=lambda r: (
            5 if _get_stat(r, "small_ratio", 0) >= 0.8 else
            4 if _get_stat(r, "small_ratio", 0) >= 0.6 else
            3 if _get_stat(r, "small_ratio", 0) >= 0.4 else 2
        ),
        reason_func=lambda r, _: f"Small interfaces (≤3 methods): {_get_stat(r, 'small_ratio', 0) * 100:.0f}%",
        suggestion_func=lambda r, s: None if s >= 5 else "Prefer small, focused interfaces (Interface Segregation Principle).",
    ),
    "go.conventions.dependency_direction": RatingRule(
        score_func=lambda r: 5 if r.stats.get("internal_imports_cmd", 0) == 0 and r.stats.get("pkg_imports_internal", 0) == 0 else 2,
        reason_func=lambda r, _: "Clean dependency direction" if r.stats.get("internal_imports_cmd", 0) == 0 else f"Violations: {r.stats.get('internal_imports_cmd', 0) + r.stats.get('pkg_imports_internal', 0)}",
        suggestion_func=lambda r, s: None if s >= 5 else "Fix dependency direction: internal/ should not import from cmd/, pkg/ should not import from internal/.",
    ),

    # Go API
    "go.conventions.http_framework": RatingRule(
        score_func=lambda r: 5 if r.stats.get("primary_framework") in ("gin", "echo", "chi", "fiber") else 4 if r.stats.get("primary_framework") == "gorilla" else 3,
        reason_func=lambda r, _: f"Uses {r.stats.get('primary_framework', 'unknown')} HTTP framework",
        suggestion_func=lambda r, s: None if s >= 4 else "Consider using a popular HTTP framework like Gin, Echo, or Chi.",
    ),
    "go.conventions.http_middleware": RatingRule(
        score_func=lambda r: min(5, 3 + (r.stats.get("handler_middleware_count", 0) + r.stats.get("use_calls", 0)) // 5),
        reason_func=lambda r, _: f"Found {r.stats.get('handler_middleware_count', 0) + r.stats.get('gin_middleware_count', 0)} middleware functions",
        suggestion_func=lambda r, s: None if s >= 4 else "Use middleware for cross-cutting concerns like auth, logging, and CORS.",
    ),
    "go.conventions.response_patterns": RatingRule(
        score_func=lambda r: min(5, 3 + (r.stats.get("json_marshal_count", 0) + r.stats.get("gin_json_count", 0)) // 10),
        reason_func=lambda r, _: f"JSON responses: {r.stats.get('json_marshal_count', 0) + r.stats.get('gin_json_count', 0) + r.stats.get('echo_json_count', 0)}",
        suggestion_func=lambda r, s: None if s >= 4 else "Use consistent JSON response patterns.",
    ),

    # Go patterns
    "go.conventions.options_pattern": RatingRule(
        score_func=lambda r: min(5, 3 + r.stats.get("with_func_count", 0) // 5),
        reason_func=lambda r, _: f"Found {r.stats.get('with_func_count', 0)} functional option functions",
        suggestion_func=lambda r, s: None if s >= 4 else "Use functional options for flexible, extensible configuration.",
    ),
    "go.conventions.builder_pattern": RatingRule(
        score_func=lambda r: min(5, 3 + r.stats.get("builder_method_count", 0) // 5),
        reason_func=lambda r, _: f"Found {r.stats.get('builder_method_count', 0)} builder chain methods",
        suggestion_func=lambda r, s: None if s >= 4 else "Use builder pattern for complex object construction.",
    ),
    "go.conventions.repository_pattern": RatingRule(
        score_func=lambda r: min(5, 3 + (r.stats.get("repo_interface_count", 0) + r.stats.get("repo_struct_count", 0)) // 3),
        reason_func=lambda r, _: f"Found {r.stats.get('repo_interface_count', 0)} repo interfaces, {r.stats.get('repo_struct_count', 0)} implementations",
        suggestion_func=lambda r, s: None if s >= 4 else "Use repository pattern with interfaces for testable data access.",
    ),

    # ============================================
    # Node.js conventions
    # ============================================

    # Node TypeScript
    "node.conventions.strict_mode": RatingRule(
        score_func=lambda r: 5 if r.stats.get("has_strict") else 3 if r.stats.get("has_strict_null_checks") or r.stats.get("has_no_implicit_any") else 2,
        reason_func=lambda r, _: "TypeScript strict mode " + ("enabled" if r.stats.get("has_strict") else "partially enabled" if r.stats.get("has_strict_null_checks") else "disabled"),
        suggestion_func=lambda r, s: None if s >= 5 else "Enable 'strict: true' in tsconfig.json for better type safety.",
    ),
    "node.conventions.type_coverage": RatingRule(
        score_func=lambda r: (
            5 if _get_stat(r, "any_ratio", 1) <= 0.05 else
            4 if _get_stat(r, "any_ratio", 1) <= 0.15 else
            3 if _get_stat(r, "any_ratio", 1) <= 0.3 else 2
        ),
        reason_func=lambda r, _: f"'any' usage ratio: {_get_stat(r, 'any_ratio', 0) * 100:.0f}%",
        suggestion_func=lambda r, s: None if s >= 5 else "Reduce 'any' usage by adding proper type annotations.",
    ),

    # Node documentation
    "node.conventions.jsdoc": RatingRule(
        score_func=lambda r: (
            5 if _get_stat(r, "jsdoc_ratio", 0) >= 0.5 and r.stats.get("param_tags", 0) >= 10 else
            4 if _get_stat(r, "jsdoc_ratio", 0) >= 0.3 else
            3 if r.stats.get("jsdoc_count", 0) >= 10 else 2
        ),
        reason_func=lambda r, _: f"JSDoc coverage: {r.stats.get('jsdoc_count', 0)} blocks, {r.stats.get('param_tags', 0)} @param tags",
        suggestion_func=lambda r, s: None if s >= 5 else "Add JSDoc comments with @param and @returns for better documentation.",
    ),

    # Node testing
    "node.conventions.test_patterns": RatingRule(
        score_func=lambda r: min(5, 3 + r.stats.get("describe_count", 0) // 5),
        reason_func=lambda r, _: f"Found {r.stats.get('describe_count', 0)} describe blocks, {r.stats.get('it_test_count', 0)} test cases",
        suggestion_func=lambda r, s: None if s >= 4 else "Use describe/it blocks for organized test structure.",
    ),
    "node.conventions.mocking": RatingRule(
        score_func=lambda r: 5 if r.stats.get("primary_library") in ("jest_mock", "sinon") else 4 if r.stats.get("mock_library_counts") else 3,
        reason_func=lambda r, _: f"Uses {r.stats.get('primary_library', 'no')} mocking",
        suggestion_func=lambda r, s: None if s >= 4 else "Use Jest mocks or Sinon for comprehensive test mocking.",
    ),
    "node.conventions.coverage_config": RatingRule(
        score_func=lambda r: 5 if r.stats.get("coverage_tools") else 3,
        reason_func=lambda r, _: f"Coverage tools: {', '.join(r.stats.get('coverage_tools', [])) or 'not configured'}",
        suggestion_func=lambda r, s: None if s >= 5 else "Configure test coverage with Jest or c8.",
    ),

    # Node logging
    "node.conventions.logging_library": RatingRule(
        score_func=lambda r: 5 if r.stats.get("primary_library") in ("pino", "winston") else 4 if r.stats.get("primary_library") else 2,
        reason_func=lambda r, _: f"Uses {r.stats.get('primary_library', 'console.log')} for logging",
        suggestion_func=lambda r, s: None if s >= 5 else "Use Pino or Winston for structured logging.",
    ),
    "node.conventions.structured_logging": RatingRule(
        score_func=lambda r: (
            5 if _get_stat(r, "console_ratio", 1) <= 0.1 else
            4 if _get_stat(r, "console_ratio", 1) <= 0.3 else
            3 if r.stats.get("logger_count", 0) > 0 else 2
        ),
        reason_func=lambda r, _: f"Logger: {r.stats.get('logger_count', 0)}, console: {r.stats.get('console_count', 0)}",
        suggestion_func=lambda r, s: None if s >= 5 else "Replace console.log with a dedicated logger for production.",
    ),

    # Node error handling
    "node.conventions.error_classes": RatingRule(
        score_func=lambda r: min(5, 3 + r.stats.get("custom_error_count", 0) // 2),
        reason_func=lambda r, _: f"Found {r.stats.get('custom_error_count', 0)} custom Error classes",
        suggestion_func=lambda r, s: None if s >= 4 else "Define custom Error classes for domain-specific errors.",
    ),
    "node.conventions.async_error_handling": RatingRule(
        score_func=lambda r: min(5, 3 + (r.stats.get("try_catch_count", 0) + r.stats.get("catch_chain_count", 0)) // 10),
        reason_func=lambda r, _: f"try/catch: {r.stats.get('try_catch_count', 0)}, .catch(): {r.stats.get('catch_chain_count', 0)}",
        suggestion_func=lambda r, s: None if s >= 4 else "Ensure async functions have proper error handling with try/catch.",
    ),
    "node.conventions.error_middleware": RatingRule(
        score_func=lambda r: 5 if r.stats.get("express_error_handlers", 0) > 0 or r.stats.get("fastify_error_handlers", 0) > 0 else 2,
        reason_func=lambda r, _: f"Express error handlers: {r.stats.get('express_error_handlers', 0)}, Fastify: {r.stats.get('fastify_error_handlers', 0)}",
        suggestion_func=lambda r, s: None if s >= 5 else "Add centralized error middleware for consistent error responses.",
    ),

    # Node security
    "node.conventions.sql_injection": RatingRule(
        score_func=lambda r: 5 if r.stats.get("orm_usage") else 4 if r.stats.get("parameterized_count", 0) > r.stats.get("raw_query_count", 0) else 2,
        reason_func=lambda r, _: "Uses ORM" if r.stats.get("orm_usage") else f"Raw: {r.stats.get('raw_query_count', 0)}, Parameterized: {r.stats.get('parameterized_count', 0)}",
        suggestion_func=lambda r, s: None if s >= 5 else "Use an ORM or parameterized queries to prevent SQL injection.",
    ),
    "node.conventions.env_config": RatingRule(
        score_func=lambda r: 5 if r.stats.get("config_library") in ("dotenv", "config", "convict", "envalid") else 3,
        reason_func=lambda r, _: f"Uses {r.stats.get('config_library', 'process.env')} for configuration",
        suggestion_func=lambda r, s: None if s >= 5 else "Use dotenv or a config library for environment management.",
    ),
    "node.conventions.input_validation": RatingRule(
        score_func=lambda r: 5 if r.stats.get("validation_library") in ("zod", "joi", "yup") else 4 if r.stats.get("validation_library") else 2,
        reason_func=lambda r, _: f"Uses {r.stats.get('validation_library', 'no library')} for validation",
        suggestion_func=lambda r, s: None if s >= 5 else "Use Zod, Joi, or Yup for input validation.",
    ),
    "node.conventions.helmet_security": RatingRule(
        score_func=lambda r: min(5, 3 + len(r.stats.get("security_libraries", []))),
        reason_func=lambda r, _: f"Security middleware: {', '.join(r.stats.get('security_libraries', [])) or 'none'}",
        suggestion_func=lambda r, s: None if s >= 4 else "Use helmet and cors middleware for HTTP security headers.",
    ),

    # Node async patterns
    "node.conventions.async_style": RatingRule(
        score_func=lambda r: (
            5 if _get_stat(r, "async_ratio", 0) >= 0.7 else
            4 if _get_stat(r, "async_ratio", 0) >= 0.4 else
            3 if r.stats.get("async_await_count", 0) > 0 else 2
        ),
        reason_func=lambda r, _: f"async/await: {r.stats.get('async_await_count', 0)}, .then(): {r.stats.get('then_chain_count', 0)}, callbacks: {r.stats.get('callback_count', 0)}",
        suggestion_func=lambda r, s: None if s >= 5 else "Prefer async/await over callbacks and .then() chains.",
    ),
    "node.conventions.promise_patterns": RatingRule(
        score_func=lambda r: min(5, 3 + (r.stats.get("promise_all_count", 0) + r.stats.get("promise_all_settled_count", 0)) // 3),
        reason_func=lambda r, _: f"Promise.all: {r.stats.get('promise_all_count', 0)}, allSettled: {r.stats.get('promise_all_settled_count', 0)}",
        suggestion_func=lambda r, s: None if s >= 4 else "Use Promise.all/allSettled for concurrent async operations.",
    ),

    # Node architecture
    "node.conventions.project_structure": RatingRule(
        score_func=lambda r: min(5, 2 + len(r.stats.get("directories", []))),
        reason_func=lambda r, _: f"Organized with: {', '.join(r.stats.get('directories', [])) or 'flat structure'}",
        suggestion_func=lambda r, s: None if s >= 4 else "Organize code into src/, routes/, services/, models/ directories.",
    ),
    "node.conventions.layer_separation": RatingRule(
        score_func=lambda r: 5 if r.stats.get("layer_count", 0) >= 3 else 4 if r.stats.get("layer_count", 0) >= 2 else 3,
        reason_func=lambda r, _: f"Layer separation: API ({r.stats.get('api_files', 0)}), Service ({r.stats.get('service_files', 0)}), DB ({r.stats.get('db_files', 0)})",
        suggestion_func=lambda r, s: None if s >= 5 else "Separate code into API, service, and data access layers.",
    ),
    "node.conventions.barrel_exports": RatingRule(
        score_func=lambda r: min(5, 3 + r.stats.get("barrel_files", 0) // 3),
        reason_func=lambda r, _: f"Found {r.stats.get('barrel_files', 0)} barrel export files (index.ts)",
        suggestion_func=lambda r, s: None if s >= 4 else "Use barrel exports (index.ts) for cleaner imports.",
    ),

    # Node API
    "node.conventions.middleware_patterns": RatingRule(
        score_func=lambda r: min(5, 3 + (r.stats.get("use_calls", 0) + r.stats.get("middleware_functions", 0)) // 5),
        reason_func=lambda r, _: f".use() calls: {r.stats.get('use_calls', 0)}, middleware functions: {r.stats.get('middleware_functions', 0)}",
        suggestion_func=lambda r, s: None if s >= 4 else "Use middleware for cross-cutting concerns.",
    ),
    "node.conventions.route_organization": RatingRule(
        score_func=lambda r: min(5, 3 + r.stats.get("route_file_count", 0) // 3),
        reason_func=lambda r, _: f"Found {r.stats.get('route_file_count', 0)} route files, {r.stats.get('route_handlers', 0)} handlers",
        suggestion_func=lambda r, s: None if s >= 4 else "Organize routes into separate files by resource/domain.",
    ),
    "node.conventions.response_patterns": RatingRule(
        score_func=lambda r: (
            5 if _get_stat(r, "json_ratio", 0) >= 0.9 else
            4 if _get_stat(r, "json_ratio", 0) >= 0.7 else 3
        ),
        reason_func=lambda r, _: f"res.json(): {r.stats.get('res_json_count', 0)}, res.send(): {r.stats.get('res_send_count', 0)}",
        suggestion_func=lambda r, s: None if s >= 5 else "Use res.json() consistently for API responses.",
    ),

    # Node patterns
    "node.conventions.dependency_injection": RatingRule(
        score_func=lambda r: 5 if r.stats.get("di_library") in ("tsyringe", "inversify", "nestjs", "awilix") else 3,
        reason_func=lambda r, _: f"Uses {r.stats.get('di_library', 'no DI library')} for dependency injection",
        suggestion_func=lambda r, s: None if s >= 5 else "Consider using a DI container for better testability.",
    ),
    "node.conventions.repository_pattern": RatingRule(
        score_func=lambda r: min(5, 3 + r.stats.get("repository_count", 0) // 2),
        reason_func=lambda r, _: f"Found {r.stats.get('repository_count', 0)} repository classes/interfaces",
        suggestion_func=lambda r, s: None if s >= 4 else "Use repository pattern for data access abstraction.",
    ),
    "node.conventions.singleton_pattern": RatingRule(
        score_func=lambda r: min(5, 3 + (r.stats.get("module_singleton_count", 0) + r.stats.get("get_instance_count", 0)) // 3),
        reason_func=lambda r, _: f"Module singletons: {r.stats.get('module_singleton_count', 0)}, getInstance: {r.stats.get('get_instance_count', 0)}",
        suggestion_func=lambda r, s: None if s >= 4 else "Use module-level singletons for shared services.",
    ),

    # ============================================
    # Generic (cross-language) conventions
    # ============================================

    # CI/CD
    "generic.conventions.ci_cd_platform": RatingRule(
        score_func=lambda r: 5 if r.stats.get("ci_features", {}).get("testing") and r.stats.get("ci_features", {}).get("linting") else 4 if r.stats.get("primary_platform") else 3,
        reason_func=lambda r, _: f"Uses {r.stats.get('primary_platform', 'unknown')} for CI/CD",
        suggestion_func=lambda r, s: None if s >= 5 else "Ensure CI/CD pipeline includes testing and linting.",
    ),
    "generic.conventions.ci_cd_quality": RatingRule(
        score_func=lambda r: min(5, 2 + len([k for k, v in r.stats.get("ci_features", {}).items() if v])),
        reason_func=lambda r, _: f"CI features: {', '.join(k for k, v in r.stats.get('ci_features', {}).items() if v) or 'minimal'}",
        suggestion_func=lambda r, s: None if s >= 5 else "Add caching, matrix builds, and deployment stages to CI.",
    ),

    # Git conventions
    "generic.conventions.commit_style": RatingRule(
        score_func=lambda r: 5 if r.stats.get("conventional_commits_ratio", 0) >= 0.8 else 4 if r.stats.get("conventional_commits_ratio", 0) >= 0.5 else 3,
        reason_func=lambda r, _: f"Conventional commits: {r.stats.get('conventional_commits_ratio', 0) * 100:.0f}%",
        suggestion_func=lambda r, s: None if s >= 5 else "Adopt Conventional Commits format for better changelog generation.",
    ),
    "generic.conventions.branch_naming": RatingRule(
        score_func=lambda r: 5 if r.stats.get("branch_convention") in ("gitflow", "trunk_based") else 4 if r.stats.get("branch_convention") else 3,
        reason_func=lambda r, _: f"Branch naming: {r.stats.get('branch_convention', 'unstructured')}",
        suggestion_func=lambda r, s: None if s >= 5 else "Adopt consistent branch naming (feature/, fix/, etc.).",
    ),
    "generic.conventions.git_hooks": RatingRule(
        score_func=lambda r: 5 if (r.stats.get("hook_tool") or r.stats.get("hooks_tools", [None])[0]) in ("pre-commit", "husky", "lefthook", "Husky", "Lefthook") else 3,
        reason_func=lambda r, _: f"Git hooks: {r.stats.get('hook_tool') or (r.stats.get('hooks_tools', ['none configured'])[0] if r.stats.get('hooks_tools') else 'none configured')}",
        suggestion_func=lambda r, s: None if s >= 5 else "Configure pre-commit hooks for automated quality checks.",
    ),

    # Dependency updates
    "generic.conventions.dependency_updates": RatingRule(
        score_func=lambda r: 5 if r.stats.get("primary_tool") in ("renovate", "dependabot") else 3,
        reason_func=lambda r, _: f"Dependency updates: {r.stats.get('primary_tool', 'not configured')}",
        suggestion_func=lambda r, s: None if s >= 5 else "Configure Dependabot or Renovate for automated dependency updates.",
    ),

    # API documentation
    "generic.conventions.api_documentation": RatingRule(
        score_func=lambda r: min(5, 3 + len(r.stats.get("formats", []))),
        reason_func=lambda r, _: f"API docs: {', '.join(r.stats.get('formats', [])) or 'none'}",
        suggestion_func=lambda r, s: None if s >= 4 else "Add OpenAPI/Swagger documentation for your API.",
    ),

    # Containerization
    "generic.conventions.dockerfile_practices": RatingRule(
        score_func=lambda r: min(5, 2 + len([k for k, v in r.stats.get("best_practices", {}).items() if v])),
        reason_func=lambda r, _: f"Dockerfile practices: {len([k for k, v in r.stats.get('best_practices', {}).items() if v])}/5",
        suggestion_func=lambda r, s: None if s >= 5 else "Apply Dockerfile best practices: multi-stage, non-root user, health checks.",
    ),
    "generic.conventions.docker_compose": RatingRule(
        score_func=lambda r: min(5, 3 + r.stats.get("service_count", 0) // 2),
        reason_func=lambda r, _: f"Docker Compose with {r.stats.get('service_count', 0)} service(s)",
        suggestion_func=lambda r, s: None if s >= 4 else "Use Docker Compose for local development orchestration.",
    ),
    "generic.conventions.kubernetes": RatingRule(
        score_func=lambda r: 5 if r.stats.get("uses_helm") or r.stats.get("uses_kustomize") else 4 if r.stats.get("manifest_count", 0) > 0 else 3,
        reason_func=lambda r, _: f"Kubernetes: {r.stats.get('manifest_count', 0)} manifests" + (" with Helm" if r.stats.get("uses_helm") else " with Kustomize" if r.stats.get("uses_kustomize") else ""),
        suggestion_func=lambda r, s: None if s >= 5 else "Use Helm or Kustomize for Kubernetes configuration management.",
    ),

    # Editor config
    "generic.conventions.editor_config": RatingRule(
        score_func=lambda r: min(5, 2 + len(r.stats.get("config_types", []))),
        reason_func=lambda r, _: f"Editor config: {', '.join(r.stats.get('config_types', [])) or 'none'}",
        suggestion_func=lambda r, s: None if s >= 4 else "Add .editorconfig for consistent formatting across editors.",
    ),

    # ============================================
    # New Python conventions
    # ============================================

    # Python dependency management
    "python.conventions.dependency_management": RatingRule(
        score_func=lambda r: 5 if r.stats.get("primary_tool") in ("poetry", "uv", "pdm") else 4 if r.stats.get("primary_tool") else 3,
        reason_func=lambda r, _: f"Dependencies: {r.stats.get('primary_tool', 'pip')}",
        suggestion_func=lambda r, s: None if s >= 5 else "Consider Poetry, uv, or PDM for modern dependency management.",
    ),

    # Python CLI
    "python.conventions.cli_framework": RatingRule(
        score_func=lambda r: 5 if r.stats.get("primary_framework") in ("typer", "click") else 4 if r.stats.get("primary_framework") else 3,
        reason_func=lambda r, _: f"CLI framework: {r.stats.get('primary_framework', 'none')}",
        suggestion_func=lambda r, s: None if s >= 5 else "Use Typer or Click for building CLI applications.",
    ),

    # Python GraphQL
    "python.conventions.graphql": RatingRule(
        score_func=lambda r: 5 if r.stats.get("primary_library") in ("strawberry", "graphene") else 4 if r.stats.get("primary_library") else 3,
        reason_func=lambda r, _: f"GraphQL: {r.stats.get('primary_library', 'none')}",
        suggestion_func=lambda r, s: None if s >= 5 else "Use Strawberry for type-safe GraphQL with Python.",
    ),

    # ============================================
    # New Go conventions
    # ============================================

    # Go modules
    "go.conventions.modules": RatingRule(
        score_func=lambda r: 5 if r.stats.get("go_version", "").startswith("1.2") else 4 if r.stats.get("has_gomod") else 2,
        reason_func=lambda r, _: f"Go {r.stats.get('go_version', 'unknown')}, {r.stats.get('dependency_count', 0)} dependencies",
        suggestion_func=lambda r, s: None if s >= 5 else "Keep Go version up to date in go.mod.",
    ),

    # Go CLI
    "go.conventions.cli_framework": RatingRule(
        score_func=lambda r: 5 if r.stats.get("primary_framework") == "cobra" else 4 if r.stats.get("primary_framework") in ("urfave", "kong") else 3,
        reason_func=lambda r, _: f"CLI framework: {r.stats.get('primary_framework', 'none')}",
        suggestion_func=lambda r, s: None if s >= 5 else "Use Cobra for building CLI applications.",
    ),

    # Go migrations
    "go.conventions.migrations": RatingRule(
        score_func=lambda r: 5 if r.stats.get("primary_tool") in ("golang_migrate", "goose", "atlas") else 4 if r.stats.get("migration_file_count", 0) > 0 else 3,
        reason_func=lambda r, _: f"Migrations: {r.stats.get('primary_tool', 'none')}, {r.stats.get('migration_file_count', 0)} files",
        suggestion_func=lambda r, s: None if s >= 5 else "Use golang-migrate or goose for database migrations.",
    ),

    # Go DI
    "go.conventions.di_framework": RatingRule(
        score_func=lambda r: 5 if r.stats.get("primary_framework") == "wire" else 4 if r.stats.get("primary_framework") in ("fx", "dig") else 3,
        reason_func=lambda r, _: f"DI framework: {r.stats.get('primary_framework', 'none')}",
        suggestion_func=lambda r, s: None if s >= 5 else "Consider Wire for compile-time dependency injection.",
    ),

    # Go gRPC
    "go.conventions.grpc": RatingRule(
        score_func=lambda r: min(5, 3 + len(r.stats.get("features", []))),
        reason_func=lambda r, _: f"gRPC: {', '.join(r.stats.get('features', [])) or 'basic'}",
        suggestion_func=lambda r, s: None if s >= 4 else "Consider gRPC-Gateway for REST/gRPC interop.",
    ),

    # Go codegen
    "go.conventions.codegen": RatingRule(
        score_func=lambda r: min(5, 3 + r.stats.get("directive_count", 0) // 5),
        reason_func=lambda r, _: f"go:generate: {r.stats.get('directive_count', 0)} directives",
        suggestion_func=lambda r, s: None if s >= 4 else "Use go:generate for code generation.",
    ),

    # ============================================
    # New Node.js conventions
    # ============================================

    # Node package manager
    "node.conventions.package_manager": RatingRule(
        score_func=lambda r: 5 if r.stats.get("primary_manager") in ("pnpm", "yarn", "bun") else 4 if r.stats.get("primary_manager") == "npm" else 3,
        reason_func=lambda r, _: f"Package manager: {r.stats.get('primary_manager', 'npm')}",
        suggestion_func=lambda r, s: None if s >= 4 else "Consider pnpm for faster, disk-efficient package management.",
    ),

    # Node monorepo
    "node.conventions.monorepo": RatingRule(
        score_func=lambda r: 5 if r.stats.get("primary_tool") in ("turborepo", "nx") else 4 if r.stats.get("primary_tool") else 3,
        reason_func=lambda r, _: f"Monorepo: {r.stats.get('primary_tool', 'workspaces')}, {r.stats.get('package_count', 0)} packages",
        suggestion_func=lambda r, s: None if s >= 5 else "Use Turborepo or Nx for optimized monorepo builds.",
    ),

    # Node build tools
    "node.conventions.build_tools": RatingRule(
        score_func=lambda r: 5 if r.stats.get("primary_tool") in ("vite", "esbuild", "tsup") else 4 if r.stats.get("primary_tool") else 3,
        reason_func=lambda r, _: f"Build tool: {r.stats.get('primary_tool', 'none')}",
        suggestion_func=lambda r, s: None if s >= 5 else "Use Vite or esbuild for fast development builds.",
    ),

    # Node linting
    "node.conventions.linting": RatingRule(
        score_func=lambda r: 5 if r.stats.get("primary_linter") == "eslint" and r.stats.get("eslint_features", []) else 4 if r.stats.get("primary_linter") else 3,
        reason_func=lambda r, _: f"Linting: {r.stats.get('primary_linter', 'none')}" + (f" with {', '.join(r.stats.get('eslint_features', [])[:2])}" if r.stats.get("eslint_features") else ""),
        suggestion_func=lambda r, s: None if s >= 5 else "Configure ESLint with TypeScript and framework plugins.",
    ),

    # Node formatting
    "node.conventions.formatting": RatingRule(
        score_func=lambda r: 5 if r.stats.get("primary_formatter") in ("prettier", "biome") else 3,
        reason_func=lambda r, _: f"Formatting: {r.stats.get('primary_formatter', 'none')}",
        suggestion_func=lambda r, s: None if s >= 5 else "Use Prettier for consistent code formatting.",
    ),

    # Node frontend
    "node.conventions.frontend": RatingRule(
        score_func=lambda r: 5 if r.stats.get("meta_frameworks") else 4 if r.stats.get("primary_framework") else 3,
        reason_func=lambda r, _: f"Frontend: {r.stats.get('primary_framework', 'none')}" + (f" with {', '.join(r.stats.get('meta_frameworks', []))}" if r.stats.get("meta_frameworks") else ""),
        suggestion_func=lambda r, s: None if s >= 4 else "Consider a meta-framework like Next.js or Nuxt for full-stack features.",
    ),

    # Node state management
    "node.conventions.state_management": RatingRule(
        score_func=lambda r: 5 if r.stats.get("primary_library") in ("redux_toolkit", "zustand", "tanstack_query", "pinia") else 4 if r.stats.get("primary_library") else 3,
        reason_func=lambda r, _: f"State: {r.stats.get('primary_library', 'none')}",
        suggestion_func=lambda r, s: None if s >= 5 else "Use Redux Toolkit, Zustand, or TanStack Query for state management.",
    ),

    # ============================================
    # Rust conventions
    # ============================================

    # Rust Cargo
    "rust.conventions.cargo": RatingRule(
        score_func=lambda r: 5 if r.stats.get("edition") in ("2021", "2024") else 4 if r.stats.get("edition") == "2018" else 3,
        reason_func=lambda r, _: f"Rust edition {r.stats.get('edition', 'unknown')}, {r.stats.get('dependency_count', 0)} deps",
        suggestion_func=lambda r, s: None if s >= 5 else "Update to Rust edition 2021 for latest features.",
    ),

    # Rust testing
    "rust.conventions.testing": RatingRule(
        score_func=lambda r: min(5, 2 + len(r.stats.get("patterns", []))),
        reason_func=lambda r, _: f"{r.stats.get('total_tests', 0)} tests with {', '.join(r.stats.get('patterns', [])[:3]) or 'standard'}",
        suggestion_func=lambda r, s: None if s >= 4 else "Add proptest for property-based testing.",
    ),

    # Rust error handling
    "rust.conventions.error_handling": RatingRule(
        score_func=lambda r: 5 if "thiserror" in r.stats.get("patterns", []) and "anyhow" in r.stats.get("patterns", []) else 4 if r.stats.get("patterns") else 3,
        reason_func=lambda r, _: f"Error handling: {r.stats.get('primary', 'basic')}",
        suggestion_func=lambda r, s: None if s >= 5 else "Use thiserror for libraries and anyhow for applications.",
    ),

    # Rust async
    "rust.conventions.async_runtime": RatingRule(
        score_func=lambda r: 5 if r.stats.get("primary_runtime") == "Tokio" else 4 if r.stats.get("primary_runtime") else 3,
        reason_func=lambda r, _: f"Async: {r.stats.get('primary_runtime', 'none')}, {r.stats.get('total_async_functions', 0)} async fns",
        suggestion_func=lambda r, s: None if s >= 5 else "Use Tokio for production async runtime.",
    ),

    # Rust web
    "rust.conventions.web_framework": RatingRule(
        score_func=lambda r: 5 if r.stats.get("primary_framework") in ("axum", "actix") else 4 if r.stats.get("primary_framework") else 3,
        reason_func=lambda r, _: f"Web framework: {r.stats.get('primary_framework', 'none')}",
        suggestion_func=lambda r, s: None if s >= 5 else "Use Axum or Actix-web for production web services.",
    ),

    # Rust CLI
    "rust.conventions.cli_framework": RatingRule(
        score_func=lambda r: 5 if r.stats.get("primary_framework") == "clap" and r.stats.get("framework_details", {}).get("clap", {}).get("derive") else 4 if r.stats.get("primary_framework") else 3,
        reason_func=lambda r, _: f"CLI: {r.stats.get('primary_framework', 'none')}" + (" with derive" if r.stats.get("framework_details", {}).get("clap", {}).get("derive") else ""),
        suggestion_func=lambda r, s: None if s >= 5 else "Use clap with derive macros for CLI parsing.",
    ),

    # Rust serialization
    "rust.conventions.serialization": RatingRule(
        score_func=lambda r: 5 if r.stats.get("uses_serde") and len(r.stats.get("formats", [])) >= 2 else 4 if r.stats.get("uses_serde") else 3,
        reason_func=lambda r, _: f"Serde with {', '.join(r.stats.get('formats', [])) or 'no formats'}",
        suggestion_func=lambda r, s: None if s >= 5 else "Use Serde for serialization with derive macros.",
    ),

    # Rust documentation
    "rust.conventions.documentation": RatingRule(
        score_func=lambda r: 5 if r.stats.get("enforces_docs") or (r.stats.get("doc_example_count", 0) >= 5 and r.stats.get("estimated_coverage", 0) >= 0.5) else 4 if r.stats.get("doc_comment_count", 0) >= 20 else 3,
        reason_func=lambda r, _: f"{r.stats.get('doc_comment_count', 0)} doc comments, {r.stats.get('doc_example_count', 0)} examples",
        suggestion_func=lambda r, s: None if s >= 5 else "Add #![deny(missing_docs)] and doc examples.",
    ),

    # Rust unsafe
    "rust.conventions.unsafe_code": RatingRule(
        score_func=lambda r: 5 if r.stats.get("unsafe_forbidden") or (r.stats.get("safety_comment_count", 0) >= r.stats.get("unsafe_block_count", 0) and r.stats.get("unsafe_block_count", 0) <= 10) else 4 if r.stats.get("category") == "FFI" else 3,
        reason_func=lambda r, _: f"Unsafe: {r.stats.get('category', 'unknown')}, {r.stats.get('unsafe_block_count', 0)} blocks",
        suggestion_func=lambda r, s: None if s >= 5 else "Add // SAFETY: comments for all unsafe blocks.",
    ),

    # Rust macros
    "rust.conventions.macros": RatingRule(
        score_func=lambda r: 5 if r.stats.get("is_proc_macro") and "syn" in r.stats.get("proc_macro_libs", []) else 4 if r.stats.get("macro_rules_count", 0) > 0 else 3,
        reason_func=lambda r, _: f"{'Proc-macro crate' if r.stats.get('is_proc_macro') else str(r.stats.get('macro_rules_count', 0)) + ' macro_rules!'}",
        suggestion_func=lambda r, s: None if s >= 4 else "Use derive macros to reduce boilerplate.",
    ),

    # Rust logging
    "rust.conventions.logging": RatingRule(
        score_func=lambda r: 5 if r.stats.get("primary_framework") == "tracing" and r.stats.get("framework_details", {}).get("tracing", {}).get("instrument_count", 0) > 0 else 4 if r.stats.get("primary_framework") in ("tracing", "log") else 3,
        reason_func=lambda r, _: f"Logging: {r.stats.get('primary_framework', 'none')}",
        suggestion_func=lambda r, s: None if s >= 5 else "Use tracing with #[instrument] for async-aware logging.",
    ),

    # Rust database
    "rust.conventions.database": RatingRule(
        score_func=lambda r: 5 if r.stats.get("primary_library") in ("sqlx", "diesel", "sea_orm") else 4 if r.stats.get("primary_library") else 3,
        reason_func=lambda r, _: f"Database: {r.stats.get('primary_library', 'none')}",
        suggestion_func=lambda r, s: None if s >= 5 else "Use SQLx or Diesel for type-safe database access.",
    ),
}


# Default rating rule for unknown conventions
DEFAULT_RATING_RULE = RatingRule(
    score_func=_generic_score,
    reason_func=_generic_reason,
    suggestion_func=_generic_suggestion,
)


def get_rating_rule(rule_id: str) -> RatingRule:
    """Get the rating rule for a convention, or the default if not found."""
    return RATING_RULES.get(rule_id, DEFAULT_RATING_RULE)


def rate_convention(rule: ConventionRule) -> tuple[int, str, str | None]:
    """
    Rate a convention and provide feedback.

    Returns:
        tuple of (score, reason, suggestion)
        - score: 1-5 rating (1=Poor, 2=Below Average, 3=Average, 4=Good, 5=Excellent)
        - reason: Explanation for the score
        - suggestion: Improvement suggestion (None if score is 5)
    """
    rating_rule = get_rating_rule(rule.id)
    score = rating_rule.score_func(rule)
    reason = rating_rule.reason_func(rule, score)
    suggestion = rating_rule.suggestion_func(rule, score)
    return score, reason, suggestion


SCORE_LABELS = {
    1: "Poor",
    2: "Below Average",
    3: "Average",
    4: "Good",
    5: "Excellent",
}


def get_score_label(score: int) -> str:
    """Get the human-readable label for a score."""
    return SCORE_LABELS.get(score, "Unknown")


def get_score_emoji(score: int) -> str:
    """Get an emoji representation of the score."""
    emojis = {
        1: "1",
        2: "2",
        3: "3",
        4: "4",
        5: "5",
    }
    return emojis.get(score, "?")
