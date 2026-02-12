"""CLAUDE.md generator for conventions detection.

Generates a structured CLAUDE.md file optimized for Claude Code,
filtering conventions by signal quality rather than score.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..schemas import ConventionRule, ConventionsOutput

# --- Rule classification ---

# Suffixes that are low-signal for Claude (editor/formatting/boilerplate)
_EXCLUDE_SUFFIXES = frozenset({
    "editor_config",
    "standard_files",
    "dependency_updates",
    "jsdoc",
    "docstrings",
    "docstring_style",
    "barrel_exports",
    "promise_patterns",
    "codegen_markers",
    "env_config",
    "string_formatting",
    "import_style",
    "import_sorting",
    "string_quotes",
    "line_length",
    "pre_commit_hooks",
    "git_hooks",
    "path_handling",
    "doc_comments",
    "documentation",
    "example_completeness",
    "example_structure",
    "organization",
    "code_generation",
    "strict_mode",
    "lock_file",
    "dependency_management",
    "container_local_dev",
    "openapi_docs",
    "coverage_thresholds",
    "coverage_config",
    "env_separation",
})

# Suffixes that get a one-liner in Tech Stack (tools, not patterns)
_TECH_STACK_SUFFIXES = frozenset({
    "package_manager",
    "formatting",
    "formatter",
    "linting",
    "linter",
    "build_tools",
    "frontend",
    "ui_library",
    "ci_platform",
    "ci_quality",
    "kubernetes",
    "docker_compose",
    "dockerfile",
    "logging_library",
    "testing_framework",
    "framework",
    "http_framework",
    "web_framework",
    "api_framework",
    "cli_framework",
    "db_library",
    "type_checker_strictness",
    "graphql",
    "grpc",
    "message_broker",
    "async_http_client",
    "cargo",
    "schema_library",
    "tracing",
    "metrics",
    "feature_flags",
})

_CONFIDENCE_THRESHOLD = 0.70

# Single-test invocation templates per framework
_SINGLE_TEST_TEMPLATES: dict[str, str] = {
    "pytest": "pytest path/to/test.py::TestClass::test_method",
    "unittest": "python -m pytest path/to/test.py::TestClass::test_method",
    "jest": "npx jest --testPathPattern=<file> --testNamePattern='<name>'",
    "vitest": "npx vitest run <file> -t '<name>'",
    "mocha": "npx mocha --grep '<name>' <file>",
    "ava": "npx ava <file> --match='<name>'",
    "testify": "go test ./<pkg>/... -run <TestName> -v",
    "go": "go test ./<pkg>/... -run <TestName> -v",
    "cargo": "cargo test <test_name> -- --exact",
}


def _get_suffix(rule: ConventionRule) -> str:
    """Extract the last segment of a rule ID (after the last dot)."""
    return rule.id.rsplit(".", 1)[-1] if "." in rule.id else rule.id


def _classify_rule(rule: ConventionRule) -> str:
    """Classify a rule as 'exclude', 'tech_stack', or 'include'."""
    if rule.confidence < _CONFIDENCE_THRESHOLD:
        return "exclude"
    suffix = _get_suffix(rule)
    if suffix in _EXCLUDE_SUFFIXES:
        return "exclude"
    if suffix in _TECH_STACK_SUFFIXES:
        return "tech_stack"
    return "include"


def _get_stat(rule: ConventionRule, key: str, default: Any = None) -> Any:
    """Safely get a stat value from a rule."""
    return rule.stats.get(key, default)


# --- Section builders ---


def _build_project_overview(output: ConventionsOutput, include_rules: list[ConventionRule]) -> str:
    """Build the Project Overview section."""
    langs = output.metadata.detected_languages
    lang_str = ", ".join(langs) if langs else "Unknown"

    # Try to find framework
    framework = None
    for rule in include_rules:
        suffix = _get_suffix(rule)
        if suffix in ("framework", "http_framework", "web_framework", "api_framework"):
            framework = _get_stat(rule, "primary_framework") or rule.title
            break

    # Try to find project description from repo_layout stats
    project_desc = ""
    for rule in include_rules:
        if _get_suffix(rule) == "repo_layout":
            project_desc = _get_stat(rule, "project_description", "")
            break

    parts = ["## Project Overview\n"]
    if framework:
        parts.append(f"{lang_str} project using {framework}.\n")
    else:
        parts.append(f"{lang_str} project.\n")

    if project_desc:
        parts.append(f"{project_desc}\n")

    return "\n".join(parts)


def _build_directory_map_section(include_rules: list[ConventionRule]) -> str:
    """Build annotated directory map section."""
    layout_rule = None
    for rule in include_rules:
        if _get_suffix(rule) == "repo_layout":
            layout_rule = rule
            break
    if not layout_rule:
        return ""

    tree = _get_stat(layout_rule, "directory_tree", {})
    if not tree:
        return ""

    lines = ["## Directory Structure\n"]
    _render_tree(tree, lines, indent=0)
    lines.append("")
    return "\n".join(lines)


# Directories whose internals are test infrastructure — don't recurse
_TEST_TOOL_DIRS = frozenset({
    "cypress", "e2e", "__tests__", ".storybook", "playwright",
    "coverage", "test-results", "jest",
})


def _render_tree(tree: dict, lines: list[str], indent: int) -> None:
    """Recursively render a directory tree into markdown lines.

    Skips recursing into:
    - directories with more than 10 children (collections of similar items)
    - known test tool directories (cypress, e2e, etc.)
    """
    prefix = "  " * indent
    for name in sorted(tree.keys()):
        node = tree[name]
        purpose = node.get("purpose", "")
        children = node.get("children", {})
        if purpose:
            # Truncate long descriptions (often from package.json)
            if len(purpose) > 80:
                purpose = purpose[:77] + "..."
            lines.append(f"{prefix}- `{name}/` — {purpose}")
        else:
            lines.append(f"{prefix}- `{name}/`")
        # Skip recursing into test tool dirs and large collections
        if name in _TEST_TOOL_DIRS:
            continue
        if len(children) <= 10:
            _render_tree(children, lines, indent + 1)


def _build_architecture_section(include_rules: list[ConventionRule]) -> str:
    """Build the Architecture section from pattern/structure rules."""
    arch_suffixes = {
        "layer_separation", "middleware_patterns", "route_organization",
        "response_patterns", "handler_pattern", "route_factory",
        "response_utility", "store_pattern", "context_pattern",
        "project_structure", "dependency_injection", "repository_pattern",
        "singleton_pattern", "constructor_injection", "di_style",
        "di_framework", "layering_direction", "forbidden_imports",
        "interface_segregation", "interfaces", "dependency_direction",
        "builder_pattern", "options_pattern", "context_usage",
        "goroutine_patterns", "sync_primitives", "channel_usage",
        "modules", "package_structure",
        "import_graph", "endpoint_chains", "service_dependencies",
        "api_routes", "monorepo", "db_entities",
    }

    arch_rules = [r for r in include_rules if _get_suffix(r) in arch_suffixes]
    if not arch_rules:
        return ""

    lines = ["## Architecture\n", "### Key Patterns\n"]
    for rule in arch_rules:
        suffix = _get_suffix(rule)
        rendered = _render_arch_rule(rule, suffix)
        if rendered:
            lines.append(rendered)
    lines.append("")

    return "\n".join(lines)


def _render_arch_rule(rule: ConventionRule, suffix: str) -> str:
    """Render a single architecture rule as an agent-useful line."""
    stats = rule.stats

    if suffix == "monorepo":
        packages = _get_stat(rule, "packages", [])
        if packages:
            lines = [f"- **{rule.title}**:"]
            for pkg in packages[:15]:
                name = pkg.get("name", "?")
                path = pkg.get("path", "")
                lines.append(f"  - `{name}` — {path}")
            return "\n".join(lines)
        return f"- **{rule.title}**: {rule.description}"

    if suffix == "db_entities":
        summary = _summarize_rule(rule)
        return f"- **{rule.title}**: {summary}"

    if suffix == "layer_separation":
        api = stats.get("api_files", stats.get("api_count", 0))
        svc = stats.get("service_files", stats.get("service_count", 0))
        db = stats.get("db_files", stats.get("db_count", 0))
        return f"- **{rule.title}**: routes ({api} files) → services ({svc} files) → data stores ({db} files)"

    if suffix == "api_routes":
        total = stats.get("total_routes", 0)
        methods = stats.get("methods", {})
        method_str = ", ".join(f"{v} {k}" for k, v in sorted(methods.items()))
        return f"- **API routes**: {total} endpoints ({method_str})"

    if suffix == "import_graph":
        cycles = stats.get("cycle_count", 0)
        cycle_examples = stats.get("cycles", [])
        if cycles and cycle_examples:
            example = cycle_examples[0]
            parts = " -> ".join(_short_path(f) for f in example[:3])
            return f"- **Circular dependencies**: {cycles} found (e.g. {parts})"
        return ""

    if suffix == "endpoint_chains":
        return ""  # Rendered separately in API Chains section

    if suffix == "service_dependencies":
        deps = stats.get("dependencies", {})
        if isinstance(deps, dict) and deps:
            examples = []
            for svc_path, store_paths in deps.items():
                svc = _short_path(svc_path)
                # Skip test files
                if ".unit." in svc or ".spec." in svc or ".test." in svc:
                    continue
                concrete_stores = [
                    _short_path(s) for s in store_paths[:2]
                    if not s.rsplit("/", 1)[-1].startswith("index.")
                ]
                if concrete_stores:
                    examples.append(f"`{svc}` → `{', '.join(concrete_stores)}`")
                if len(examples) >= 3:
                    break
            if examples:
                return "- **Service → store wiring**: " + "; ".join(examples)
        return ""

    if suffix == "store_pattern":
        count = stats.get("store_class_count", 0)
        dirs = stats.get("store_directories", [])
        dir_str = ", ".join(f"`{d}/`" for d in dirs) if dirs else ""
        return f"- **Store pattern**: {count} store classes in {dir_str}"

    if suffix == "context_pattern":
        count = stats.get("context_interface_count", stats.get("context_count", 0))
        return f"- **Context object pattern**: passes services/stores via context ({count} context interfaces)"

    if suffix in ("middleware_patterns", "route_organization", "handler_pattern",
                   "route_factory", "response_utility"):
        # These are useful patterns — keep title, strip counts from description
        desc = _strip_counts(rule.description)
        return f"- **{rule.title}**: {desc}"

    # Default: use description but truncate
    desc = rule.description
    if len(desc) > 200:
        desc = desc[:197] + "..."
    return f"- **{rule.title}**: {desc}"


def _strip_counts(description: str) -> str:
    """Remove raw count stats from a description, keeping the pattern info."""
    import re
    # Remove sentence fragments that are mostly stats/counts
    # e.g. "async/await: 8780, .then(): 612, callbacks: 5"
    # or "try/catch: 314, .catch(): 12"
    parts = description.split(". ")
    useful = []
    for part in parts:
        stripped = part.strip().rstrip(".")
        # Skip parts that have 2+ stat entries like "key: N, key: N"
        if len(re.findall(r"[\w./()]+:\s*\d+", stripped)) >= 2:
            continue
        # Skip parts that are just "Found N things" or "Found N X Y"
        if re.match(r"^Found \d+ [\w\s]+$", stripped):
            continue
        if re.match(r"^\d+ \w+ (found|detected|files?)\.?$", stripped):
            continue
        # Skip parts that are "Total X: N"
        if re.match(r"^Total \w+:\s*\d+$", stripped):
            continue
        # Strip trailing count phrases like ", 30 typed handlers" or ". Total usages: 50"
        part = re.sub(r",?\s*\d+\s+\w+\s+(handlers?|usages?|instances?|occurrences?|files?)\b\.?", "", part)
        # Strip "Total X: N" patterns
        part = re.sub(r"\.\s*Total \w+:\s*\d+\.?", "", part)
        part = part.strip().rstrip(",").strip()
        if part:
            useful.append(part)
    if not useful:
        return description
    return ". ".join(useful)


def _build_tech_stack_section(
    tech_rules: list[ConventionRule],
    output: ConventionsOutput,
) -> str:
    """Build the Tech Stack section."""
    lines = ["## Tech Stack\n"]

    langs = output.metadata.detected_languages
    if langs:
        lines.append(f"- **Runtime**: {', '.join(langs)}")

    # Map suffixes to display labels and stat key candidates (tried in order)
    stack_map: list[tuple[str, str, list[str]]] = [
        ("package_manager", "Package manager", ["primary_manager"]),
        ("framework", "Backend", ["primary_framework"]),
        ("http_framework", "Backend", ["primary_framework"]),
        ("web_framework", "Backend", ["primary_framework"]),
        ("api_framework", "Backend", ["primary_framework"]),
        ("frontend", "Frontend", ["primary_framework", "primary_library"]),
        ("ui_library", "UI library", ["primary_library"]),
        ("testing_framework", "Testing", ["primary_framework", "primary_library"]),
        ("db_library", "Database", ["primary_library"]),
        ("formatting", "Formatting", ["primary_formatter", "primary_tool"]),
        ("formatter", "Formatting", ["primary_formatter"]),
        ("linting", "Linting", ["primary_linter", "primary_tool"]),
        ("linter", "Linting", ["primary_linter"]),
        ("logging_library", "Logging", ["primary_library"]),
        ("ci_platform", "CI/CD", ["platform", "platforms"]),
        ("build_tools", "Build", ["primary_tool"]),
        ("schema_library", "Schema validation", ["primary_library"]),
        ("message_broker", "Message broker", ["primary_broker"]),
        ("graphql", "GraphQL", []),
        ("grpc", "gRPC", []),
    ]

    seen_labels: set[str] = set()
    for rule in tech_rules:
        suffix = _get_suffix(rule)
        for sfx, label, stat_keys in stack_map:
            if suffix == sfx and label not in seen_labels:
                value = None
                for key in stat_keys:
                    value = _get_stat(rule, key)
                    if value:
                        break
                if not value and not stat_keys:
                    value = rule.title
                if value:
                    display = ", ".join(value) if isinstance(value, list) else str(value)
                    lines.append(f"- **{label}**: {display}")
                    seen_labels.add(label)
                break

    # TypeScript info from include rules (ts_migration, typescript)
    lines.append("")
    return "\n".join(lines)


def _build_environment_section(include_rules: list[ConventionRule]) -> str:
    """Build the Environment Setup section."""
    env_suffixes = {"env_setup", "required_services", "runtime_prerequisites"}
    env_rules = [r for r in include_rules if _get_suffix(r) in env_suffixes]
    if not env_rules:
        return ""

    lines = ["## Environment Setup\n"]

    for rule in env_rules:
        suffix = _get_suffix(rule)
        if suffix == "runtime_prerequisites":
            tools = _get_stat(rule, "tools", [])
            if tools:
                lines.append("### Prerequisites\n")
                for tool in tools:
                    lines.append(f"- **{tool['name']}**: {tool['version']} (from `{tool['source']}`)")
                lines.append("")
        elif suffix == "required_services":
            services = _get_stat(rule, "services", [])
            if services:
                lines.append("### Required Services\n")
                for svc in services:
                    img = svc.get("image", "")
                    if img:
                        lines.append(f"- **{svc['name']}**: `{img}`")
                    else:
                        lines.append(f"- **{svc['name']}**")
                lines.append("")
        elif suffix == "env_setup":
            total = _get_stat(rule, "total_vars", 0)
            env_file = _get_stat(rule, "env_file", ".env.example")
            categories = _get_stat(rule, "var_categories", {})
            lines.append("### Environment Variables\n")
            lines.append(f"{total} variables in `{env_file}`.")
            if categories:
                cat_parts = [f"{k} ({v})" for k, v in sorted(categories.items())]
                lines.append(f"Categories: {', '.join(cat_parts)}.")
            lines.append("")

    return "\n".join(lines)


def _find_single_test_template(
    tech_rules: list[ConventionRule],
    include_rules: list[ConventionRule],
) -> str | None:
    """Find the single-test invocation template from testing framework rules."""
    for rule in tech_rules + include_rules:
        if _get_suffix(rule) != "testing_framework":
            continue
        fw = (_get_stat(rule, "primary_framework")
              or _get_stat(rule, "primary_library")
              or "")
        if not fw:
            continue
        fw_lower = fw.lower()
        for key, template in _SINGLE_TEST_TEMPLATES.items():
            if key in fw_lower:
                return template
    return None


def _build_commands_section(
    include_rules: list[ConventionRule],
    tech_rules: list[ConventionRule],
) -> str:
    """Build commands section, preferring detected task runner data."""
    lines = ["## Commands\n"]

    # Check for task runner data first
    task_runner_rule = None
    for rule in include_rules:
        if _get_suffix(rule) == "task_runner":
            task_runner_rule = rule
            break

    if task_runner_rule:
        return _build_commands_from_task_runner(task_runner_rule, tech_rules, include_rules, lines)

    return _build_commands_inferred(include_rules, tech_rules, lines)


def _build_commands_from_task_runner(
    rule: ConventionRule,
    tech_rules: list[ConventionRule],
    include_rules: list[ConventionRule],
    lines: list[str],
) -> str:
    """Build commands from detected task runner targets."""
    targets = _get_stat(rule, "targets", {})
    primary = _get_stat(rule, "primary_runner", "")

    # Detect package manager for npm scripts
    pkg_mgr = "npm"
    for tr in tech_rules:
        if _get_suffix(tr) == "package_manager":
            mgr = _get_stat(tr, "primary_manager", "npm")
            if mgr:
                pkg_mgr = mgr.lower()
            break

    runner_cmds = {
        "makefile": "make",
        "taskfile": "task",
        "justfile": "just",
    }

    # Dev-related keywords for categorization
    _DEV_KEYWORDS = {"test", "build", "check", "install", "dev", "run", "start",
                     "lint", "format", "watch", "serve", "clean", "typecheck"}
    _INFRA_KEYWORDS = {"docker", "compose", "workflow", "dhall", "k8s", "deploy",
                       "ci", "helm", "terraform", "kustomize", "image", "push",
                       "release", "publish"}

    def _is_dev_target(target_name: str) -> bool:
        parts = set(target_name.lower().replace("_", "-").split("-"))
        if parts & _INFRA_KEYWORDS:
            return False
        return bool(parts & _DEV_KEYWORDS)

    # List commands from the primary runner
    check_cmd = None
    test_cmd = None

    if primary in runner_cmds:
        prefix = runner_cmds[primary]
        runner_targets = targets.get(primary, [])
        dev_targets = [t for t in runner_targets if _is_dev_target(t.get("name", ""))]

        for target in dev_targets:
            name = target.get("name", "")
            desc = target.get("description", "")
            label = name.replace("_", " ").replace("-", " ").title()
            if desc:
                lines.append(f"- **{label}**: `{prefix} {name}` — {desc}")
            else:
                lines.append(f"- **{label}**: `{prefix} {name}`")
            # Track check/test commands for verify line
            name_lower = name.lower()
            if "check" in name_lower or "lint" in name_lower or "typecheck" in name_lower:
                check_cmd = f"{prefix} {name}"
            if "test" in name_lower and "integration" not in name_lower:
                test_cmd = f"{prefix} {name}"

        # Non-dev targets (docker, workflow, etc.) are omitted — agents can discover them
    elif primary == "package_json":
        runner_targets = targets.get("package_json", [])
        run_prefix = f"{pkg_mgr} run " if pkg_mgr == "npm" else f"{pkg_mgr} "
        for target in runner_targets:
            name = target.get("name", "")
            cmd = target.get("command", "")
            label = name.replace("_", " ").replace("-", " ").title()
            if cmd:
                lines.append(f"- **{label}**: `{run_prefix}{name}` (`{cmd}`)")
            else:
                lines.append(f"- **{label}**: `{run_prefix}{name}`")

    # If primary runner is not package_json, also show important npm scripts
    if primary != "package_json":
        pkg_targets = targets.get("package_json", [])
        if pkg_targets:
            _NPM_DEV_SCRIPTS = {"dev", "start", "build", "test", "lint", "typecheck",
                                "format", "dev:api", "dev:server", "cy:open", "cy:run"}
            run_prefix = f"{pkg_mgr} run " if pkg_mgr == "npm" else f"{pkg_mgr} "
            dev_scripts = [t for t in pkg_targets if t.get("name", "") in _NPM_DEV_SCRIPTS]
            if dev_scripts:
                lines.append("")
                lines.append("### npm scripts\n")
                for target in dev_scripts:
                    name = target.get("name", "")
                    label = name.replace("_", " ").replace("-", " ").replace(":", " ").title()
                    lines.append(f"- **{label}**: `{run_prefix}{name}`")

    # Append single-test command template
    single_test = _find_single_test_template(tech_rules, include_rules)
    if single_test:
        lines.append(f"- **Test single**: `{single_test}`")

    # Add verify line combining check + test
    if check_cmd and test_cmd:
        lines.append(f"- **Verify changes**: `{check_cmd} && {test_cmd}`")
    elif test_cmd:
        lines.append(f"- **Verify changes**: `{test_cmd}`")

    lines.append("")
    return "\n".join(lines)


def _build_commands_inferred(
    include_rules: list[ConventionRule],
    tech_rules: list[ConventionRule],
    lines: list[str],
) -> str:
    """Infer common commands from detected conventions (fallback)."""
    # Detect package manager (only if explicitly detected)
    pkg_mgr = None
    for rule in tech_rules:
        if _get_suffix(rule) == "package_manager":
            mgr = _get_stat(rule, "primary_manager", "")
            if mgr:
                pkg_mgr = mgr.lower()
            break

    # Detect dependency management (Python: uv, pip, poetry, pdm)
    if not pkg_mgr:
        for rule in tech_rules:
            if _get_suffix(rule) == "dependency_management":
                mgr = _get_stat(rule, "primary_manager", "")
                if mgr:
                    pkg_mgr = mgr.lower()
                break

    # Detect test framework
    test_cmd = None
    for rule in tech_rules + include_rules:
        if _get_suffix(rule) == "testing_framework":
            fw = _get_stat(rule, "primary_framework") or _get_stat(rule, "primary_library") or ""
            if fw:
                fw_lower = fw.lower()
                if "pytest" in fw_lower:
                    test_cmd = "pytest"
                elif "ava" in fw_lower:
                    test_cmd = f"{pkg_mgr or 'npm'} run ava"
                elif "jest" in fw_lower:
                    test_cmd = f"{pkg_mgr or 'npm'} test"
                elif "vitest" in fw_lower:
                    test_cmd = f"{pkg_mgr or 'npm'} test"
                elif "mocha" in fw_lower:
                    test_cmd = f"{pkg_mgr or 'npm'} test"
                elif "go" in fw_lower:
                    test_cmd = "go test ./..."
                elif "cargo" in fw_lower:
                    test_cmd = "cargo test"
            break

    if pkg_mgr in ("npm", "yarn", "pnpm", "bun"):
        lines.append(f"- **Install**: `{pkg_mgr} install`")
        if pkg_mgr == "npm":
            lines.append(f"- **Dev server**: `{pkg_mgr} run dev`")
        else:
            lines.append(f"- **Dev server**: `{pkg_mgr} dev`")
    elif pkg_mgr in ("pip", "poetry", "uv", "pdm"):
        lines.append(f"- **Install**: `{pkg_mgr} install`")
    elif pkg_mgr == "go":
        lines.append("- **Build**: `go build ./...`")

    if test_cmd:
        lines.append(f"- **Test**: `{test_cmd}`")

    # Append single-test command template
    single_test = _find_single_test_template(tech_rules, include_rules)
    if single_test:
        lines.append(f"- **Test single**: `{single_test}`")

    lines.append("")
    lines.append("[TODO: Add project-specific commands]")
    lines.append("")
    return "\n".join(lines)


def _build_conventions_section(
    include_rules: list[ConventionRule],
    tech_rules: list[ConventionRule] | None = None,
) -> str:
    """Build the Conventions section from naming, module, async rules."""
    conv_suffixes = {
        "file_naming", "test_file_naming", "module_system", "async_style",
        "error_classes", "error_handling", "error_handling_boundary",
        "error_taxonomy", "error_types", "error_wrapping", "error_wrapper",
        "error_transformation", "error_response_pattern", "exception_chaining",
        "exception_handlers", "commit_messages", "branch_naming",
        "naming", "constant_naming", "enum_usage", "string_constants",
        "class_style", "data_class_style", "typing_coverage", "type_coverage",
        "typescript", "ts_migration", "validation_style",
        "test_patterns", "test_structure", "test_naming", "mocking",
        "async_error_handling", "async_orm", "caching",
        "auth_pattern", "auth_provider", "rate_limiting",
        "secret_management", "secrets_access_style", "password_hashing",
        "sql_injection", "input_validation", "helmet_security",
        "structured_logging", "logging_fields", "correlation_ids",
        "custom_decorators", "decorator_patterns",
        "db_session_lifecycle", "db_query_style", "db_transactions",
        "db_migrations", "db_connection_pooling", "migrations",
        "response_shape", "response_envelope", "pagination_pattern",
        "api_versioning", "background_tasks", "background_jobs",
        "context_managers", "sentinel_errors", "subtests",
        "table_driven_tests", "test_helpers",
        "serialization", "resilience",
        "state_management",
        "config_access",
        "code_owners", "file_hotspots",
        "commit_messages", "pr_template",
        "import_aliases",
    }

    conv_rules = [r for r in include_rules if _get_suffix(r) in conv_suffixes]
    if not conv_rules:
        return ""

    # Suppress structured_logging (console.log) when a real logging library is detected
    has_logging_library = any(
        _get_suffix(r) == "logging_library" for r in (tech_rules or [])
    )

    lines = ["## Conventions\n"]
    for rule in conv_rules:
        if _get_suffix(rule) == "structured_logging" and has_logging_library:
            continue
        # Extract the most useful stat or fall back to description
        summary = _summarize_rule(rule)
        # Avoid "Title: Title" duplication
        if summary.lower() == rule.title.lower():
            lines.append(f"- **{rule.title}**")
        else:
            lines.append(f"- **{rule.title}**: {summary}")

    lines.append("")
    lines.append("[TODO: Add project-specific conventions]")
    lines.append("")
    return "\n".join(lines)


def _summarize_rule(rule: ConventionRule) -> str:
    """Create a concise summary from a rule's stats or description."""
    suffix = _get_suffix(rule)
    stats = rule.stats

    # Try to extract the most useful stat for known patterns
    if suffix == "file_naming" and "dominant_style" in stats:
        pct = stats.get("dominant_percentage", "")
        return f"{stats['dominant_style']}" + (f" ({pct}%)" if pct else "")

    if suffix == "test_file_naming" and "dominant_pattern" in stats:
        return stats["dominant_pattern"]

    if suffix == "module_system" and "dominant_system" in stats:
        pct = stats.get("dominant_percentage", "")
        return f"{stats['dominant_system']}" + (f" ({pct}%)" if pct else "")

    if suffix == "async_style" and "dominant_style" in stats:
        return stats["dominant_style"]

    if suffix == "typescript":
        ratio = stats.get("ts_ratio") or stats.get("typescript_percentage")
        if ratio is not None:
            return f"{ratio}% TypeScript"

    if suffix == "ts_migration":
        ts_check = stats.get("ts_check_count", 0)
        parts = []
        if stats.get("allow_js"):
            parts.append("allowJs enabled")
        if stats.get("check_js"):
            parts.append("checkJs enabled")
        if ts_check:
            parts.append(f"{ts_check} @ts-check files")
        if parts:
            return f"Early stage JS→TS migration ({', '.join(parts)})"

    if suffix == "commit_messages" and "dominant_style" in stats:
        return stats["dominant_style"]

    if suffix == "branch_naming":
        strategy = stats.get("strategy", "")
        if strategy == "gitflow":
            return "GitFlow branching"
        if strategy == "trunk":
            return "Trunk-based/GitHub Flow"
        if "dominant_pattern" in stats:
            return stats["dominant_pattern"]

    if suffix == "monorepo" and "workspace_count" in stats:
        mgr = stats.get("manager", "")
        return f"{stats['workspace_count']} workspaces" + (f" ({mgr})" if mgr else "")

    if suffix == "import_graph":
        total = stats.get("total_files", "?")
        edges = stats.get("total_edges", "?")
        cycles = stats.get("cycle_count", 0)
        parts = [f"{total} files, {edges} internal imports"]
        if cycles:
            parts.append(f"{cycles} circular deps")
        return ", ".join(parts)

    if suffix == "endpoint_chains":
        count = stats.get("chain_count", "?")
        return f"{count} traced endpoint chains"

    if suffix == "service_dependencies":
        count = stats.get("dependency_count", "?")
        return f"{count} service dependencies mapped"

    if suffix == "api_routes":
        total = stats.get("total_routes", "?")
        methods = stats.get("methods", {})
        method_str = ", ".join(f"{k}: {v}" for k, v in sorted(methods.items()))
        return f"{total} API endpoints ({method_str})" if method_str else f"{total} API endpoints"

    if suffix == "task_runner":
        runners = stats.get("runners_found", [])
        total = stats.get("total_targets", 0)
        return f"{', '.join(runners)} ({total} targets)"

    if suffix == "db_migrations":
        tool = stats.get("primary_tool", "unknown")
        count = stats.get("total_migration_files", 0)
        return f"{tool} ({count} migrations)"

    if suffix == "migrations":
        tool = stats.get("primary_tool", "unknown")
        count = stats.get("migration_file_count", 0)
        return f"{tool} ({count} migrations)"

    if suffix == "env_setup":
        total = stats.get("total_vars", 0)
        return f"{total} env vars required"

    if suffix == "required_services":
        services = stats.get("services", [])
        names = [s["name"] for s in services[:5]]
        return ", ".join(names) + " required"

    if suffix == "config_access":
        libs = stats.get("libraries", {})
        if libs:
            lib_name = max(libs, key=libs.get)
            # Clean up library name: node_dotenv -> dotenv
            lib_name = lib_name.replace("node_", "").replace("python_", "")
            return f"Uses `{lib_name}` for env config"
        style = stats.get("access_style", "")
        if style == "direct":
            return "Direct `process.env`/`os.environ` config access"
        return rule.description

    if suffix == "code_owners":
        count = stats.get("owner_count", "?")
        rules_count = stats.get("rule_count", "?")
        return f"{count} owners, {rules_count} rules"

    if suffix == "file_hotspots":
        hotspots = stats.get("hotspots", [])
        if hotspots:
            names = [f"`{h['file'].rsplit('/', 1)[-1]}`" for h in hotspots[:3]]
            return f"Frequently modified: {', '.join(names)}"
        return rule.description

    if suffix == "commit_messages":
        convention = stats.get("convention", "freeform")
        if convention == "conventional":
            return "Conventional Commits (feat:, fix:, docs:, refactor:, ...)"
        if convention == "gitmoji":
            return "Gitmoji commit messages"
        if convention == "ticket":
            return "Ticket-prefixed commits (ABC-123)"
        return "Freeform commit messages"

    if suffix == "pr_template":
        sections = stats.get("sections", [])
        has_multiple = stats.get("has_multiple_templates", False)
        if has_multiple:
            count = stats.get("template_count", 0)
            return f"{count} PR templates available"
        if sections:
            return f"Sections: {', '.join(sections[:4])}"
        return "PR template present"

    if suffix == "import_aliases":
        # Node: show alias mappings
        aliases = stats.get("aliases", {})
        module_path = stats.get("module_path", "")
        layout = stats.get("layout", "")
        package_name = stats.get("package_name", "")
        if aliases:
            parts = [f"`{k}` -> `{v}`" for k, v in list(aliases.items())[:3]]
            return ", ".join(parts)
        if module_path:
            return f"Module: `{module_path}`"
        if package_name:
            return f"{layout}-layout: `import {package_name}`"
        return rule.description

    if suffix == "db_entities":
        count = stats.get("entity_count", 0)
        orm = stats.get("orm", "")
        entities = stats.get("entities", [])
        names = [e["name"] for e in entities[:8]]
        label = f"{count} {orm} entities" if orm else f"{count} entities"
        if names:
            return f"{label}: {', '.join(names)}" + ("..." if count > 8 else "")
        return label

    if suffix == "dependency_health":
        strategy = stats.get("pinning_strategy", "unknown")
        total = stats.get("total_deps", 0)
        has_lock = stats.get("has_lock_file", False)
        parts = [f"{strategy} pinning ({total} deps)"]
        if has_lock:
            parts.append("lock file present")
        return ", ".join(parts)

    # Fall back to description, stripped of raw counts for agent readability
    desc = _strip_counts(rule.description)
    if len(desc) > 200:
        desc = desc[:197] + "..."
    return desc


