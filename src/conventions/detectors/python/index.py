"""Python code indexer using AST analysis."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from ...fs import get_relative_path, read_file_safe, walk_files
from ...schemas import EvidenceSnippet


@dataclass
class FunctionInfo:
    """Information about a function definition."""

    name: str
    line: int
    is_async: bool = False
    has_return_annotation: bool = False
    annotated_args: int = 0
    total_args: int = 0
    has_docstring: bool = False
    docstring: Optional[str] = None
    decorators: list[str] = field(default_factory=list)

    @property
    def has_any_annotation(self) -> bool:
        """Check if function has any type annotations."""
        return self.has_return_annotation or self.annotated_args > 0


@dataclass
class ClassInfo:
    """Information about a class definition."""

    name: str
    line: int
    bases: list[str] = field(default_factory=list)
    has_docstring: bool = False
    docstring: Optional[str] = None
    decorators: list[str] = field(default_factory=list)


@dataclass
class CallInfo:
    """Information about a function/method call."""

    name: str  # Full dotted name (e.g., "session.query", "HTTPException")
    line: int
    kwargs: list[str] = field(default_factory=list)  # Keyword argument names


@dataclass
class ImportInfo:
    """Information about an import."""

    module: str  # e.g., "fastapi" or "sqlalchemy.orm"
    names: list[str] = field(default_factory=list)  # e.g., ["FastAPI", "Depends"]
    line: int = 0


@dataclass
class DecoratorInfo:
    """Information about a decorator usage."""

    name: str  # Full dotted name
    line: int
    call_args: list[str] = field(default_factory=list)  # Argument names if it's a call


@dataclass
class FileIndex:
    """Index of a single Python file."""

    path: Path
    relative_path: str
    role: str  # api, service, db, test, other
    parse_error: Optional[str] = None

    # Collected data
    imports: list[ImportInfo] = field(default_factory=list)
    functions: list[FunctionInfo] = field(default_factory=list)
    classes: list[ClassInfo] = field(default_factory=list)
    calls: list[CallInfo] = field(default_factory=list)
    decorators: list[DecoratorInfo] = field(default_factory=list)

    # Content for evidence extraction
    lines: list[str] = field(default_factory=list)

    @property
    def async_function_count(self) -> int:
        """Return the count of async functions in this file."""
        return sum(1 for f in self.functions if f.is_async)

    @property
    def sync_function_count(self) -> int:
        """Return the count of synchronous functions in this file."""
        return sum(1 for f in self.functions if not f.is_async)


class PythonIndex:
    """
    Index of Python files in a repository.

    Provides efficient access to code structure information
    for convention detection.
    """

    def __init__(
        self,
        repo_root: Path,
        max_files: int = 2000,
    ):
        self.repo_root = Path(repo_root).resolve()
        self.max_files = max_files
        self.files: dict[str, FileIndex] = {}  # relative_path -> FileIndex
        self._built = False

    def build(self) -> None:
        """Build the index by scanning all Python files."""
        if self._built:
            return

        for file_path in walk_files(
            self.repo_root,
            extensions={".py"},
            max_files=self.max_files,
        ):
            file_index = self._index_file(file_path)
            self.files[file_index.relative_path] = file_index

        self._built = True

    def _index_file(self, file_path: Path) -> FileIndex:
        """Index a single Python file."""
        relative_path = get_relative_path(file_path, self.repo_root)
        role = infer_module_role(relative_path)

        file_index = FileIndex(
            path=file_path,
            relative_path=relative_path,
            role=role,
        )

        content = read_file_safe(file_path)
        if content is None:
            file_index.parse_error = "Could not read file"
            return file_index

        file_index.lines = content.splitlines()

        try:
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError as e:
            file_index.parse_error = f"Syntax error: {e}"
            return file_index
        except Exception as e:
            file_index.parse_error = f"Parse error: {e}"
            return file_index

        # Extract information from AST
        visitor = _ASTVisitor(file_index)
        visitor.visit(tree)

        return file_index

    def get_files_by_role(self, role: str) -> list[FileIndex]:
        """Get all files with a specific role."""
        return [f for f in self.files.values() if f.role == role]

    def get_all_imports(self) -> list[tuple[str, ImportInfo]]:
        """Get all imports across all files as (relative_path, ImportInfo) tuples."""
        result = []
        for rel_path, file_idx in self.files.items():
            for imp in file_idx.imports:
                result.append((rel_path, imp))
        return result

    def get_all_calls(self) -> list[tuple[str, CallInfo]]:
        """Get all calls across all files."""
        result = []
        for rel_path, file_idx in self.files.items():
            for call in file_idx.calls:
                result.append((rel_path, call))
        return result

    def get_all_decorators(self) -> list[tuple[str, DecoratorInfo]]:
        """Get all decorators across all files."""
        result = []
        for rel_path, file_idx in self.files.items():
            for dec in file_idx.decorators:
                result.append((rel_path, dec))
        return result

    def get_all_functions(self) -> list[tuple[str, FunctionInfo]]:
        """Get all functions across all files."""
        result = []
        for rel_path, file_idx in self.files.items():
            for func in file_idx.functions:
                result.append((rel_path, func))
        return result

    def get_all_classes(self) -> list[tuple[str, ClassInfo]]:
        """Get all classes across all files."""
        result = []
        for rel_path, file_idx in self.files.items():
            for cls in file_idx.classes:
                result.append((rel_path, cls))
        return result

    def count_imports_matching(self, pattern: str) -> int:
        """Count imports where module matches pattern (substring or regex)."""
        count = 0
        for file_idx in self.files.values():
            for imp in file_idx.imports:
                if pattern in imp.module:
                    count += 1
                elif imp.names and any(pattern in name for name in imp.names):
                    count += 1
        return count

    def count_calls_matching(self, pattern: str) -> int:
        """Count calls where name matches pattern."""
        count = 0
        for file_idx in self.files.values():
            for call in file_idx.calls:
                if pattern in call.name:
                    count += 1
        return count

    def find_calls_matching(
        self,
        pattern: str,
        limit: int = 100,
    ) -> list[tuple[str, CallInfo]]:
        """Find calls matching pattern."""
        results = []
        for rel_path, file_idx in self.files.items():
            for call in file_idx.calls:
                if pattern in call.name:
                    results.append((rel_path, call))
                    if len(results) >= limit:
                        return results
        return results

    def find_imports_matching(
        self,
        pattern: str,
        limit: int = 100,
    ) -> list[tuple[str, ImportInfo]]:
        """Find imports matching pattern."""
        results = []
        for rel_path, file_idx in self.files.items():
            for imp in file_idx.imports:
                if pattern in imp.module:
                    results.append((rel_path, imp))
                    if len(results) >= limit:
                        return results
                elif imp.names and any(pattern in name for name in imp.names):
                    results.append((rel_path, imp))
                    if len(results) >= limit:
                        return results
        return results


class _ASTVisitor(ast.NodeVisitor):
    """AST visitor that extracts information for the index."""

    def __init__(self, file_index: FileIndex):
        self.file_index = file_index

    def visit_Import(self, node: ast.Import) -> None:
        """Process import statements and record import information."""
        for alias in node.names:
            self.file_index.imports.append(ImportInfo(
                module=alias.name,
                names=[],
                line=node.lineno,
            ))
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Process from-import statements and record import information."""
        module = node.module or ""
        names = [alias.name for alias in node.names]
        self.file_index.imports.append(ImportInfo(
            module=module,
            names=names,
            line=node.lineno,
        ))
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Process synchronous function definitions."""
        self._process_function(node, is_async=False)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Process asynchronous function definitions."""
        self._process_function(node, is_async=True)
        self.generic_visit(node)

    def _process_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        is_async: bool,
    ) -> None:
        # Count annotations
        annotated_args = 0
        total_args = len(node.args.args) + len(node.args.posonlyargs) + len(node.args.kwonlyargs)

        for arg in node.args.args + node.args.posonlyargs + node.args.kwonlyargs:
            if arg.annotation is not None:
                annotated_args += 1

        # Check for docstring
        has_docstring = False
        docstring = None
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            has_docstring = True
            docstring = node.body[0].value.value

        # Extract decorators
        decorators = [get_decorator_name(d) for d in node.decorator_list]

        self.file_index.functions.append(FunctionInfo(
            name=node.name,
            line=node.lineno,
            is_async=is_async,
            has_return_annotation=node.returns is not None,
            annotated_args=annotated_args,
            total_args=total_args,
            has_docstring=has_docstring,
            docstring=docstring,
            decorators=decorators,
        ))

        # Also record decorators
        for dec in node.decorator_list:
            self._record_decorator(dec)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        # Extract base classes
        bases = [get_dotted_name(base) for base in node.bases]
        bases = [b for b in bases if b]

        # Check for docstring
        has_docstring = False
        docstring = None
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            has_docstring = True
            docstring = node.body[0].value.value

        # Extract decorators
        decorators = [get_decorator_name(d) for d in node.decorator_list]

        self.file_index.classes.append(ClassInfo(
            name=node.name,
            line=node.lineno,
            bases=bases,
            has_docstring=has_docstring,
            docstring=docstring,
            decorators=decorators,
        ))

        # Record decorators
        for dec in node.decorator_list:
            self._record_decorator(dec)

        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Process function calls and record call information."""
        call_name = get_dotted_name(node.func)
        if call_name:
            # Extract keyword argument names
            kwargs = [kw.arg for kw in node.keywords if kw.arg is not None]

            self.file_index.calls.append(CallInfo(
                name=call_name,
                line=node.lineno,
                kwargs=kwargs,
            ))

        self.generic_visit(node)

    def _record_decorator(self, node: ast.expr) -> None:
        """Record a decorator usage."""
        if isinstance(node, ast.Call):
            name = get_dotted_name(node.func)
            call_args = [kw.arg for kw in node.keywords if kw.arg is not None]
        else:
            name = get_dotted_name(node)
            call_args = []

        if name:
            self.file_index.decorators.append(DecoratorInfo(
                name=name,
                line=node.lineno,
                call_args=call_args,
            ))


def get_dotted_name(node: ast.expr) -> Optional[str]:
    """
    Extract a dotted name from an AST node.

    Examples:
        Name('foo') -> 'foo'
        Attribute(Name('foo'), 'bar') -> 'foo.bar'
        Attribute(Attribute(Name('a'), 'b'), 'c') -> 'a.b.c'
    """
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        base = get_dotted_name(node.value)
        if base:
            return f"{base}.{node.attr}"
        return node.attr
    elif isinstance(node, ast.Call):
        return get_dotted_name(node.func)
    return None


def get_decorator_name(node: ast.expr) -> str:
    """Extract decorator name, handling both simple and call decorators."""
    if isinstance(node, ast.Call):
        return get_dotted_name(node.func) or ""
    return get_dotted_name(node) or ""


def infer_module_role(relative_path: str) -> str:
    """
    Infer the role of a module from its relative path.

    Returns one of: api, service, db, test, other
    """
    path_lower = relative_path.lower()
    parts = Path(relative_path).parts

    # Test files
    if any(p in ("tests", "test") for p in parts):
        return "test"
    if path_lower.endswith("_test.py") or path_lower.endswith("test_.py"):
        return "test"
    if "conftest" in path_lower:
        return "test"

    # API/router files
    api_patterns = ("api", "routes", "routers", "endpoints", "views", "handlers", "controllers")
    if any(p in api_patterns for p in parts):
        return "api"

    # Database/model files
    db_patterns = ("db", "database", "models", "repositories", "repo", "dal", "orm")
    if any(p in db_patterns for p in parts):
        return "db"

    # Service layer
    service_patterns = ("services", "service", "business", "logic", "domain", "usecases")
    if any(p in service_patterns for p in parts):
        return "service"

    # Schema/DTO files
    if any(p in ("schemas", "dtos", "dto") for p in parts):
        return "schema"

    return "other"


def make_evidence(
    index: PythonIndex,
    relative_path: str,
    line: int,
    radius: int = 5,
) -> Optional[EvidenceSnippet]:
    """
    Create an evidence snippet from the index.

    Args:
        index: The Python index
        relative_path: Relative path to the file
        line: Target line number (1-indexed)
        radius: Lines of context before/after

    Returns:
        EvidenceSnippet or None if not available
    """
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
