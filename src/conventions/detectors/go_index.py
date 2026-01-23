"""Go code indexer using regex-based analysis."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..fs import get_relative_path, read_file_safe, walk_files
from ..schemas import EvidenceSnippet


@dataclass
class GoFileIndex:
    """Index of a single Go file."""

    path: Path
    relative_path: str
    package: str = ""
    role: str = "other"  # api, service, test, other
    parse_error: Optional[str] = None

    # Extracted data
    imports: list[tuple[str, int]] = field(default_factory=list)  # (module, line)
    functions: list[tuple[str, int]] = field(default_factory=list)  # (name, line)
    interfaces: list[tuple[str, int]] = field(default_factory=list)  # (name, line)
    structs: list[tuple[str, int]] = field(default_factory=list)  # (name, line)

    # Raw content
    lines: list[str] = field(default_factory=list)


class GoIndex:
    """
    Index of Go files in a repository.

    Uses regex-based analysis (lighter than full AST).
    """

    def __init__(
        self,
        repo_root: Path,
        max_files: int = 1000,
    ):
        self.repo_root = Path(repo_root).resolve()
        self.max_files = max_files
        self.files: dict[str, GoFileIndex] = {}
        self._built = False

    def build(self) -> None:
        """Build the index by scanning all Go files."""
        if self._built:
            return

        for file_path in walk_files(
            self.repo_root,
            extensions={".go"},
            max_files=self.max_files,
        ):
            file_index = self._index_file(file_path)
            self.files[file_index.relative_path] = file_index

        self._built = True

    def _index_file(self, file_path: Path) -> GoFileIndex:
        """Index a single Go file."""
        relative_path = get_relative_path(file_path, self.repo_root)

        file_index = GoFileIndex(
            path=file_path,
            relative_path=relative_path,
        )

        content = read_file_safe(file_path)
        if content is None:
            file_index.parse_error = "Could not read file"
            return file_index

        file_index.lines = content.splitlines()

        # Extract package name
        package_match = re.search(r"^package\s+(\w+)", content, re.MULTILINE)
        if package_match:
            file_index.package = package_match.group(1)

        # Infer role from path and package
        file_index.role = infer_go_module_role(relative_path, file_index.package)

        # Extract imports
        file_index.imports = self._extract_imports(content)

        # Extract function declarations
        file_index.functions = self._extract_functions(content)

        # Extract interfaces
        file_index.interfaces = self._extract_interfaces(content)

        # Extract structs
        file_index.structs = self._extract_structs(content)

        return file_index

    def _extract_imports(self, content: str) -> list[tuple[str, int]]:
        """Extract import statements."""
        imports = []

        # Single import: import "package"
        for match in re.finditer(r'^import\s+"([^"]+)"', content, re.MULTILINE):
            pkg = match.group(1)
            line = content[:match.start()].count("\n") + 1
            imports.append((pkg, line))

        # Import block: import ( ... )
        import_block = re.search(r"import\s*\(([\s\S]*?)\)", content)
        if import_block:
            block_start = content[:import_block.start()].count("\n")
            block_content = import_block.group(1)

            for i, line_content in enumerate(block_content.split("\n")):
                pkg_match = re.search(r'"([^"]+)"', line_content)
                if pkg_match:
                    imports.append((pkg_match.group(1), block_start + i + 1))

        return imports

    def _extract_functions(self, content: str) -> list[tuple[str, int]]:
        """Extract function declarations."""
        functions = []

        # func Name(...) or func (receiver) Name(...)
        for match in re.finditer(r"^func\s+(?:\([^)]+\)\s+)?(\w+)\s*\(", content, re.MULTILINE):
            name = match.group(1)
            line = content[:match.start()].count("\n") + 1
            functions.append((name, line))

        return functions

    def _extract_interfaces(self, content: str) -> list[tuple[str, int]]:
        """Extract interface declarations."""
        interfaces = []

        for match in re.finditer(r"^type\s+(\w+)\s+interface\s*\{", content, re.MULTILINE):
            name = match.group(1)
            line = content[:match.start()].count("\n") + 1
            interfaces.append((name, line))

        return interfaces

    def _extract_structs(self, content: str) -> list[tuple[str, int]]:
        """Extract struct declarations."""
        structs = []

        for match in re.finditer(r"^type\s+(\w+)\s+struct\s*\{", content, re.MULTILINE):
            name = match.group(1)
            line = content[:match.start()].count("\n") + 1
            structs.append((name, line))

        return structs

    def count_imports_matching(self, pattern: str) -> int:
        """Count files that import a package matching pattern."""
        count = 0
        for file_idx in self.files.values():
            for pkg, _ in file_idx.imports:
                if pattern in pkg:
                    count += 1
                    break
        return count

    def find_imports_matching(
        self,
        pattern: str,
        limit: int = 50,
    ) -> list[tuple[str, str, int]]:
        """Find imports matching pattern. Returns (file_path, package, line)."""
        results = []
        for rel_path, file_idx in self.files.items():
            for pkg, line in file_idx.imports:
                if pattern in pkg:
                    results.append((rel_path, pkg, line))
                    if len(results) >= limit:
                        return results
        return results


def infer_go_module_role(relative_path: str, package: str) -> str:
    """Infer the role of a Go module."""
    path_lower = relative_path.lower()
    parts = Path(relative_path).parts

    # Test files
    if path_lower.endswith("_test.go"):
        return "test"

    # API/handlers
    if any(p in ("api", "handlers", "routes", "controllers", "http") for p in parts):
        return "api"
    if package in ("api", "handlers", "http"):
        return "api"

    # Services
    if any(p in ("services", "service", "domain", "usecase") for p in parts):
        return "service"

    # Repository/DB
    if any(p in ("repository", "repositories", "db", "database", "store", "storage") for p in parts):
        return "db"

    # Models
    if any(p in ("models", "entities", "domain") for p in parts):
        return "model"

    return "other"


def make_evidence(
    index: GoIndex,
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
