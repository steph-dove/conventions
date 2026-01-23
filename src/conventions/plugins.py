"""Plugin system for custom convention detectors and rating rules.

Plugins allow users to define custom detectors and rating rules in external
Python files that are loaded at runtime.

Example plugin file (my_custom_rules.py):

    from conventions.detectors.base import BaseDetector, DetectorResult

    class MyDetector(BaseDetector):
        name = "my_custom_detector"
        description = "My custom convention detector"
        languages = {"python"}

        def detect(self, ctx):
            result = DetectorResult()
            # Custom detection logic
            return result

    # Required exports
    DETECTORS = [MyDetector]
    RATING_RULES = {
        "custom.my_rule": RatingRule(
            score_func=lambda r: 5,
            reason_func=lambda r, s: "Custom reason",
            suggestion_func=lambda r, s: None,
        )
    }
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any, Callable, Optional, Type

from .detectors.base import BaseDetector
from .detectors.registry import DetectorRegistry
from .ratings import RATING_RULES, RatingRule


class PluginError(Exception):
    """Error loading or validating a plugin."""
    pass


class PluginLoader:
    """Loads and registers plugins from Python files."""

    def __init__(self, progress_callback: Optional[Callable[[str], None]] = None):
        """Initialize the plugin loader.

        Args:
            progress_callback: Optional callback for progress messages
        """
        self.progress_callback = progress_callback
        self.loaded_plugins: list[str] = []

    def _log(self, message: str) -> None:
        """Log a message via callback if available."""
        if self.progress_callback:
            self.progress_callback(message)

    def load_from_path(self, path: str) -> dict[str, Any]:
        """Load a plugin from a Python file path.

        Args:
            path: Path to the plugin Python file

        Returns:
            Dictionary with loaded detectors and rating rules

        Raises:
            PluginError: If plugin cannot be loaded or is invalid
        """
        plugin_path = Path(path).resolve()

        if not plugin_path.exists():
            raise PluginError(f"Plugin file not found: {path}")

        if not plugin_path.suffix == ".py":
            raise PluginError(f"Plugin must be a .py file: {path}")

        self._log(f"Loading plugin: {plugin_path.name}")

        # Load the module
        module_name = f"conventions_plugin_{plugin_path.stem}"

        try:
            spec = importlib.util.spec_from_file_location(module_name, plugin_path)
            if spec is None or spec.loader is None:
                raise PluginError(f"Could not load plugin spec: {path}")

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

        except Exception as e:
            raise PluginError(f"Error loading plugin {path}: {e}")

        # Extract detectors and rating rules
        result: dict[str, Any] = {
            "detectors": [],
            "rating_rules": {},
            "path": str(plugin_path),
        }

        # Get DETECTORS list
        if hasattr(module, "DETECTORS"):
            detectors = getattr(module, "DETECTORS")
            if not isinstance(detectors, (list, tuple)):
                raise PluginError(f"DETECTORS must be a list in {path}")

            for detector_class in detectors:
                if not isinstance(detector_class, type) or not issubclass(detector_class, BaseDetector):
                    raise PluginError(
                        f"Invalid detector in {path}: {detector_class}. "
                        "Must be a class inheriting from BaseDetector."
                    )
                result["detectors"].append(detector_class)
                self._log(f"  Found detector: {detector_class.name}")

        # Get RATING_RULES dict
        if hasattr(module, "RATING_RULES"):
            rating_rules = getattr(module, "RATING_RULES")
            if not isinstance(rating_rules, dict):
                raise PluginError(f"RATING_RULES must be a dict in {path}")

            for rule_id, rule in rating_rules.items():
                if not isinstance(rule_id, str):
                    raise PluginError(f"Rating rule ID must be string in {path}")
                if not isinstance(rule, RatingRule):
                    raise PluginError(
                        f"Invalid rating rule {rule_id} in {path}. "
                        "Must be a RatingRule instance."
                    )
                result["rating_rules"][rule_id] = rule
                self._log(f"  Found rating rule: {rule_id}")

        self.loaded_plugins.append(str(plugin_path))
        return result

    def register_detectors(self, detectors: list[Type[BaseDetector]]) -> None:
        """Register detector classes with the registry.

        Args:
            detectors: List of detector classes to register
        """
        for detector_class in detectors:
            DetectorRegistry.register(detector_class)
            self._log(f"Registered detector: {detector_class.name}")

    def merge_rating_rules(self, rules: dict[str, RatingRule]) -> None:
        """Merge rating rules into the global registry.

        Args:
            rules: Dictionary of rule_id -> RatingRule
        """
        for rule_id, rule in rules.items():
            if rule_id in RATING_RULES:
                self._log(f"Warning: Overriding existing rating rule: {rule_id}")
            RATING_RULES[rule_id] = rule
            self._log(f"Registered rating rule: {rule_id}")

    def load_and_register(self, path: str) -> None:
        """Load a plugin and register all its components.

        Args:
            path: Path to the plugin Python file
        """
        result = self.load_from_path(path)
        self.register_detectors(result["detectors"])
        self.merge_rating_rules(result["rating_rules"])


def load_plugins(
    plugin_paths: list[str],
    progress_callback: Optional[Callable[[str], None]] = None,
) -> list[str]:
    """Load multiple plugins from file paths.

    Args:
        plugin_paths: List of paths to plugin files
        progress_callback: Optional callback for progress messages

    Returns:
        List of successfully loaded plugin paths

    Note:
        Errors loading individual plugins are logged but don't stop
        other plugins from loading.
    """
    loader = PluginLoader(progress_callback)
    loaded = []

    for path in plugin_paths:
        try:
            loader.load_and_register(path)
            loaded.append(path)
        except PluginError as e:
            if progress_callback:
                progress_callback(f"Warning: {e}")
        except Exception as e:
            if progress_callback:
                progress_callback(f"Warning: Unexpected error loading plugin {path}: {e}")

    return loaded


def create_example_plugin(output_path: Path) -> None:
    """Create an example plugin file at the specified path.

    Args:
        output_path: Where to write the example plugin
    """
    example_content = '''"""Example custom conventions plugin.

