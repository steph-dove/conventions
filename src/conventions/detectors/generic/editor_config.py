"""Editor configuration detector."""

from __future__ import annotations

from pathlib import Path

from ..base import BaseDetector, DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from ...fs import read_file_safe


@DetectorRegistry.register
class EditorConfigDetector(BaseDetector):
    """Detect editor configuration patterns."""

    name = "generic_editor_config"
    description = "Detects editor configuration and code style settings"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect editor configuration patterns."""
        result = DetectorResult()

        configs: dict[str, dict] = {}

        # .editorconfig
        editorconfig = ctx.repo_root / ".editorconfig"
        if editorconfig.is_file():
            content = read_file_safe(editorconfig)
            settings = []
            if content:
                if "indent_style" in content:
                    settings.append("indent style")
                if "indent_size" in content:
                    settings.append("indent size")
                if "end_of_line" in content:
                    settings.append("line endings")
                if "trim_trailing_whitespace" in content:
                    settings.append("trailing whitespace")
                if "insert_final_newline" in content:
                    settings.append("final newline")

            configs["editorconfig"] = {
                "name": "EditorConfig",
                "settings": settings,
            }

        # VS Code settings
        vscode_settings = ctx.repo_root / ".vscode" / "settings.json"
        if vscode_settings.is_file():
            content = read_file_safe(vscode_settings)
            features = []
            if content:
                if "editor.formatOnSave" in content:
                    features.append("format on save")
                if "editor.defaultFormatter" in content:
                    features.append("default formatter")
                if "editor.tabSize" in content:
                    features.append("tab size")
                if "files.exclude" in content:
                    features.append("file exclusions")

            configs["vscode"] = {
                "name": "VS Code",
                "features": features,
            }

        # VS Code extensions recommendations
        vscode_extensions = ctx.repo_root / ".vscode" / "extensions.json"
        if vscode_extensions.is_file():
            if "vscode" in configs:
                configs["vscode"]["has_extensions"] = True
            else:
                configs["vscode"] = {
                    "name": "VS Code",
                    "features": ["extension recommendations"],
                    "has_extensions": True,
                }

        # JetBrains IDE config
        idea_dir = ctx.repo_root / ".idea"
        if idea_dir.is_dir():
            configs["jetbrains"] = {
                "name": "JetBrains IDE",
            }

        if not configs:
            return result

        config_names = [c["name"] for c in configs.values()]
        title = f"Editor config: {', '.join(config_names)}"

        descriptions = []
        for config_id, config_info in configs.items():
            if config_id == "editorconfig" and config_info.get("settings"):
                descriptions.append(f"EditorConfig ({len(config_info['settings'])} settings)")
            elif config_id == "vscode" and config_info.get("features"):
                desc = "VS Code"
                if config_info.get("has_extensions"):
                    desc += " with extensions"
                descriptions.append(desc)
            else:
                descriptions.append(config_info["name"])

        description = f"Editor configuration: {', '.join(descriptions)}."
        confidence = min(0.9, 0.6 + len(configs) * 0.15)

        result.rules.append(self.make_rule(
            rule_id="generic.conventions.editor_config",
            category="tooling",
            title=title,
            description=description,
            confidence=confidence,
            language="generic",
            evidence=[],
            stats={
                "configs": list(configs.keys()),
                "config_details": configs,
            },
        ))

        return result
