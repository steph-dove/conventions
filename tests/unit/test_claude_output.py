"""Tests for CLAUDE.md output generator."""
from __future__ import annotations

import pytest

from conventions.outputs.claude import (
    _classify_rule,
    _summarize_rule,
    generate_claude_md,
    write_claude_md,
)
from conventions.schemas import ConventionRule, ConventionsOutput, RepoMetadata


def _make_rule(
    suffix: str,
    confidence: float = 0.90,
    category: str = "testing",
    title: str = "Test Rule",
    description: str = "A test rule",
    stats: dict | None = None,
    language: str | None = "node",
) -> ConventionRule:
    """Helper to create a rule with a given suffix."""
    return ConventionRule(
        id=f"node.conventions.{suffix}",
        category=category,
        title=title,
        description=description,
        confidence=confidence,
        language=language,
        stats=stats or {},
    )


def _make_output(rules: list[ConventionRule] | None = None) -> ConventionsOutput:
    """Helper to create a ConventionsOutput."""
    return ConventionsOutput(
        metadata=RepoMetadata(
            path="/test/my-project",
            detected_languages=["node"],
            total_files_scanned=100,
        ),
        rules=rules or [],
    )


class TestClassifyRule:
    """Tests for rule classification."""

    def test_excludes_low_confidence(self):
        """Rules below 0.70 confidence are excluded."""
        rule = _make_rule("framework", confidence=0.50)
        assert _classify_rule(rule) == "exclude"

    def test_excludes_noise_suffixes(self):
        """Known noise suffixes are excluded regardless of confidence."""
        for suffix in ("editor_config", "jsdoc", "docstrings", "barrel_exports"):
            rule = _make_rule(suffix, confidence=0.95)
            assert _classify_rule(rule) == "exclude", f"{suffix} should be excluded"

    def test_classifies_tech_stack(self):
        """Tool-oriented suffixes go to tech_stack."""
        for suffix in ("package_manager", "formatting", "linting", "testing_framework", "framework"):
            rule = _make_rule(suffix, confidence=0.90)
            assert _classify_rule(rule) == "tech_stack", f"{suffix} should be tech_stack"

    def test_classifies_include(self):
        """Architecture and convention suffixes are included."""
        for suffix in ("layer_separation", "middleware_patterns", "error_classes", "file_naming"):
            rule = _make_rule(suffix, confidence=0.85)
            assert _classify_rule(rule) == "include", f"{suffix} should be include"

    def test_unknown_suffix_is_included(self):
        """Unknown suffixes default to include (not exclude)."""
        rule = _make_rule("some_new_detector", confidence=0.80)
        assert _classify_rule(rule) == "include"

    def test_confidence_boundary(self):
        """Rules at exactly 0.70 are included (threshold is <0.70)."""
        rule = _make_rule("file_naming", confidence=0.70)
        assert _classify_rule(rule) == "include"

    def test_confidence_just_below_threshold(self):
        """Rules at 0.69 are excluded."""
        rule = _make_rule("file_naming", confidence=0.69)
        assert _classify_rule(rule) == "exclude"