This file demonstrates how to create custom detectors and rating rules.
"""

from conventions.detectors.base import BaseDetector, DetectorContext, DetectorResult
from conventions.ratings import RatingRule
from conventions.schemas import ConventionRule


class CustomCopyrightDetector(BaseDetector):
    """Detect copyright headers in source files."""

    name = "custom_copyright"
    description = "Detects copyright headers in source files"
    languages = {"python"}  # Or set() for language-agnostic

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        result = DetectorResult()

        # Get Python files from the index
        index = ctx.get_python_index()

        files_with_copyright = 0
        total_files = len(index.files)

        for rel_path, file_index in index.files.items():
            if file_index.lines:
                # Check first 5 lines for copyright
                header = "\\n".join(file_index.lines[:5])
                if "copyright" in header.lower() or "license" in header.lower():
                    files_with_copyright += 1

        if total_files > 0:
            ratio = files_with_copyright / total_files
            rule = self.make_rule(
                rule_id="custom.conventions.copyright_header",
                category="documentation",
                title="Copyright Headers",
                description="Source files with copyright/license headers",
                confidence=0.8,
                language="python",
                stats={
                    "files_with_header": files_with_copyright,
                    "total_files": total_files,
                    "coverage_ratio": ratio,
                },
            )
            result.rules.append(rule)

        return result


# Required export: list of detector classes
DETECTORS = [CustomCopyrightDetector]

# Optional: custom rating rules
RATING_RULES = {
    "custom.conventions.copyright_header": RatingRule(
        score_func=lambda r: (
            5 if r.stats.get("coverage_ratio", 0) >= 0.9 else
            4 if r.stats.get("coverage_ratio", 0) >= 0.7 else
            3 if r.stats.get("coverage_ratio", 0) >= 0.5 else
            2 if r.stats.get("coverage_ratio", 0) >= 0.2 else 1
        ),
        reason_func=lambda r, s: f"Copyright header coverage: {r.stats.get('coverage_ratio', 0) * 100:.0f}%",
        suggestion_func=lambda r, s: (
            None if s >= 5 else
            "Add copyright/license headers to all source files."
        ),
    ),
}
'''
    output_path.write_text(example_content)