def _build_generated_code_section(include_rules: list[ConventionRule]) -> str:
    """Build the Generated Code warning section."""
    gen_rule = None
    for rule in include_rules:
        if _get_suffix(rule) == "generated_code":
            gen_rule = rule
            break
    if not gen_rule:
        return ""

    lines = ["## Generated Code (do not edit)\n"]

    dirs = _get_stat(gen_rule, "generated_dirs", [])
    for d in dirs:
        lines.append(f"- `{d}/`")

    patterns = _get_stat(gen_rule, "generated_file_patterns", [])
    for p in patterns:
        lines.append(f"- `{p}`")

    configs = _get_stat(gen_rule, "codegen_configs", [])
    if configs:
        lines.append(f"- Config: {', '.join(f'`{c}`' for c in configs)}")

    marker_count = _get_stat(gen_rule, "marker_count", 0)
    if marker_count and not dirs and not patterns:
        lines.append(f"- {marker_count} files with `@generated` markers")

    lines.append("")
    return "\n".join(lines)


def _build_deployment_section(
    tech_rules: list[ConventionRule],
    include_rules: list[ConventionRule],
) -> str:
    """Build the Deployment section from CI/CD and container rules."""
    deploy_suffixes = {
        "ci_platform", "ci_quality", "branch_naming",
        "dockerfile", "docker_compose", "kubernetes",
    }
    all_rules = tech_rules + include_rules
    deploy_rules = [r for r in all_rules if _get_suffix(r) in deploy_suffixes]
    if not deploy_rules:
        return ""

    lines = ["## Deployment\n"]

    for rule in deploy_rules:
        suffix = _get_suffix(rule)
        if suffix == "ci_platform":
            pass  # Already shown in Tech Stack
        elif suffix == "ci_quality":
            features = []
            if _get_stat(rule, "has_test_workflow"):
                features.append("tests")
            if _get_stat(rule, "has_lint_workflow"):
                features.append("linting")
            if _get_stat(rule, "has_deploy_workflow"):
                features.append("deploy")
            if _get_stat(rule, "has_caching"):
                features.append("caching")
            if _get_stat(rule, "has_matrix"):
                features.append("matrix builds")
            if features:
                lines.append(f"- **CI features**: {', '.join(features)}")
        elif suffix == "branch_naming":
            strategy = _get_stat(rule, "strategy", "")
            if strategy:
                lines.append(f"- **Branch strategy**: {strategy}")
        elif suffix == "dockerfile":
            good = _get_stat(rule, "good_practice_count", 0)
            stages = _get_stat(rule, "from_count", 1)
            parts = []
            if stages > 1:
                parts.append(f"multi-stage ({stages} stages)")
            if good:
                parts.append(f"{good} best practices")
            if parts:
                lines.append(f"- **Docker**: {', '.join(parts)}")
            else:
                lines.append("- **Docker**: Dockerfile present")
        elif suffix == "docker_compose":
            svc_count = _get_stat(rule, "service_count", 0)
            features = _get_stat(rule, "features", [])
            parts = [f"{svc_count} services"]
            if features:
                parts.extend(features[:3])
            lines.append(f"- **Compose**: {', '.join(parts)}")
        elif suffix == "kubernetes":
            manifest_count = _get_stat(rule, "manifest_count", 0)
            has_helm = _get_stat(rule, "has_helm", False)
            has_kustomize = _get_stat(rule, "has_kustomize", False)
            parts = [f"{manifest_count} manifests"]
            if has_helm:
                parts.append("Helm")
            if has_kustomize:
                parts.append("Kustomize")
            lines.append(f"- **Kubernetes**: {', '.join(parts)}")

    lines.append("")
    return "\n".join(lines)