class TestSummarizeRule:
    """Tests for rule summarization."""

    def test_file_naming_with_dominant_style(self):
        """File naming rule extracts dominant_style."""
        rule = _make_rule(
            "file_naming",
            stats={"dominant_style": "kebab-case", "dominant_percentage": 85},
        )
        result = _summarize_rule(rule)
        assert "kebab-case" in result
        assert "85%" in result

    def test_module_system_with_dominant(self):
        """Module system rule extracts dominant_system."""
        rule = _make_rule(
            "module_system",
            stats={"dominant_system": "CommonJS", "dominant_percentage": 90},
        )
        result = _summarize_rule(rule)
        assert "CommonJS" in result

    def test_typescript_ratio(self):
        """TypeScript rule extracts ts_ratio."""
        rule = _make_rule(
            "typescript",
            stats={"ts_ratio": 72},
        )
        result = _summarize_rule(rule)
        assert "72%" in result
        assert "TypeScript" in result

    def test_fallback_to_description(self):
        """Rules without known stats fall back to description."""
        rule = _make_rule(
            "some_custom_rule",
            description="This is a custom convention",
        )
        result = _summarize_rule(rule)
        assert result == "This is a custom convention"

    def test_long_description_truncated(self):
        """Long descriptions are truncated to 200 chars."""
        long_desc = "x" * 300
        rule = _make_rule("some_custom_rule", description=long_desc)
        result = _summarize_rule(rule)
        assert len(result) == 200
        assert result.endswith("...")

    def test_import_graph_summary(self):
        """Import graph rule summarizes file and edge counts."""
        rule = _make_rule(
            "import_graph",
            stats={"total_files": 42, "total_edges": 85, "cycle_count": 3},
        )
        result = _summarize_rule(rule)
        assert "42 files" in result
        assert "85 internal imports" in result
        assert "3 circular deps" in result

    def test_endpoint_chains_summary(self):
        """Endpoint chains rule summarizes chain count."""
        rule = _make_rule("endpoint_chains", stats={"chain_count": 7})
        result = _summarize_rule(rule)
        assert "7 traced endpoint chains" in result

    def test_service_dependencies_summary(self):
        """Service dependencies rule summarizes dependency count."""
        rule = _make_rule("service_dependencies", stats={"dependency_count": 4})
        result = _summarize_rule(rule)
        assert "4 service dependencies mapped" in result

    def test_api_routes_summary(self):
        """API routes rule summarizes total and methods."""
        rule = _make_rule("api_routes", stats={
            "total_routes": 15,
            "methods": {"GET": 8, "POST": 4, "PUT": 2, "DELETE": 1},
        })
        result = _summarize_rule(rule)
        assert "15 API endpoints" in result
        assert "GET: 8" in result

    def test_task_runner_summary(self):
        """Task runner rule summarizes runners and targets."""
        rule = _make_rule("task_runner", stats={
            "runners_found": ["makefile", "package_json"],
            "total_targets": 12,
        })
        result = _summarize_rule(rule)
        assert "makefile" in result
        assert "12 targets" in result

    def test_db_migrations_summary(self):
        """DB migrations rule summarizes tool and count."""
        rule = _make_rule("db_migrations", stats={
            "primary_tool": "prisma",
            "total_migration_files": 8,
        })
        result = _summarize_rule(rule)
        assert "prisma" in result
        assert "8 migrations" in result

    def test_dependency_health_summary(self):
        """Dependency health rule summarizes pinning strategy."""
        rule = _make_rule("dependency_health", stats={
            "pinning_strategy": "caret",
            "total_deps": 25,
            "has_lock_file": True,
        })
        result = _summarize_rule(rule)
        assert "caret pinning" in result
        assert "25 deps" in result
        assert "lock file" in result

    def test_config_access_summary(self):
        """Config access rule summarizes library name."""
        rule = _make_rule("config_access", stats={
            "access_style": "library",
            "libraries": {"node_dotenv": 15, "config": 3},
        })
        result = _summarize_rule(rule)
        assert "dotenv" in result

    def test_code_owners_summary(self):
        """Code owners rule summarizes owner count."""
        rule = _make_rule("code_owners", stats={
            "owner_count": 5,
            "rule_count": 12,
        })
        result = _summarize_rule(rule)
        assert "5 owners" in result
        assert "12 rules" in result

    def test_go_migrations_summary(self):
        """Go migrations rule (suffix 'migrations') summarizes tool and count."""
        rule = ConventionRule(
            id="go.conventions.migrations",
            category="database",
            title="DB migrations",
            description="golang-migrate with 5 migrations",
            confidence=0.90,
            language="go",
            stats={"primary_tool": "golang-migrate", "migration_file_count": 5},
        )
        result = _summarize_rule(rule)
        assert "golang-migrate" in result
        assert "5 migrations" in result

    def test_commit_messages_conventional(self):
        """Commit messages summarizer for conventional commits."""
        rule = _make_rule("commit_messages", stats={
            "convention": "conventional",
            "conventional_ratio": 0.85,
        })
        result = _summarize_rule(rule)
        assert "Conventional Commits" in result
        assert "feat:" in result

    def test_commit_messages_ticket(self):
        """Commit messages summarizer for ticket-prefixed."""
        rule = _make_rule("commit_messages", stats={"convention": "ticket"})
        result = _summarize_rule(rule)
        assert "Ticket-prefixed" in result

    def test_pr_template_with_sections(self):
        """PR template summarizer with sections."""
        rule = _make_rule("pr_template", stats={
            "sections": ["Description", "Testing", "Checklist"],
            "has_multiple_templates": False,
        })
        result = _summarize_rule(rule)
        assert "Description" in result
        assert "Testing" in result

    def test_pr_template_multiple(self):
        """PR template summarizer for multiple templates."""
        rule = _make_rule("pr_template", stats={
            "has_multiple_templates": True,
            "template_count": 3,
        })
        result = _summarize_rule(rule)
        assert "3 PR templates" in result


