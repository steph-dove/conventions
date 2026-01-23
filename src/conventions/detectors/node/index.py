"""Node.js code indexer using regex-based analysis."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ...fs import get_relative_path, read_file_safe, walk_files
from ...schemas import EvidenceSnippet


@dataclass
class NodeFileIndex:
    """Index of a single Node.js file."""

    path: Path
    relative_path: str
    role: str  # api, service, test, other
    parse_error: Optional[str] = None

    # Extracted data
    imports: list[tuple[str, int]] = field(default_factory=list)  # (module, line)
    exports: list[tuple[str, int]] = field(default_factory=list)  # (name, line)
    function_count: int = 0
    async_function_count: int = 0
    class_count: int = 0
    has_typescript: bool = False

    # Raw content for analysis
    lines: list[str] = field(default_factory=list)


class NodeIndex:
    """
    Index of Node.js files in a repository.

    Uses regex-based analysis (lighter than full AST).
    """

    def __init__(
        self,
        repo_root: Path,
        max_files: int = 1000,
    ):
        self.repo_root = Path(repo_root).resolve()
        self.max_files = max_files
        self.files: dict[str, NodeFileIndex] = {}
        self._built = False

    def build(self) -> None:
        """Build the index by scanning all Node.js files."""
        if self._built:
            return

        extensions = {".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"}

        for file_path in walk_files(
            self.repo_root,
            extensions=extensions,
            max_files=self.max_files,
        ):
            file_index = self._index_file(file_path)
            self.files[file_index.relative_path] = file_index

        self._built = True

    def _index_file(self, file_path: Path) -> NodeFileIndex:
        """Index a single Node.js file."""
        relative_path = get_relative_path(file_path, self.repo_root)
        role = infer_node_module_role(relative_path)

        file_index = NodeFileIndex(
            path=file_path,
            relative_path=relative_path,
            role=role,
            has_typescript=file_path.suffix in {".ts", ".tsx"},
        )

        content = read_file_safe(file_path)
        if content is None:
            file_index.parse_error = "Could not read file"
            return file_index

        file_index.lines = content.splitlines()

        # Extract imports
        file_index.imports = self._extract_imports(content)

        # Extract exports
        file_index.exports = self._extract_exports(content)

        # Count functions
        file_index.function_count = len(re.findall(
            r"(?:function\s+\w+|const\s+\w+\s*=\s*(?:async\s+)?\(|=>\s*\{)",
            content,
        ))
        file_index.async_function_count = len(re.findall(
            r"async\s+(?:function|\(|\w+\s*=>)",
            content,
        ))

        # Count classes
        file_index.class_count = len(re.findall(r"class\s+\w+", content))

        return file_index

    def _extract_imports(self, content: str) -> list[tuple[str, int]]:
        """Extract import statements."""
        imports = []

        # ES6 imports: import X from 'module'
        for match in re.finditer(r"import\s+.*?from\s+['\"]([^'\"]+)['\"]", content):
            module = match.group(1)
            line = content[:match.start()].count("\n") + 1
            imports.append((module, line))

        # CommonJS requires: require('module')
        for match in re.finditer(r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)", content):
            module = match.group(1)
            line = content[:match.start()].count("\n") + 1
            imports.append((module, line))

        return imports

    def _extract_exports(self, content: str) -> list[tuple[str, int]]:
        """Extract export statements."""
        exports = []

        # ES6 exports
        for match in re.finditer(r"export\s+(?:default\s+)?(?:const|let|var|function|class|async\s+function)\s+(\w+)", content):
            name = match.group(1)
            line = content[:match.start()].count("\n") + 1
            exports.append((name, line))

        # module.exports
        for match in re.finditer(r"module\.exports\s*=", content):
            line = content[:match.start()].count("\n") + 1
            exports.append(("module.exports", line))

        return exports

    def count_imports_matching(self, pattern: str) -> int:
        """Count files that import a module matching pattern."""
        count = 0
        for file_idx in self.files.values():
            for module, _ in file_idx.imports:
                if pattern in module:
                    count += 1
                    break
        return count

    def find_imports_matching(
        self,
        pattern: str,
        limit: int = 50,
    ) -> list[tuple[str, str, int]]:
        """Find imports matching pattern. Returns (file_path, module, line)."""
        results = []
        for rel_path, file_idx in self.files.items():
            for module, line in file_idx.imports:
                if pattern in module:
                    results.append((rel_path, module, line))
                    if len(results) >= limit:
                        return results
        return results

    def get_files_by_role(self, role: str) -> list[NodeFileIndex]:
        """Get all files with a specific role."""
        return [f for f in self.files.values() if f.role == role]

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

    def get_test_files(self) -> list[NodeFileIndex]:
        """Get all test files."""
        return [f for f in self.files.values() if f.role == "test"]

    def get_non_test_files(self) -> list[NodeFileIndex]:
        """Get all non-test files."""
        return [f for f in self.files.values() if f.role != "test"]

    def get_typescript_files(self) -> list[NodeFileIndex]:
        """Get all TypeScript files."""
        return [f for f in self.files.values() if f.has_typescript]

    def get_javascript_files(self) -> list[NodeFileIndex]:
        """Get all JavaScript files."""
        return [f for f in self.files.values() if not f.has_typescript]


def infer_node_module_role(relative_path: str) -> str:
    """Infer the role of a Node.js module from its path."""
    path_lower = relative_path.lower()
    parts = Path(relative_path).parts

    # Test files
    if any(p in ("test", "tests", "__tests__", "spec") for p in parts):
        return "test"
    if path_lower.endswith(".test.js") or path_lower.endswith(".spec.js"):
        return "test"
    if path_lower.endswith(".test.ts") or path_lower.endswith(".spec.ts"):
        return "test"

    # API/routes
    if any(p in ("routes", "api", "controllers", "handlers", "endpoints") for p in parts):
        return "api"

    # Services
    if any(p in ("services", "service") for p in parts):
        return "service"

    # Models/DB
    if any(p in ("models", "db", "database", "repositories") for p in parts):
        return "db"

    return "other"


def make_evidence(
    index: NodeIndex,
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
