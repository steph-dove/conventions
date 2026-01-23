"""Node.js formatting conventions detector."""

from __future__ import annotations

import json

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import NodeDetector


@DetectorRegistry.register
class NodeFormattingDetector(NodeDetector):
    """Detect Node.js formatting conventions."""

    name = "node_formatting"
    description = "Detects Prettier, Biome, and other code formatters"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect formatting conventions."""
        result = DetectorResult()

        formatters: dict[str, dict] = {}

        # Check for Prettier
        prettier_configs = [
            ".prettierrc",
            ".prettierrc.json",
            ".prettierrc.yml",
            ".prettierrc.yaml",
            ".prettierrc.js",
            ".prettierrc.cjs",
            ".prettierrc.mjs",
            "prettier.config.js",
            "prettier.config.cjs",
            "prettier.config.mjs",
        ]
        for config in prettier_configs:
            if (ctx.repo_root / config).exists():
                formatters["prettier"] = {"name": "Prettier", "config": config}
                break

        # Check package.json for prettier config
        pkg_json_path = ctx.repo_root / "package.json"
        if "prettier" not in formatters and pkg_json_path.exists():
            try:
                pkg_data = json.loads(pkg_json_path.read_text())
                if "prettier" in pkg_data:
                    formatters["prettier"] = {
                        "name": "Prettier",
                        "config": "package.json",
                    }
            except (json.JSONDecodeError, OSError):
                pass

        # Check for .prettierignore
        if (ctx.repo_root / ".prettierignore").exists():
            if "prettier" in formatters:
                formatters["prettier"]["has_ignore"] = True
            else:
                formatters["prettier"] = {
                    "name": "Prettier",
                    "config": "inferred",
                    "has_ignore": True,
                }

        # Check for Biome (also a formatter)
        biome_configs = ["biome.json", "biome.jsonc"]
        for config in biome_configs:
            if (ctx.repo_root / config).exists():
                formatters["biome"] = {"name": "Biome", "config": config}
                break

        # Check for dprint
        dprint_configs = ["dprint.json", ".dprint.json"]
        for config in dprint_configs:
            if (ctx.repo_root / config).exists():
                formatters["dprint"] = {"name": "dprint", "config": config}
                break

        # Check package.json dependencies for formatters
        if pkg_json_path.exists():
            try:
                pkg_data = json.loads(pkg_json_path.read_text())
                all_deps = {
                    **pkg_data.get("dependencies", {}),
                    **pkg_data.get("devDependencies", {}),
                }

                if "prettier" in all_deps and "prettier" not in formatters:
                    formatters["prettier"] = {
                        "name": "Prettier",
                        "in_deps": True,
                    }

            except (json.JSONDecodeError, OSError):
                pass

        # Detect Prettier plugins
        prettier_plugins = []
        if "prettier" in formatters and pkg_json_path.exists():
            try:
                pkg_data = json.loads(pkg_json_path.read_text())
                all_deps = {
                    **pkg_data.get("dependencies", {}),
                    **pkg_data.get("devDependencies", {}),
                }

                plugin_mapping = {
                    "prettier-plugin-tailwindcss": "Tailwind CSS",
                    "@prettier/plugin-php": "PHP",
                    "@prettier/plugin-xml": "XML",
                    "prettier-plugin-organize-imports": "import organization",
                    "prettier-plugin-packagejson": "package.json sorting",
                    "prettier-plugin-sql": "SQL",
                    "prettier-plugin-prisma": "Prisma",
                }

                for dep, label in plugin_mapping.items():
                    if dep in all_deps:
                        prettier_plugins.append(label)

                formatters["prettier"]["plugins"] = prettier_plugins

            except (json.JSONDecodeError, OSError):
                pass

        if not formatters:
            return result

        primary = list(formatters.keys())[0]
        formatter_info = formatters[primary]

        title = f"Formatting: {formatter_info['name']}"
        description = f"Uses {formatter_info['name']} for code formatting."

        if primary == "prettier":
            plugins = formatter_info.get("plugins", [])
            if plugins:
                description += f" Plugins: {', '.join(plugins[:3])}."
            if formatter_info.get("has_ignore"):
                description += " Has .prettierignore."

        if len(formatters) > 1:
            others = [f["name"] for k, f in formatters.items() if k != primary]
            description += f" Also: {', '.join(others)}."

        confidence = 0.95

        result.rules.append(self.make_rule(
            rule_id="node.conventions.formatting",
            category="tooling",
            title=title,
            description=description,
            confidence=confidence,
            language="javascript",
            evidence=[],
            stats={
                "formatters": list(formatters.keys()),
                "primary_formatter": primary,
                "prettier_plugins": prettier_plugins if "prettier" in formatters else [],
                "formatter_details": formatters,
            },
        ))

        return result