class TestGenerateClaudeMd:
    """Tests for the main generate_claude_md function."""

    def test_empty_rules_produces_skeleton(self):
        """Empty rules still produce a valid CLAUDE.md with skeleton sections."""
        output = _make_output([])
        result = generate_claude_md(output)

        assert "# CLAUDE.md - my-project" in result
        assert "## Project Overview" in result
        assert "## Tech Stack" in result
        assert "## Commands" in result
        assert "## Decision Log" in result
        assert "## Known Pitfalls" in result
        assert "[TODO:" in result

    def test_project_name_from_path(self):
        """Project name is extracted from repo path."""
        output = ConventionsOutput(
            metadata=RepoMetadata(
                path="/home/user/projects/awesome-app",
                detected_languages=["python"],
                total_files_scanned=50,
            ),
            rules=[],
        )
        result = generate_claude_md(output)
        assert "# CLAUDE.md - awesome-app" in result

    def test_tech_stack_rules_appear_in_section(self):
        """Tech stack rules appear in the Tech Stack section."""
        rules = [
            _make_rule("package_manager", stats={"primary_manager": "npm"}),
            _make_rule("testing_framework", stats={"primary_framework": "Jest"}),
            _make_rule("linting", stats={"primary_tool": "ESLint"}),
        ]
        output = _make_output(rules)
        result = generate_claude_md(output)

        assert "npm" in result
        assert "Jest" in result
        assert "ESLint" in result

    def test_architecture_rules_create_section(self):
        """Architecture rules create a Key Patterns section."""
        rules = [
            _make_rule(
                "middleware_patterns",
                title="Express Middleware",
                description="Uses Express-style middleware chain",
            ),
            _make_rule(
                "layer_separation",
                title="Layered Architecture",
                description="Controllers, services, repositories pattern",
            ),
        ]
        output = _make_output(rules)
        result = generate_claude_md(output)

        assert "## Architecture" in result
        assert "### Key Patterns" in result
        assert "Express Middleware" in result
        assert "Layered Architecture" in result

    def test_excluded_rules_not_in_output(self):
        """Excluded rules (noise) do not appear in output."""
        rules = [
            _make_rule("editor_config", title="Editor Config"),
            _make_rule("jsdoc", title="JSDoc Style"),
            _make_rule("file_naming", title="File Naming", stats={"dominant_style": "kebab-case"}),
        ]
        output = _make_output(rules)
        result = generate_claude_md(output)

        assert "Editor Config" not in result
        assert "JSDoc Style" not in result
        assert "File Naming" in result  # This one should be included

    def test_low_confidence_rules_excluded(self):
        """Rules below confidence threshold are excluded from all sections."""
        rules = [
            _make_rule("framework", confidence=0.50, stats={"primary_framework": "Express"}),
        ]
        output = _make_output(rules)
        result = generate_claude_md(output)

        assert "Express" not in result

    def test_conventions_section_with_rules(self):
        """Convention rules create a Conventions section."""
        rules = [
            _make_rule("file_naming", title="File Naming", stats={"dominant_style": "camelCase", "dominant_percentage": 80}),
            _make_rule("async_style", title="Async Style", stats={"dominant_style": "async/await"}),
        ]
        output = _make_output(rules)
        result = generate_claude_md(output)

        assert "## Conventions" in result
        assert "camelCase" in result
        assert "async/await" in result

    def test_auto_generated_header(self):
        """Output includes auto-generated notice."""
        output = _make_output([])
        result = generate_claude_md(output)
        assert "Auto-generated by conventions-cli" in result

    def test_commands_inferred_from_npm(self):
        """Commands section infers npm commands."""
        rules = [
            _make_rule("package_manager", stats={"primary_manager": "npm"}),
            _make_rule("testing_framework", stats={"primary_framework": "Jest"}),
        ]
        output = _make_output(rules)
        result = generate_claude_md(output)

        assert "npm install" in result
        assert "npm test" in result

    def test_commands_from_task_runner(self):
        """Commands section uses task runner data when available."""
        rules = [
            _make_rule("package_manager", stats={"primary_manager": "npm"}),
            _make_rule(
                "task_runner",
                title="Task runners",
                stats={
                    "runners_found": ["makefile"],
                    "primary_runner": "makefile",
                    "total_targets": 3,
                    "targets": {
                        "makefile": [
                            {"name": "build", "description": "Build the project"},
                            {"name": "test", "description": "Run tests"},
                            {"name": "lint", "description": ""},
                        ],
                    },
                },
            ),
        ]
        output = _make_output(rules)
        result = generate_claude_md(output)

        assert "make build" in result
        assert "make test" in result
        assert "make lint" in result
        assert "Build the project" in result

    def test_environment_section(self):
        """Environment section shows prerequisites and services."""
        rules = [
            _make_rule(
                "runtime_prerequisites",
                title="Runtime prerequisites",
                stats={
                    "tools": [
                        {"name": "node", "version": "20.10.0", "source": ".node-version"},
                    ],
                },
                language="generic",
            ),
            _make_rule(
                "required_services",
                title="Required services",
                stats={
                    "services": [
                        {"name": "postgres", "image": "postgres:15"},
                        {"name": "redis", "image": "redis:7"},
                    ],
                    "total_services": 2,
                },
                language="generic",
            ),
        ]
        output = _make_output(rules)
        result = generate_claude_md(output)

        assert "## Environment Setup" in result
        assert "### Prerequisites" in result
        assert "node" in result
        assert "20.10.0" in result
        assert "### Required Services" in result
        assert "postgres" in result
        assert "redis" in result

    def test_deployment_section(self):
        """Deployment section shows CI, Docker, and branch info."""
        rules = [
            _make_rule("ci_platform", stats={"platforms": ["github_actions"]}),
            _make_rule("ci_quality", stats={
                "has_test_workflow": True,
                "has_lint_workflow": True,
                "has_deploy_workflow": True,
                "has_caching": False,
                "has_matrix": False,
            }),
            _make_rule("branch_naming", stats={"strategy": "gitflow"}),
            _make_rule("dockerfile", stats={"good_practice_count": 3, "from_count": 2}),
            _make_rule("kubernetes", stats={
                "tools": ["kubectl"],
                "manifest_count": 5,
                "has_helm": True,
                "has_kustomize": False,
            }),
        ]
        output = _make_output(rules)
        result = generate_claude_md(output)

        assert "## Deployment" in result
        assert "github_actions" in result
        assert "tests" in result
        assert "deploy" in result
        assert "gitflow" in result
        assert "multi-stage" in result
        assert "Helm" in result

    def test_api_chains_section(self):
        """API chains section links routes to endpoint chains."""
        rules = [
            _make_rule(
                "api_routes",
                title="API routes",
                stats={
                    "routes": [
                        {"method": "GET", "path": "/api/users", "file": "src/routes/users.ts", "line": 10},
                        {"method": "POST", "path": "/api/users", "file": "src/routes/users.ts", "line": 20},
                    ],
                    "total_routes": 2,
                    "methods": {"GET": 1, "POST": 1},
                },
            ),
            _make_rule(
                "endpoint_chains",
                title="Endpoint chains",
                stats={
                    "chain_count": 1,
                    "chains": [
                        {
                            "endpoint": "src/routes/users.ts",
                            "services": ["src/services/userService.ts"],
                            "stores": ["src/store/userRepo.ts"],
                            "depth": 3,
                        },
                    ],
                },
            ),
        ]
        output = _make_output(rules)
        result = generate_claude_md(output)

        assert "### API Routes" in result
        assert "GET /api/users" in result
        assert "(+1)" in result  # POST is grouped with GET (same endpoint file)
        assert "userService.ts" in result
        assert "userRepo.ts" in result

    def test_api_chains_filters_barrel_exports(self):
        """API chains skip index.ts barrel export files."""
        rules = [
            _make_rule(
                "api_routes",
                title="API routes",
                stats={
                    "routes": [
                        {"method": "GET", "path": "/api/items", "file": "src/routes/items.ts", "line": 5},
                    ],
                    "total_routes": 1,
                    "methods": {"GET": 1},
                },
            ),
            _make_rule(
                "endpoint_chains",
                title="Endpoint chains",
                stats={
                    "chain_count": 1,
                    "chains": [
                        {
                            "endpoint": "src/routes/items.ts",
                            "services": ["src/services/index.ts", "src/services/itemService.ts"],
                            "stores": ["src/db/index.ts", "src/db/itemRepo.ts"],
                            "depth": 3,
                        },
                    ],
                },
            ),
        ]
        output = _make_output(rules)
        result = generate_claude_md(output)

        assert "itemService.ts" in result
        assert "itemRepo.ts" in result
        # Barrel exports should be filtered out
        assert "index.ts" not in result

    def test_api_chains_collapses_many_stores(self):
        """API chains show directory name instead of individual files when >5 stores."""
        rules = [
            _make_rule(
                "api_routes",
                title="API routes",
                stats={
                    "routes": [
                        {"method": "GET", "path": "/api/users", "file": "src/routes/users.ts", "line": 5},
                    ],
                    "total_routes": 1,
                    "methods": {"GET": 1},
                },
            ),
            _make_rule(
                "endpoint_chains",
                title="Endpoint chains",
                stats={
                    "chain_count": 1,
                    "chains": [
                        {
                            "endpoint": "src/routes/users.ts",
                            "services": ["src/services/userService.ts"],
                            "stores": [
                                "src/data-store/mongo-database/users.ts",
                                "src/data-store/mongo-database/invoices.ts",
                                "src/data-store/mongo-database/orders.ts",
                                "src/data-store/mongo-database/products.ts",
                                "src/data-store/mongo-database/settings.ts",
                                "src/data-store/mongo-database/audit.ts",
                                "src/data-store/mongo-database/notifications.ts",
                            ],
                            "depth": 3,
                        },
                    ],
                },
            ),
        ]
        output = _make_output(rules)
        result = generate_claude_md(output)

        # Should show directory name, not individual store files
        assert "mongo-database" in result
        # Should NOT list individual store files
        assert "users.ts" not in result or "mongo-database/" in result

    def test_structured_logging_suppressed_when_library_present(self):
        """structured_logging convention suppressed when logging_library in tech stack."""
        rules = [
            _make_rule("logging_library", stats={"primary_library": "pino"}),
            _make_rule("structured_logging", title="Console.log logging",
                       description="Relies on console.log"),
        ]
        output = _make_output(rules)
        result = generate_claude_md(output)

        # logging_library should appear in tech stack
        assert "pino" in result
        # structured_logging (console.log) should NOT appear in conventions
        assert "Console.log logging" not in result

    def test_go_migrations_in_conventions(self):
        """Go migrations rule (suffix 'migrations') appears in Conventions section."""
        rules = [
            ConventionRule(
                id="go.conventions.migrations",
                category="database",
                title="DB migrations",
                description="Uses golang-migrate",
                confidence=0.90,
                language="go",
                stats={"primary_tool": "golang-migrate", "migration_file_count": 5},
            ),
        ]
        output = _make_output(rules)
        result = generate_claude_md(output)

        assert "## Conventions" in result
        assert "golang-migrate" in result

    def test_directory_map_renders(self):
        """Directory map section renders from repo_layout rule."""
        rules = [
            _make_rule("repo_layout", stats={
                "found_directories": ["src", "tests"],
                "directory_tree": {
                    "src": {
                        "purpose": "source code",
                        "children": {
                            "routes": {"purpose": "", "children": {}},
                            "services": {"purpose": "", "children": {}},
                        },
                    },
                    "tests": {
                        "purpose": "tests",
                        "children": {},
                    },
                },
            }),
        ]
        output = _make_output(rules)
        result = generate_claude_md(output)

        assert "## Directory Structure" in result
        assert "`src/` — source code" in result
        assert "`routes/`" in result
        assert "`services/`" in result
        assert "`tests/` — tests" in result

    def test_repo_layout_no_longer_excluded(self):
        """repo_layout with high confidence is classified as include."""
        rule = _make_rule("repo_layout", confidence=0.90)
        assert _classify_rule(rule) == "include"

    def test_import_aliases_node_output(self):
        """Node import aliases render in Conventions."""
        rules = [
            _make_rule("import_aliases", stats={
                "aliases": {"@/*": "src/*", "@utils/*": "src/utils/*"},
                "base_url": ".",
            }),
        ]
        output = _make_output(rules)
        result = generate_claude_md(output)

        assert "## Conventions" in result
        assert "@/*" in result
        assert "src/*" in result

    def test_monorepo_package_list_renders(self):
        """Monorepo packages render in Architecture section."""
        rules = [
            _make_rule("monorepo", title="Monorepo: Turborepo", stats={
                "tools": ["turborepo"],
                "primary_tool": "turborepo",
                "package_count": 2,
                "packages": [
                    {"name": "@org/api", "path": "packages/api"},
                    {"name": "@org/shared", "path": "packages/shared"},
                ],
            }),
        ]
        output = _make_output(rules)
        result = generate_claude_md(output)

        assert "## Architecture" in result
        assert "@org/api" in result
        assert "packages/api" in result
        assert "@org/shared" in result

    def test_generated_code_section_renders(self):
        """Generated code section renders directories and configs."""
        rules = [
            _make_rule("generated_code", stats={
                "generated_dirs": ["generated"],
                "codegen_configs": ["codegen.yml", "buf.gen.yaml"],
                "generated_file_patterns": ["*.pb.go"],
                "marker_count": 3,
            }),
        ]
        output = _make_output(rules)
        result = generate_claude_md(output)

        assert "## Generated Code (do not edit)" in result
        assert "`generated/`" in result
        assert "`*.pb.go`" in result
        assert "`codegen.yml`" in result

    def test_import_aliases_go_output(self):
        """Go import aliases render module path."""
        rules = [
            ConventionRule(
                id="go.conventions.import_aliases",
                category="language",
                title="Go module import path",
                description="Import prefix: github.com/myorg/myapp",
                confidence=0.95,
                language="go",
                stats={"module_path": "github.com/myorg/myapp"},
            ),
        ]
        output = _make_output(rules)
        result = generate_claude_md(output)

        assert "github.com/myorg/myapp" in result

    def test_single_test_command_pytest(self):
        """Single test command template for pytest."""
        rules = [
            _make_rule("package_manager", stats={"primary_manager": "pip"}, language="python"),
            _make_rule("testing_framework", stats={"primary_framework": "pytest"}, language="python"),
        ]
        output = _make_output(rules)
        result = generate_claude_md(output)

        assert "Test single" in result
        assert "pytest path/to/test.py::TestClass::test_method" in result

    def test_single_test_command_jest(self):
        """Single test command template for Jest."""
        rules = [
            _make_rule("package_manager", stats={"primary_manager": "npm"}),
            _make_rule("testing_framework", stats={"primary_framework": "Jest"}),
        ]
        output = _make_output(rules)
        result = generate_claude_md(output)

        assert "Test single" in result
        assert "npx jest" in result
        assert "--testPathPattern" in result

    def test_single_test_command_go(self):
        """Single test command template for Go."""
        rules = [
            _make_rule("testing_framework", stats={"primary_framework": "go"}, language="go"),
        ]
        output = ConventionsOutput(
            metadata=RepoMetadata(
                path="/test/my-project",
                detected_languages=["go"],
                total_files_scanned=100,
            ),
            rules=rules,
        )
        result = generate_claude_md(output)

        assert "Test single" in result
        assert "go test" in result
        assert "-run" in result

    def test_single_test_command_with_task_runner(self):
        """Single test template appears even with task runner present."""
        rules = [
            _make_rule("package_manager", stats={"primary_manager": "npm"}),
            _make_rule("testing_framework", stats={"primary_framework": "Jest"}),
            _make_rule(
                "task_runner",
                title="Task runners",
                stats={
                    "runners_found": ["makefile"],
                    "primary_runner": "makefile",
                    "total_targets": 1,
                    "targets": {
                        "makefile": [{"name": "test", "description": "Run tests"}],
                    },
                },
            ),
        ]
        output = _make_output(rules)
        result = generate_claude_md(output)

        assert "make test" in result
        assert "Test single" in result
        assert "npx jest" in result

    def test_db_entities_in_architecture(self):
        """Database entities render in Architecture section."""
        rules = [
            _make_rule("db_entities", title="Database entities", stats={
                "entities": [
                    {"name": "User", "file": "models/user.py"},
                    {"name": "Order", "file": "models/order.py"},
                    {"name": "Product", "file": "models/product.py"},
                ],
                "entity_count": 3,
                "orm": "sqlalchemy",
            }),
        ]
        output = _make_output(rules)
        result = generate_claude_md(output)

        assert "## Architecture" in result
        assert "3 sqlalchemy entities" in result
        assert "User" in result
        assert "Order" in result
        assert "Product" in result

    def test_commands_inferred_from_pytest(self):
        """Commands section infers pytest commands."""
        rules = [
            _make_rule("package_manager", stats={"primary_manager": "pip"}, language="python"),
            _make_rule("testing_framework", stats={"primary_framework": "pytest"}, language="python"),
        ]
        output = ConventionsOutput(
            metadata=RepoMetadata(
                path="/test/my-project",
                detected_languages=["python"],
                total_files_scanned=100,
            ),
            rules=rules,
        )
        result = generate_claude_md(output)

        assert "pip install" in result
        assert "pytest" in result


    def test_project_description_in_overview(self):
        """Project description from repo_layout shows in Project Overview."""
        rules = [
            ConventionRule(
                id="generic.conventions.repo_layout",
                category="structure",
                title="Standard repository layout",
                description="Has standard directories",
                confidence=0.8,
                language="generic",
                stats={
                    "found_directories": ["src"],
                    "directory_tree": {},
                    "project_description": "Property management application",
                },
            ),
        ]
        output = _make_output(rules)
        result = generate_claude_md(output)

        assert "## Project Overview" in result
        assert "Property management application" in result