def _build_api_chains_section(include_rules: list[ConventionRule]) -> str:
    """Build API route reference grouped by route file."""
    # Collect routes and chains
    routes_by_file: dict[str, list[dict]] = {}
    chains: list[dict] = []

    for rule in include_rules:
        suffix = _get_suffix(rule)
        if suffix == "api_routes":
            for route in _get_stat(rule, "routes", []):
                f = route.get("file", "")
                if f:
                    routes_by_file.setdefault(f, []).append(route)
        elif suffix == "endpoint_chains":
            chains = _get_stat(rule, "chains", [])

    if not routes_by_file:
        return ""

    # Build chain lookup: endpoint file -> services/stores
    chain_by_file: dict[str, dict] = {}
    for chain in chains:
        ep = chain.get("endpoint", "")
        if ep:
            chain_by_file[ep] = chain

    # Check if chains are degenerate — when barrel imports / DI wiring causes
    # every chain to pull in all services + all stores, the chains provide no
    # useful per-route differentiation. Detect by checking if most chains
    # have large overlapping store sets.
    store_counts = [len(chain.get("stores", [])) for chain in chains]
    avg_stores = sum(store_counts) / len(store_counts) if store_counts else 0
    chains_are_degenerate = avg_stores > 10  # Barrel import explosion

    lines = ["\n### API Routes\n"]

    _MAX_ROUTE_ENTRIES = 12

    if chains_are_degenerate or not chains:
        # Show route files with their endpoints — more useful than identical chains
        sorted_files = sorted(routes_by_file.keys())
        for endpoint_file in sorted_files[:_MAX_ROUTE_ENTRIES]:
            file_routes = routes_by_file[endpoint_file]
            short = _short_path(endpoint_file)
            route_strs = []
            for r in file_routes[:4]:
                route_strs.append(f"`{r.get('method', '?')} {r.get('path', '?')}`")
            if len(file_routes) > 4:
                route_strs.append(f"+{len(file_routes) - 4} more")
            lines.append(f"- `{short}`: {', '.join(route_strs)}")
        if len(sorted_files) > _MAX_ROUTE_ENTRIES:
            lines.append(f"- ... and {len(sorted_files) - _MAX_ROUTE_ENTRIES} more route files")
    else:
        # Chains have differentiated services/stores — show the flow
        connected: list[str] = []
        seen_endpoints: set[str] = set()
        for chain in chains:
            endpoint_file = chain.get("endpoint", "")
            if endpoint_file in seen_endpoints:
                continue
            seen_endpoints.add(endpoint_file)

            file_routes = routes_by_file.get(endpoint_file, [])
            services = _unique_short_paths(chain.get("services", []))
            stores = _unique_short_paths(chain.get("stores", []))

            if not file_routes:
                continue
            route = file_routes[0]
            route_label = f"`{route.get('method', '?')} {route.get('path', '?')}`"
            if len(file_routes) > 1:
                route_label += f" (+{len(file_routes) - 1})"

            parts = [route_label, _short_path(endpoint_file)]
            for svc in services[:2]:
                parts.append(svc)
            if len(stores) > 5:
                raw_stores = [
                    s for s in chain.get("stores", [])
                    if not s.rsplit("/", 1)[-1].startswith("index.")
                ]
                store_dir = _common_store_dir(raw_stores)
                parts.append(f"`{store_dir}/`" if store_dir else f"{len(stores)} stores")
            elif stores:
                parts.append(stores[0])
            connected.append(" → ".join(parts))

        for entry in connected[:8]:
            lines.append(f"- {entry}")
        if len(connected) > 8:
            lines.append(f"- ... and {len(connected) - 8} more chains")

    lines.append("")
    return "\n".join(lines)


