"""Incremental scanning cache for conventions detection.

This module provides caching of scan results to enable incremental scanning,
where only changed files are re-scanned on subsequent runs.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .schemas import ConventionRule, ConventionsOutput

CACHE_VERSION = "1.0.0"
CACHE_FILE_NAME = ".cache.json"


@dataclass
class FileHash:
    """Hash information for a file."""
    path: str
    content_hash: str
    mtime: float
    size: int


@dataclass
class ScanCache:
    """Cache of previous scan results."""

    version: str = CACHE_VERSION
    timestamp: str = ""
    config_hash: str = ""  # Hash of config to detect config changes
    file_hashes: dict[str, FileHash] = field(default_factory=dict)
    rules_by_file: dict[str, list[dict[str, Any]]] = field(default_factory=dict)  # file -> rules that depend on it
    global_rules: list[dict[str, Any]] = field(default_factory=list)  # Rules not tied to specific files

    def to_dict(self) -> dict[str, Any]:
        """Convert cache to dictionary for serialization."""
        return {
            "version": self.version,
            "timestamp": self.timestamp,
            "config_hash": self.config_hash,
            "file_hashes": {
                path: {
                    "path": fh.path,
                    "content_hash": fh.content_hash,
                    "mtime": fh.mtime,
                    "size": fh.size,
                }
                for path, fh in self.file_hashes.items()
            },
            "rules_by_file": self.rules_by_file,
            "global_rules": self.global_rules,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScanCache":
        """Create cache from dictionary."""
        file_hashes = {}
        for path, fh_data in data.get("file_hashes", {}).items():
            file_hashes[path] = FileHash(
                path=fh_data["path"],
                content_hash=fh_data["content_hash"],
                mtime=fh_data["mtime"],
                size=fh_data["size"],
            )

        return cls(
            version=data.get("version", CACHE_VERSION),
            timestamp=data.get("timestamp", ""),
            config_hash=data.get("config_hash", ""),
            file_hashes=file_hashes,
            rules_by_file=data.get("rules_by_file", {}),
            global_rules=data.get("global_rules", []),
        )


class CacheManager:
    """Manages scan result caching for incremental scanning."""

    def __init__(self, repo_root: Path):
        """Initialize the cache manager.

        Args:
            repo_root: Root directory of the repository
        """
        self.repo_root = Path(repo_root).resolve()
        self.cache_dir = self.repo_root / ".conventions"
        self.cache_path = self.cache_dir / CACHE_FILE_NAME
        self._cache: Optional[ScanCache] = None

    def load_cache(self) -> Optional[ScanCache]:
        """Load cache from disk.

        Returns:
            ScanCache if exists and valid, None otherwise
        """
        if self._cache is not None:
            return self._cache

        if not self.cache_path.exists():
            return None

        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            cache = ScanCache.from_dict(data)

            # Validate cache version
            if cache.version != CACHE_VERSION:
                return None

            self._cache = cache
            return cache

        except (json.JSONDecodeError, KeyError, TypeError):
            return None

    def save_cache(self, cache: ScanCache) -> None:
        """Save cache to disk.

        Args:
            cache: ScanCache to save
        """
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(cache.to_dict(), f, indent=2)

        self._cache = cache

    def clear_cache(self) -> None:
        """Remove cache file."""
        if self.cache_path.exists():
            self.cache_path.unlink()
        self._cache = None

    def compute_file_hash(self, file_path: Path) -> Optional[FileHash]:
        """Compute hash for a file.

        Args:
            file_path: Path to the file

        Returns:
            FileHash or None if file cannot be read
        """
        try:
            stat = file_path.stat()
            with open(file_path, "rb") as f:
                content_hash = hashlib.sha256(f.read()).hexdigest()

            rel_path = str(file_path.relative_to(self.repo_root))
            return FileHash(
                path=rel_path,
                content_hash=content_hash,
                mtime=stat.st_mtime,
                size=stat.st_size,
            )
        except (OSError, IOError):
            return None

    def compute_config_hash(self, config_dict: dict[str, Any]) -> str:
        """Compute hash for configuration.

        Args:
            config_dict: Configuration dictionary

        Returns:
            Hash string
        """
        config_str = json.dumps(config_dict, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()

    def get_changed_files(
        self,
        all_files: list[Path],
        config_hash: str,
    ) -> tuple[list[Path], list[str]]:
        """Find files that have changed since last scan.

        Args:
            all_files: List of all files to potentially scan
            config_hash: Hash of current configuration

        Returns:
            Tuple of (changed_files, unchanged_file_paths)
        """
        cache = self.load_cache()

        # If no cache or config changed, all files are "changed"
        if cache is None or cache.config_hash != config_hash:
            return all_files, []

        changed: list[Path] = []
        unchanged: list[str] = []

        for file_path in all_files:
            try:
                rel_path = str(file_path.relative_to(self.repo_root))
            except ValueError:
                changed.append(file_path)
                continue

            cached_hash = cache.file_hashes.get(rel_path)

            if cached_hash is None:
                # New file
                changed.append(file_path)
            else:
                current_hash = self.compute_file_hash(file_path)
                if current_hash is None:
                    changed.append(file_path)
                elif current_hash.content_hash != cached_hash.content_hash:
                    changed.append(file_path)
                else:
                    unchanged.append(rel_path)

        return changed, unchanged

    def get_cached_rules_for_files(
        self,
        unchanged_files: list[str],
    ) -> list[ConventionRule]:
        """Get cached rules for unchanged files.

        Args:
            unchanged_files: List of unchanged file relative paths

        Returns:
            List of cached ConventionRule objects
        """
        cache = self.load_cache()
        if cache is None:
            return []

        rules = []
        seen_rules: set[str] = set()

        for file_path in unchanged_files:
            cached_rules = cache.rules_by_file.get(file_path, [])
            for rule_data in cached_rules:
                rule_id = rule_data.get("id", "")
                if rule_id not in seen_rules:
                    rules.append(ConventionRule.model_validate(rule_data))
                    seen_rules.add(rule_id)

        return rules

    def update_cache(
        self,
        output: ConventionsOutput,
        all_files: list[Path],
        config_hash: str,
    ) -> None:
        """Update cache with new scan results.

        Args:
            output: Scan output
            all_files: All files that were considered
            config_hash: Hash of configuration used
        """
        # Build file hashes
        file_hashes: dict[str, FileHash] = {}
        for file_path in all_files:
            file_hash = self.compute_file_hash(file_path)
            if file_hash:
                file_hashes[file_hash.path] = file_hash

        # Organize rules by file
        rules_by_file: dict[str, list[dict[str, Any]]] = {}
        global_rules: list[dict[str, Any]] = []

        for rule in output.rules:
            rule_dict = rule.model_dump()

            if rule.evidence:
                # Associate rule with files in evidence
                seen_files: set[str] = set()
                for ev in rule.evidence:
                    if ev.file_path not in seen_files:
                        if ev.file_path not in rules_by_file:
                            rules_by_file[ev.file_path] = []
                        rules_by_file[ev.file_path].append(rule_dict)
                        seen_files.add(ev.file_path)
            else:
                # Rule with no file evidence is global
                global_rules.append(rule_dict)

        cache = ScanCache(
            version=CACHE_VERSION,
            timestamp=datetime.now().isoformat(),
            config_hash=config_hash,
            file_hashes=file_hashes,
            rules_by_file=rules_by_file,
            global_rules=global_rules,
        )

        self.save_cache(cache)

    def merge_results(
        self,
        new_rules: list[ConventionRule],
        cached_rules: list[ConventionRule],
    ) -> list[ConventionRule]:
        """Merge new rules with cached rules.

        New rules take precedence over cached rules with the same ID.

        Args:
            new_rules: Rules from the current scan
            cached_rules: Rules from cache

        Returns:
            Merged list of rules
        """
        # Build set of new rule IDs
        new_rule_ids = {rule.id for rule in new_rules}

        # Start with new rules
        merged = list(new_rules)

        # Add cached rules that don't conflict
        for rule in cached_rules:
            if rule.id not in new_rule_ids:
                merged.append(rule)

        return merged