class TestWriteClaudeMd:
    """Tests for write_claude_md file writing."""

    def test_writes_to_project_root(self, tmp_path):
        """Default writes CLAUDE.md to project root."""
        output = _make_output([])
        path = write_claude_md(output, tmp_path)

        assert path == tmp_path / "CLAUDE.md"
        assert path.exists()
        content = path.read_text()
        assert "# CLAUDE.md" in content

    def test_writes_to_claude_dir_when_personal(self, tmp_path):
        """With personal=True, writes to .claude/CLAUDE.md."""
        output = _make_output([])
        path = write_claude_md(output, tmp_path, personal=True)

        assert path == tmp_path / ".claude" / "CLAUDE.md"
        assert path.exists()
        assert (tmp_path / ".claude").is_dir()

    def test_creates_claude_dir_if_missing(self, tmp_path):
        """.claude/ directory is created if it doesn't exist."""
        output = _make_output([])
        claude_dir = tmp_path / ".claude"
        assert not claude_dir.exists()

        write_claude_md(output, tmp_path, personal=True)
        assert claude_dir.exists()

    def test_overwrites_existing_file(self, tmp_path):
        """Overwrites existing CLAUDE.md."""
        existing = tmp_path / "CLAUDE.md"
        existing.write_text("old content")

        output = _make_output([])
        write_claude_md(output, tmp_path)

        content = existing.read_text()
        assert "old content" not in content
        assert "# CLAUDE.md" in content