def _common_store_dir(file_list: list[str]) -> str:
    """Find the common parent directory for a list of store file paths."""
    if not file_list:
        return ""
    from collections import Counter
    parent_counts: Counter = Counter()
    for f in file_list:
        parts = f.replace("\\", "/").split("/")
        if len(parts) >= 2:
            parent_counts[parts[-2]] += 1
    if not parent_counts:
        return ""
    # If one directory dominates (>60%), use it; otherwise combine top 2
    top = parent_counts.most_common(2)
    total = sum(parent_counts.values())
    if len(top) == 1 or top[0][1] / total > 0.6:
        return top[0][0]
    return f"{top[0][0]}, {top[1][0]}"


def _unique_short_paths(file_list: list[str]) -> list[str]:
    """Deduplicate and shorten file paths, filtering out barrel/index files."""
    seen: set[str] = set()
    result: list[str] = []
    for f in file_list:
        short = _short_path(f)
        # Skip barrel export files
        basename = f.rsplit("/", 1)[-1] if "/" in f else f
        if basename in ("index.ts", "index.js", "index.mjs"):
            continue
        if short not in seen:
            seen.add(short)
            result.append(short)
    return result


def _short_path(filepath: str) -> str:
    """Shorten a file path for display (keep last 2 segments)."""
    parts = filepath.replace("\\", "/").split("/")
    if len(parts) <= 2:
        return filepath
    return "/".join(parts[-2:])


