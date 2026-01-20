"""Node.js linting conventions detector."""

from __future__ import annotations

import json

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import NodeDetector


@DetectorRegistry.register
class NodeLintingDetector(NodeDetector):
    """Detect Node.js linting conventions."""

    name = "node_linting"
    description = "Detects ESLint, Biome, and other linting configurations"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect linting conventions."""
        result = DetectorResult()

        linters: dict[str, dict] = {}

        # Check for ESLint
        eslint_configs = [
            ".eslintrc",
            ".eslintrc.js",
            ".eslintrc.cjs",
            ".eslintrc.json",
            ".eslintrc.yml",
            ".eslintrc.yaml",
            "eslint.config.js",  # Flat config
            "eslint.config.mjs",
            "eslint.config.cjs",
        ]
        for config in eslint_configs:
            if (ctx.repo_root / config).exists():
                is_flat = config.startswith("eslint.config")
                linters["eslint"] = {
                    "name": "ESLint",
                    "config": config,
                    "flat_config": is_flat,
                }
                break

        # Check package.json for eslintConfig
        pkg_json_path = ctx.repo_root / "package.json"
        if "eslint" not in linters and pkg_json_path.exists():
            try:
                pkg_data = json.loads(pkg_json_path.read_text())
                if "eslintConfig" in pkg_data:
                    linters["eslint"] = {
                        "name": "ESLint",
                        "config": "package.json",
                        "flat_config": False,
                    }
            except (json.JSONDecodeError, OSError):
                pass

        # Check for Biome (formerly Rome)
        biome_configs = ["biome.json", "biome.jsonc"]
        for config in biome_configs:
            if (ctx.repo_root / config).exists():
                linters["biome"] = {"name": "Biome", "config": config}
                break

        # Check for Rome (legacy)
        if (ctx.repo_root / "rome.json").exists():
            linters["rome"] = {"name": "Rome", "config": "rome.json"}

        # Check for StandardJS
        if pkg_json_path.exists():
            try:
                pkg_data = json.loads(pkg_json_path.read_text())
                all_deps = {
                    **pkg_data.get("dependencies", {}),
                    **pkg_data.get("devDependencies", {}),
                }
                if "standard" in all_deps:
                    linters["standard"] = {"name": "StandardJS", "in_deps": True}
            except (json.JSONDecodeError, OSError):
                pass

        # Check for TSLint (deprecated but still in use)
        if (ctx.repo_root / "tslint.json").exists():
            linters["tslint"] = {
                "name": "TSLint (deprecated)",
                "config": "tslint.json",
            }

        # Detect ESLint plugins/presets
        eslint_features = []
        if "eslint" in linters and pkg_json_path.exists():
            try:
                pkg_data = json.loads(pkg_json_path.read_text())
                all_deps = {
                    **pkg_data.get("dependencies", {}),
                    **pkg_data.get("devDependencies", {}),
                }

                if "@typescript-eslint/eslint-plugin" in all_deps:
                    eslint_features.append("TypeScript")

                if "eslint-plugin-react" in all_deps or "eslint-plugin-react-hooks" in all_deps:
                    eslint_features.append("React")

                if "eslint-plugin-vue" in all_deps:
                    eslint_features.append("Vue")

                if "eslint-plugin-prettier" in all_deps:
                    eslint_features.append("Prettier integration")

                if "eslint-plugin-import" in all_deps:
                    eslint_features.append("import rules")

                if "eslint-plugin-jest" in all_deps:
                    eslint_features.append("Jest")

                if "eslint-plugin-security" in all_deps:
                    eslint_features.append("security")

                linters["eslint"]["features"] = eslint_features

            except (json.JSONDecodeError, OSError):
                pass

        if not linters:
            return result

        primary = list(linters.keys())[0]
        linter_info = linters[primary]

        title = f"Linting: {linter_info['name']}"
        description = f"Uses {linter_info['name']} for code linting."

        if primary == "eslint":
            if linter_info.get("flat_config"):
                description += " Uses flat config format."
            features = linter_info.get("features", [])
            if features:
                description += f" Plugins: {', '.join(features[:4])}."

        if len(linters) > 1:
            others = [lib["name"] for k, lib in linters.items() if k != primary]
            description += f" Also: {', '.join(others)}."

        confidence = 0.95

        result.rules.append(self.make_rule(
            rule_id="node.conventions.linting",
            category="tooling",
            title=title,
            description=description,
            confidence=confidence,
            language="javascript",
            evidence=[],
            stats={
                "linters": list(linters.keys()),
                "primary_linter": primary,
                "eslint_features": eslint_features if "eslint" in linters else [],
                "linter_details": linters,
            },
        ))

        return result
