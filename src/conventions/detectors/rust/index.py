"""Rust code indexer using regex-based analysis."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ...fs import get_relative_path, read_file_safe, walk_files
from ...schemas import EvidenceSnippet


@dataclass
class RustFileIndex:
    """Index of a single Rust file."""

    path: Path
    relative_path: str
    role: str  # lib, bin, test, example, bench
    parse_error: Optional[str] = None

    # Extracted data
    uses: list[tuple[str, int]] = field(default_factory=list)  # (crate/module, line)
    mods: list[tuple[str, int]] = field(default_factory=list)  # (module_name, line)
    functions: list[tuple[str, int, bool]] = field(default_factory=list)  # (name, line, is_pub)
    structs: list[tuple[str, int, bool]] = field(default_factory=list)  # (name, line, is_pub)
    enums: list[tuple[str, int, bool]] = field(default_factory=list)  # (name, line, is_pub)
    traits: list[tuple[str, int, bool]] = field(default_factory=list)  # (name, line, is_pub)
    impls: list[tuple[str, int]] = field(default_factory=list)  # (type_name, line)
    macros: list[tuple[str, int]] = field(default_factory=list)  # (macro_name, line)
    unsafe_count: int = 0
    async_count: int = 0

    # Raw content for analysis
    lines: list[str] = field(default_factory=list)


class RustIndex:
    """
    Index of Rust files in a repository.

    Uses regex-based analysis (lighter than full AST).
    """

    def __init__(
        self,
        repo_root: Path,
        max_files: int = 1000,
    ):
        self.repo_root = Path(repo_root).resolve()
        self.max_files = max_files
        self.files: dict[str, RustFileIndex] = {}
        self._built = False

    def build(self) -> None:
        """Build the index by scanning all Rust files."""
        if self._built:
            return

        for file_path in walk_files(
            self.repo_root,
            extensions={".rs"},
            max_files=self.max_files,
        ):
            file_index = self._index_file(file_path)
            self.files[file_index.relative_path] = file_index

        self._built = True

    def _index_file(self, file_path: Path) -> RustFileIndex:
        """Index a single Rust file."""
        relative_path = get_relative_path(file_path, self.repo_root)
        role = infer_rust_file_role(relative_path)

        file_index = RustFileIndex(
            path=file_path,
            relative_path=relative_path,
            role=role,
        )

        content = read_file_safe(file_path)
        if content is None:
            file_index.parse_error = "Could not read file"
            return file_index

        file_index.lines = content.splitlines()

        # Extract use statements
        file_index.uses = self._extract_uses(content)

        # Extract mod declarations
        file_index.mods = self._extract_mods(content)

        # Extract functions
        file_index.functions = self._extract_functions(content)

        # Extract structs
        file_index.structs = self._extract_structs(content)

        # Extract enums
        file_index.enums = self._extract_enums(content)

        # Extract traits
        file_index.traits = self._extract_traits(content)

        # Extract impl blocks
        file_index.impls = self._extract_impls(content)

        # Extract macro definitions
        file_index.macros = self._extract_macros(content)

        # Count unsafe blocks
        file_index.unsafe_count = len(re.findall(r"\bunsafe\b", content))

        # Count async functions/blocks
        file_index.async_count = len(re.findall(r"\basync\b", content))

        return file_index

    def _extract_uses(self, content: str) -> list[tuple[str, int]]:
        """Extract use statements."""
        uses = []
        for match in re.finditer(r"use\s+([\w:]+)", content):
            path = match.group(1)
            line = content[:match.start()].count("\n") + 1
            uses.append((path, line))
        return uses

    def _extract_mods(self, content: str) -> list[tuple[str, int]]:
        """Extract mod declarations."""
        mods = []
        for match in re.finditer(r"(?:pub\s+)?mod\s+(\w+)", content):
            name = match.group(1)
            line = content[:match.start()].count("\n") + 1
            mods.append((name, line))
        return mods

    def _extract_functions(self, content: str) -> list[tuple[str, int, bool]]:
        """Extract function definitions."""
        functions = []
        pattern = r"(pub(?:\s*\([^)]*\))?\s+)?(?:async\s+)?(?:unsafe\s+)?fn\s+(\w+)"
        for match in re.finditer(pattern, content):
            is_pub = match.group(1) is not None
            name = match.group(2)
            line = content[:match.start()].count("\n") + 1
            functions.append((name, line, is_pub))
        return functions

    def _extract_structs(self, content: str) -> list[tuple[str, int, bool]]:
        """Extract struct definitions."""
        structs = []
        pattern = r"(pub(?:\s*\([^)]*\))?\s+)?struct\s+(\w+)"
        for match in re.finditer(pattern, content):
            is_pub = match.group(1) is not None
            name = match.group(2)
            line = content[:match.start()].count("\n") + 1
            structs.append((name, line, is_pub))
        return structs

    def _extract_enums(self, content: str) -> list[tuple[str, int, bool]]:
        """Extract enum definitions."""
        enums = []
        pattern = r"(pub(?:\s*\([^)]*\))?\s+)?enum\s+(\w+)"
        for match in re.finditer(pattern, content):
            is_pub = match.group(1) is not None
            name = match.group(2)
            line = content[:match.start()].count("\n") + 1
            enums.append((name, line, is_pub))
        return enums

    def _extract_traits(self, content: str) -> list[tuple[str, int, bool]]:
        """Extract trait definitions."""
        traits = []
        pattern = r"(pub(?:\s*\([^)]*\))?\s+)?trait\s+(\w+)"
        for match in re.finditer(pattern, content):
            is_pub = match.group(1) is not None
            name = match.group(2)
            line = content[:match.start()].count("\n") + 1
            traits.append((name, line, is_pub))
        return traits

    def _extract_impls(self, content: str) -> list[tuple[str, int]]:
        """Extract impl blocks."""
        impls = []
        pattern = r"impl(?:<[^>]*>)?\s+(?:(\w+)\s+for\s+)?(\w+)"
        for match in re.finditer(pattern, content):
            type_name = match.group(2)
            line = content[:match.start()].count("\n") + 1
            impls.append((type_name, line))
        return impls

    def _extract_macros(self, content: str) -> list[tuple[str, int]]:
        """Extract macro definitions."""
        macros = []
        pattern = r"macro_rules!\s+(\w+)"
        for match in re.finditer(pattern, content):
            name = match.group(1)
            line = content[:match.start()].count("\n") + 1
            macros.append((name, line))
        return macros

    def find_uses_matching(
        self,
        pattern: str,
        limit: int = 50,
    ) -> list[tuple[str, str, int]]:
        """Find use statements matching pattern. Returns (file_path, use_path, line)."""
        results = []
        for rel_path, file_idx in self.files.items():
            for use_path, line in file_idx.uses:
                if pattern in use_path:
                    results.append((rel_path, use_path, line))
                    if len(results) >= limit:
                        return results
        return results

    def count_uses_matching(self, pattern: str) -> int:
        """Count files that use a crate/module matching pattern."""
        count = 0
        for file_idx in self.files.values():
            for use_path, _ in file_idx.uses:
                if pattern in use_path:
                    count += 1
                    break
        return count

    def search_pattern(
        self,
        pattern: str,
        limit: int = 100,
        exclude_tests: bool = False,
    ) -> list[tuple[str, int, str]]:
        """Search for regex pattern in all files. Returns (file_path, line, match)."""
        results = []
        compiled = re.compile(pattern, re.MULTILINE)

        for rel_path, file_idx in self.files.items():
            if exclude_tests and file_idx.role == "test":
                continue

            content = "\n".join(file_idx.lines)
            for match in compiled.finditer(content):
                line = content[:match.start()].count("\n") + 1
                results.append((rel_path, line, match.group(0)))
                if len(results) >= limit:
                    return results

        return results

    def count_pattern(
        self,
        pattern: str,
        exclude_tests: bool = False,
    ) -> int:
        """Count occurrences of regex pattern across all files."""
        count = 0
        compiled = re.compile(pattern, re.MULTILINE)

        for file_idx in self.files.values():
            if exclude_tests and file_idx.role == "test":
                continue

            content = "\n".join(file_idx.lines)
            count += len(compiled.findall(content))

        return count

    def get_test_files(self) -> list[RustFileIndex]:
        """Get all test files."""
        return [f for f in self.files.values() if f.role == "test"]

    def get_non_test_files(self) -> list[RustFileIndex]:
        """Get all non-test files."""
        return [f for f in self.files.values() if f.role != "test"]


def infer_rust_file_role(relative_path: str) -> str:
    """Infer the role of a Rust file from its path."""
    path_lower = relative_path.lower()
    parts = Path(relative_path).parts

    # Test files
    if "tests" in parts or path_lower.endswith("_test.rs"):
        return "test"
    if "#[cfg(test)]" in relative_path:  # This won't work, but for pattern matching
        return "test"

    # Examples
    if "examples" in parts:
        return "example"

    # Benchmarks
    if "benches" in parts:
        return "bench"

    # Binary
    if "src/bin" in relative_path or relative_path.endswith("main.rs"):
        return "bin"

    # Library
    if relative_path.endswith("lib.rs"):
        return "lib"

    return "lib"


def make_evidence(
    index: RustIndex,
    relative_path: str,
    line: int,
    radius: int = 5,
) -> Optional[EvidenceSnippet]:
    """Create an evidence snippet from the index."""
    file_idx = index.files.get(relative_path)
    if file_idx is None:
        return None

    lines = file_idx.lines
    if not lines or line < 1 or line > len(lines):
        return None

    line_start = max(1, line - radius)
    line_end = min(len(lines), line + radius)

    excerpt_lines = lines[line_start - 1 : line_end]
    excerpt = "\n".join(excerpt_lines)

    return EvidenceSnippet(
        file_path=relative_path,
        line_start=line_start,
        line_end=line_end,
        excerpt=excerpt,
    )