# --- Main generators ---


def generate_claude_md(output: ConventionsOutput) -> str:
    """Generate a CLAUDE.md from conventions output.

    Classifies each rule as exclude/tech_stack/include, then builds
    a structured document optimized for Claude Code context.
    """
    # Classify rules
    tech_rules: list[ConventionRule] = []
    include_rules: list[ConventionRule] = []

    for rule in output.rules:
        bucket = _classify_rule(rule)
        if bucket == "tech_stack":
            tech_rules.append(rule)
        elif bucket == "include":
            include_rules.append(rule)
        # "exclude" rules are dropped

    # Also pass tech_rules through include for framework detection
    all_relevant = tech_rules + include_rules

    # Extract project name from repo path
    project_name = Path(output.metadata.path).name

    sections: list[str] = []

    # Header
    sections.append(f"# CLAUDE.md - {project_name}\n")
    sections.append("> Auto-generated by conventions-cli. Customize and extend with project-specific context.\n")

    # Project Overview
    sections.append(_build_project_overview(output, all_relevant))

    # Directory Structure
    dir_map = _build_directory_map_section(include_rules)
    if dir_map:
        sections.append(dir_map)

    # Architecture (includes API surface + connected chains)
    arch = _build_architecture_section(include_rules)
    if arch:
        sections.append(arch)
        chains = _build_api_chains_section(include_rules)
        if chains:
            sections.append(chains)

    # Tech Stack
    sections.append(_build_tech_stack_section(tech_rules, output))

    # Environment Setup (prerequisites, services, env vars)
    env = _build_environment_section(include_rules)
    if env:
        sections.append(env)

    # Commands (enhanced with task runner data)
    sections.append(_build_commands_section(include_rules, tech_rules))

    # Conventions
    conv = _build_conventions_section(include_rules, tech_rules)
    if conv:
        sections.append(conv)

    # Generated Code warning
    gen_code = _build_generated_code_section(include_rules)
    if gen_code:
        sections.append(gen_code)

    # Deployment (CI/CD, containers, branch strategy)
    deploy = _build_deployment_section(tech_rules, include_rules)
    if deploy:
        sections.append(deploy)

    # Skeleton sections
    sections.append("## Decision Log\n")
    sections.append("[TODO: Record architectural decisions]\n")
    sections.append("## Known Pitfalls\n")
    sections.append("[TODO: Document gotchas and anti-patterns]\n")

    return "\n".join(sections)


def write_claude_md(
    output: ConventionsOutput,
    repo_root: Path,
    personal: bool = False,
) -> Path:
    """Write CLAUDE.md to the repo root or .claude/ directory.

    Args:
        output: Conventions scan output.
        repo_root: Path to the repository root.
        personal: If True, write to .claude/CLAUDE.md instead of root.

    Returns:
        Path to the written file.
    """
    content = generate_claude_md(output)

    if personal:
        target_dir = repo_root / ".claude"
        target_dir.mkdir(exist_ok=True)
        target_path = target_dir / "CLAUDE.md"
    else:
        target_path = repo_root / "CLAUDE.md"

    target_path.write_text(content, encoding="utf-8")
    return target_path
