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


def _get_stat(rule: ConventionRule, key: str, default: float = 0.0) -> float:
    """Safely get a stat value from a rule."""
    return rule.stats.get(key, default)


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

    # Consistent is good (either all async or all sync)
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
    return f"API style: {async_count} async, {sync_count} sync ({ratio * 100:.0f}% async)"


def _async_style_suggestion(r: ConventionRule, score: int) -> str | None:
    if score >= 5:
        return None
    ratio = _get_stat(r, "async_ratio", 0)
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

    # Modern async frameworks preferred
    if primary in ("fastapi", "litestar") and len(frameworks) == 1:
        return 5
    if primary in ("fastapi", "litestar"):
        return 4
    if primary in ("flask", "django", "starlette"):
        return 4
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
    frameworks = r.stats.get("framework_counts", {})
    if len(frameworks) > 1:
        return "Consolidate API frameworks to a single choice for consistency."
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


def _generic_suggestion(_r: ConventionRule, score: int) -> str | None:
    if score >= 4:
        return None
    return "Review this convention for potential improvements based on best practices."


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
        score_func=lambda r: 5 if r.stats.get("hook_tool") in ("pre-commit", "husky", "lefthook") else 3,
        reason_func=lambda r, _: f"Git hooks: {r.stats.get('hook_tool', 'none configured')}",
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

    # Python tooling
    "python.conventions.formatter": RatingRule(
        score_func=lambda r: 5 if r.stats.get("primary_formatter") in ("black", "ruff") else 4 if r.stats.get("primary_formatter") else 3,
        reason_func=lambda r, _: f"Code formatter: {r.stats.get('primary_formatter', 'none')}",
        suggestion_func=lambda r, s: None if s >= 5 else "Use Black or Ruff for consistent code formatting.",
    ),
    "python.conventions.linter": RatingRule(
        score_func=lambda r: 5 if r.stats.get("primary_linter") in ("ruff", "flake8_mypy") else 4 if r.stats.get("primary_linter") else 3,
        reason_func=lambda r, _: f"Linter: {r.stats.get('primary_linter', 'none')}",
        suggestion_func=lambda r, s: None if s >= 5 else "Use Ruff for fast, comprehensive linting.",
    ),
    "python.conventions.import_sorting": RatingRule(
        score_func=lambda r: 5 if r.stats.get("import_sorter") in ("isort", "ruff") else 3,
        reason_func=lambda r, _: f"Import sorting: {r.stats.get('import_sorter', 'none')}",
        suggestion_func=lambda r, s: None if s >= 5 else "Use isort or Ruff for consistent import ordering.",
    ),

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

    # Python background tasks
    "python.conventions.background_tasks": RatingRule(
        score_func=lambda r: 5 if r.stats.get("primary_library") in ("celery", "dramatiq", "rq") else 4 if r.stats.get("primary_library") else 3,
        reason_func=lambda r, _: f"Background tasks: {r.stats.get('primary_library', 'none')}",
        suggestion_func=lambda r, s: None if s >= 4 else "Use Celery or Dramatiq for background task processing.",
    ),

    # Python caching
    "python.conventions.caching": RatingRule(
        score_func=lambda r: 5 if r.stats.get("primary_library") in ("redis", "aiocache") else 4 if r.stats.get("primary_library") else 3,
        reason_func=lambda r, _: f"Caching: {r.stats.get('primary_library', 'none')}",
        suggestion_func=lambda r, s: None if s >= 4 else "Use Redis or functools caching for performance.",
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
