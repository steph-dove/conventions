"""Orchestrator for running convention detectors."""

from __future__ import annotations

import sys
import traceback
from pathlib import Path
from typing import Callable, Optional

from ..schemas import ConventionRule, ConventionsOutput, DetectorWarning, RepoMetadata
from .base import DetectorContext
from .registry import DetectorRegistry, register_all_detectors


def detect_languages(repo_root: Path) -> set[str]:
    """
    Auto-detect programming languages in the repository.

    Returns set of detected language strings.
    """
    from ..fs import walk_files

    languages: set[str] = set()

    # Check for Python files
    py_files = list(walk_files(repo_root, {".py"}, max_files=5))
    if py_files:
        languages.add("python")

    # Check for Go files
    go_files = list(walk_files(repo_root, {".go"}, max_files=5))
    if go_files:
        languages.add("go")

    # Check for Node.js files (JavaScript/TypeScript)
    node_files = list(walk_files(repo_root, {".js", ".ts", ".jsx", ".tsx"}, max_files=5))
    if node_files:
        languages.add("node")

    return languages


def run_detectors(
    repo_root: Path,
    languages: Optional[set[str]] = None,
    max_files: int = 2000,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> ConventionsOutput:
    """
    Run all registered detectors on a repository.

    Args:
        repo_root: Path to the repository root
        languages: Set of languages to scan (auto-detect if None)
        max_files: Maximum files to scan per language
        progress_callback: Optional callback for progress updates

    Returns:
        ConventionsOutput with all detected rules and warnings
    """
    repo_root = Path(repo_root).resolve()

    # Register all detectors
    register_all_detectors()

    # Auto-detect languages if not specified
    if languages is None:
        languages = detect_languages(repo_root)
        if progress_callback:
            progress_callback(f"Detected languages: {', '.join(sorted(languages)) or 'none'}")

    # Create context
    ctx = DetectorContext(
        repo_root=repo_root,
        selected_languages=languages,
        max_files=max_files,
    )

    # Collect results
    all_rules: list[ConventionRule] = []
    all_warnings: list[DetectorWarning] = []
    total_files_scanned = 0

    # Run each detector
    for detector_class in DetectorRegistry.get_all():
        detector = detector_class()

        if not detector.should_run(ctx):
            continue

        if progress_callback:
            progress_callback(f"Running detector: {detector.name}")

        try:
            result = detector.detect(ctx)
            all_rules.extend(result.rules)

            # Convert string warnings to DetectorWarning objects
            for warning_msg in result.warnings:
                all_warnings.append(DetectorWarning(
                    detector=detector.name,
                    message=warning_msg,
                ))

        except Exception as e:
            # Capture exception as warning and continue
            tb = traceback.format_exc()
            all_warnings.append(DetectorWarning(
                detector=detector.name,
                message=f"Detector failed with exception: {e}\n{tb}",
            ))
            if progress_callback:
                progress_callback(f"Warning: {detector.name} failed - {e}")

    # Get file count from Python index if available
    if ctx._python_index is not None:
        total_files_scanned = len(ctx._python_index.files)

    # Build output
    return ConventionsOutput(
        metadata=RepoMetadata(
            path=str(repo_root),
            detected_languages=sorted(languages),
            total_files_scanned=total_files_scanned,
        ),
        rules=all_rules,
        warnings=all_warnings,
    )


def write_conventions_output(
    output: ConventionsOutput,
    repo_root: Path,
) -> Path:
    """
    Write conventions output to .conventions/conventions.raw.json.

    Returns the path to the written file.
    """
    from ..fs import ensure_conventions_dir

    conventions_dir = ensure_conventions_dir(repo_root)
    output_path = conventions_dir / "conventions.raw.json"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output.model_dump_json(indent=2))

    return output_path
