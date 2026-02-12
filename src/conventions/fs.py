"""File system utilities for conventions detection."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator, Optional

try:
    import pathspec
except ImportError:
    pathspec = None  # type: ignore


# Hard excludes - always skip these directories/patterns
HARD_EXCLUDES = {
    # VCS
    ".git",
    ".svn",
    ".hg",
    # Caches
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    # Dependencies
    "node_modules",
    "vendor",
    ".venv",
    "venv",
    "env",
    ".env",
    ".tox",
    ".nox",
    # Build artifacts
    "build",
    "dist",
    "eggs",
    "*.egg-info",
    ".eggs",
    "site-packages",
    # Conventions output
    ".conventions",
    # Documentation & examples — tutorial/example code is not representative
    # of project conventions and pollutes language detection and pattern analysis
    "docs",
    "docs_src",
    "doc",
    "examples",
    "example",
    "samples",
    "sample",
    "tutorials",
    "tutorial",
    "demo",
    "demos",
}

# File size limit (skip very large files)
MAX_FILE_SIZE_BYTES = 1024 * 1024  # 1MB

# Default file caps per language
DEFAULT_MAX_FILES = 2000


def load_gitignore(repo_root: Path) -> Optional["pathspec.PathSpec"]:
    """Load .gitignore patterns from repository root."""
    if pathspec is None:
        return None

    gitignore_path = repo_root / ".gitignore"
    if not gitignore_path.exists():
        return None

    try:
        with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as f:
            patterns = f.read().splitlines()
        return pathspec.PathSpec.from_lines("gitwildmatch", patterns)
    except Exception:
        return None


def should_exclude(
    path: Path,
    repo_root: Path,
    gitignore_spec: Optional["pathspec.PathSpec"] = None,
    custom_excludes: Optional["pathspec.PathSpec"] = None,
) -> bool:
    """Check if a path should be excluded from scanning."""
    # Check hard excludes against any path component
    for part in path.parts:
        if part in HARD_EXCLUDES:
            return True
        # Handle wildcard patterns
        for pattern in HARD_EXCLUDES:
            if pattern.startswith("*") and part.endswith(pattern[1:]):
                return True

    try:
        rel_path = path.relative_to(repo_root)
        rel_path_str = str(rel_path)
    except ValueError:
        rel_path_str = None

    # Check gitignore patterns
    if gitignore_spec is not None and rel_path_str is not None:
        if gitignore_spec.match_file(rel_path_str):
            return True

    # Check custom exclude patterns
    if custom_excludes is not None and rel_path_str is not None:
        if custom_excludes.match_file(rel_path_str):
            return True

    return False


def create_exclude_spec(patterns: list[str]) -> Optional["pathspec.PathSpec"]:
    """Create a PathSpec from a list of glob patterns."""
    if not patterns or pathspec is None:
        return None
    try:
        return pathspec.PathSpec.from_lines("gitwildmatch", patterns)
    except Exception:
        return None


def walk_files(
    repo_root: Path,
    extensions: set[str],
    max_files: int = DEFAULT_MAX_FILES,
    respect_gitignore: bool = True,
    exclude_patterns: Optional[list[str]] = None,
) -> Iterator[Path]:
    """
    Walk repository and yield files matching given extensions.

    Args:
        repo_root: Root directory to scan
        extensions: Set of file extensions to include (e.g., {".py", ".pyi"})
        max_files: Maximum number of files to yield
        respect_gitignore: Whether to respect .gitignore patterns
        exclude_patterns: Additional glob patterns to exclude

    Yields:
        Path objects for matching files
    """
    repo_root = Path(repo_root).resolve()
    gitignore_spec = load_gitignore(repo_root) if respect_gitignore else None
    custom_excludes = create_exclude_spec(exclude_patterns or [])

    file_count = 0

    for root, dirs, files in os.walk(repo_root):
        root_path = Path(root)

        # Filter directories in-place to skip excluded ones
        dirs[:] = [
            d for d in dirs
            if not should_exclude(root_path / d, repo_root, gitignore_spec, custom_excludes)
        ]

        for filename in files:
            if file_count >= max_files:
                return

            file_path = root_path / filename

            # Check extension
            if not any(filename.endswith(ext) for ext in extensions):
                continue

            # Check exclusions
            if should_exclude(file_path, repo_root, gitignore_spec, custom_excludes):
                continue

            # Check file size
            try:
                if file_path.stat().st_size > MAX_FILE_SIZE_BYTES:
                    continue
            except OSError:
                continue

            file_count += 1
            yield file_path


def read_file_safe(path: Path, max_bytes: int = MAX_FILE_SIZE_BYTES) -> Optional[str]:
    """
    Read file contents safely with size limit.

    Returns None if file cannot be read or exceeds size limit.
    """
    try:
        if path.stat().st_size > max_bytes:
            return None
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except (OSError, IOError):
        return None


def get_relative_path(file_path: Path, repo_root: Path) -> str:
    """Get relative path string from repo root."""
    try:
        return str(file_path.relative_to(repo_root))
    except ValueError:
        return str(file_path)


def ensure_conventions_dir(repo_root: Path) -> Path:
    """Ensure .conventions directory exists and return its path."""
    conventions_dir = repo_root / ".conventions"
    conventions_dir.mkdir(parents=True, exist_ok=True)
    return conventions_dir
