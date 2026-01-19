"""Scanning utilities for conventions detection."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .schemas import ConventionsOutput


def scan_repository(
    repo_path: Path,
    languages: Optional[set[str]] = None,
    max_files: int = 2000,
    verbose: bool = False,
) -> ConventionsOutput:
    """
    Scan a repository for coding conventions.

    Args:
        repo_path: Path to the repository
        languages: Languages to analyze (auto-detect if None)
        max_files: Maximum files to scan per language
        verbose: Whether to print progress

    Returns:
        ConventionsOutput with detected conventions
    """
    from .detectors.orchestrator import run_detectors

    def progress(msg: str) -> None:
        if verbose:
            print(f"  {msg}")

    return run_detectors(
        repo_root=repo_path,
        languages=languages,
        max_files=max_files,
        progress_callback=progress if verbose else None,
    )
