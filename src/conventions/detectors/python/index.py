"""Python code indexer using AST analysis."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

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
    is_relative: bool = False  # True for relative imports (from . or from ..)


@dataclass
class DecoratorInfo:
    """Information about a decorator usage."""

    name: str  # Full dotted name
    line: int
    call_args: list[str] = field(default_factory=list)  # Argument names if it's a call


@dataclass
class ExceptHandlerInfo:
    """Information about an except handler and what it calls."""

    line: int
    exception_types: list[str] = field(default_factory=list)  # e.g., ["ValueError", "KeyError"]
    calls_in_handler: list[str] = field(default_factory=list)  # Functions called in the handler
    raises_in_handler: list[str] = field(default_factory=list)  # Exceptions raised in the handler
    returns_call: Optional[str] = None  # If handler returns a function call result


@dataclass
class StringFormatInfo:
    """Information about string formatting usage."""

    line: int
    format_type: str  # "fstring", "format_method", "percent", "concat"


@dataclass
class WithStatementInfo:
    """Information about a with/context manager statement."""

    line: int
    context_expr: str  # The expression being used as context manager
    is_async: bool = False


@dataclass
class ConstantInfo:
    """Information about a module-level constant."""

    name: str
    line: int
    is_all_caps: bool = False  # ALL_CAPS naming
    value_type: Optional[str] = None  # "str", "int", "enum", etc.


@dataclass
class ReturnInfo:
    """Information about a return statement."""

    line: int
    returns_none: bool = False  # Explicit return None or bare return
    returns_optional: bool = False  # Returns Optional[X] type
    in_function: str = ""  # Which function this return is in


@dataclass
class AssertInfo:
    """Information about an assert statement."""

    line: int
    in_function: str = ""  # Which function this assert is in


@dataclass
class RaiseInfo:
    """Information about a raise statement."""

    line: int
    exception_type: Optional[str] = None  # The exception being raised
    has_from_clause: bool = False  # True if `raise X from Y` is used
    is_bare_raise: bool = False  # True if just `raise` (re-raise)


@dataclass
class FileIndex:
    """Index of a single Python file."""

    path: Path
    relative_path: str
    role: str  # api, service, db, test, docs, other
    parse_error: Optional[str] = None

    # Test file classification (only relevant when role == "test")
    is_test_file: bool = False  # True for test_*.py or *_test.py files
    is_conftest: bool = False  # True for conftest.py files

    # Collected data
    imports: list[ImportInfo] = field(default_factory=list)
    functions: list[FunctionInfo] = field(default_factory=list)
    classes: list[ClassInfo] = field(default_factory=list)
    calls: list[CallInfo] = field(default_factory=list)
    decorators: list[DecoratorInfo] = field(default_factory=list)
    except_handlers: list[ExceptHandlerInfo] = field(default_factory=list)
    string_formats: list[StringFormatInfo] = field(default_factory=list)
    with_statements: list[WithStatementInfo] = field(default_factory=list)
    constants: list[ConstantInfo] = field(default_factory=list)
    returns: list[ReturnInfo] = field(default_factory=list)
    asserts: list[AssertInfo] = field(default_factory=list)
    raises: list[RaiseInfo] = field(default_factory=list)

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
        exclude_patterns: Optional[list[str]] = None,
    ):
        self.repo_root = Path(repo_root).resolve()
        self.max_files = max_files
        self.exclude_patterns = exclude_patterns or []
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
            exclude_patterns=self.exclude_patterns,
        ):
            file_index = self._index_file(file_path)
            self.files[file_index.relative_path] = file_index

        self._built = True

    def _index_file(self, file_path: Path) -> FileIndex:
        """Index a single Python file."""
        relative_path = get_relative_path(file_path, self.repo_root)
        role = infer_module_role(relative_path)

        # Determine test file classification
        filename = file_path.name.lower()
        is_test_file = (
            filename.startswith("test_") and filename.endswith(".py")
        ) or (
            filename.endswith("_test.py")
        )
        is_conftest = filename == "conftest.py"

        file_index = FileIndex(
            path=file_path,
            relative_path=relative_path,
            role=role,
            is_test_file=is_test_file,
            is_conftest=is_conftest,
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

    def get_test_files(self, include_support: bool = False) -> list[FileIndex]:
        """
        Get test files.

        Args:
            include_support: If True, includes all files in test directories.
                           If False (default), only returns actual test files
                           (test_*.py, *_test.py) and conftest.py.
        """
        if include_support:
            return [f for f in self.files.values() if f.role == "test"]
        return [
            f for f in self.files.values()
            if f.role == "test" and (f.is_test_file or f.is_conftest)
        ]

    def get_conftest_files(self, include_docs: bool = False) -> list[FileIndex]:
        """
        Get conftest.py files.

        Args:
            include_docs: If True, includes conftest.py from docs/examples directories.
        """
        if include_docs:
            return [f for f in self.files.values() if f.is_conftest]
        return [
            f for f in self.files.values()
            if f.is_conftest and f.role == "test"
        ]

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

    def get_all_except_handlers(self) -> list[tuple[str, ExceptHandlerInfo]]:
        """Get all except handlers across all files."""
        result = []
        for rel_path, file_idx in self.files.items():
            for handler in file_idx.except_handlers:
                result.append((rel_path, handler))
        return result

    def get_all_string_formats(self) -> list[tuple[str, StringFormatInfo]]:
        """Get all string format usages across all files."""
        result = []
        for rel_path, file_idx in self.files.items():
            for fmt in file_idx.string_formats:
                result.append((rel_path, fmt))
        return result

    def get_all_with_statements(self) -> list[tuple[str, WithStatementInfo]]:
        """Get all with statements across all files."""
        result = []
        for rel_path, file_idx in self.files.items():
            for stmt in file_idx.with_statements:
                result.append((rel_path, stmt))
        return result

    def get_all_constants(self) -> list[tuple[str, ConstantInfo]]:
        """Get all module-level constants across all files."""
        result = []
        for rel_path, file_idx in self.files.items():
            for const in file_idx.constants:
                result.append((rel_path, const))
        return result

    def get_all_returns(self) -> list[tuple[str, ReturnInfo]]:
        """Get all return statements across all files."""
        result = []
        for rel_path, file_idx in self.files.items():
            for ret in file_idx.returns:
                result.append((rel_path, ret))
        return result

    def get_all_raises(self) -> list[tuple[str, RaiseInfo]]:
        """Get all raise statements across all files."""
        result = []
        for rel_path, file_idx in self.files.items():
            for raise_info in file_idx.raises:
                result.append((rel_path, raise_info))
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
        # node.level > 0 means relative import (from . or from ..)
        is_relative = node.level > 0
        self.file_index.imports.append(ImportInfo(
            module=module,
            names=names,
            line=node.lineno,
            is_relative=is_relative,
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
        bases: list[str] = [b for b in (get_dotted_name(base) for base in node.bases) if b is not None]

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

            # Check for .format() string formatting
            if call_name.endswith(".format"):
                self.file_index.string_formats.append(StringFormatInfo(
                    line=node.lineno,
                    format_type="format_method",
                ))

        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        """Process try/except blocks and record except handler information."""
        for handler in node.handlers:
            # Get exception types being caught
            exception_types: list[str] = []
            if handler.type is not None:
                if isinstance(handler.type, ast.Tuple):
                    # Multiple exceptions: except (ValueError, KeyError)
                    for elt in handler.type.elts:
                        name = get_dotted_name(elt)
                        if name:
                            exception_types.append(name)
                else:
                    # Single exception: except ValueError
                    name = get_dotted_name(handler.type)
                    if name:
                        exception_types.append(name)

            # Find calls within the handler body
            calls_in_handler: list[str] = []
            raises_in_handler: list[str] = []
            returns_call: Optional[str] = None

            for stmt in handler.body:
                # Check for function calls
                for call_node in ast.walk(stmt):
                    if isinstance(call_node, ast.Call):
                        call_name = get_dotted_name(call_node.func)
                        if call_name:
                            calls_in_handler.append(call_name)

                # Check for raise statements
                if isinstance(stmt, ast.Raise):
                    if stmt.exc is not None:
                        if isinstance(stmt.exc, ast.Call):
                            raise_name = get_dotted_name(stmt.exc.func)
                            if raise_name:
                                raises_in_handler.append(raise_name)
                        else:
                            raise_name = get_dotted_name(stmt.exc)
                            if raise_name:
                                raises_in_handler.append(raise_name)

                # Check for return statements with a call
                if isinstance(stmt, ast.Return) and stmt.value is not None:
                    if isinstance(stmt.value, ast.Call):
                        returns_call = get_dotted_name(stmt.value.func)

            self.file_index.except_handlers.append(ExceptHandlerInfo(
                line=handler.lineno,
                exception_types=exception_types,
                calls_in_handler=calls_in_handler,
                raises_in_handler=raises_in_handler,
                returns_call=returns_call,
            ))

        self.generic_visit(node)

    def visit_JoinedStr(self, node: ast.JoinedStr) -> None:
        """Process f-strings."""
        self.file_index.string_formats.append(StringFormatInfo(
            line=node.lineno,
            format_type="fstring",
        ))
        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp) -> None:
        """Process binary operations, looking for % string formatting."""
        if isinstance(node.op, ast.Mod) and isinstance(node.left, ast.Constant):
            if isinstance(node.left.value, str):
                self.file_index.string_formats.append(StringFormatInfo(
                    line=node.lineno,
                    format_type="percent",
                ))
        self.generic_visit(node)

    def visit_Assert(self, node: ast.Assert) -> None:
        """Process assert statements."""
        # Track current function context
        # Note: This is a simple approach; for nested functions we get the outermost
        current_function = ""
        for func in self.file_index.functions:
            if func.line <= node.lineno:
                current_function = func.name

        self.file_index.asserts.append(AssertInfo(
            line=node.lineno,
            in_function=current_function,
        ))
        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        """Process with statements (context managers)."""
        for item in node.items:
            context_expr = get_dotted_name(item.context_expr)
            if context_expr:
                self.file_index.with_statements.append(WithStatementInfo(
                    line=node.lineno,
                    context_expr=context_expr,
                    is_async=False,
                ))
        self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        """Process async with statements."""
        for item in node.items:
            context_expr = get_dotted_name(item.context_expr)
            if context_expr:
                self.file_index.with_statements.append(WithStatementInfo(
                    line=node.lineno,
                    context_expr=context_expr,
                    is_async=True,
                ))
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Process assignments, looking for module-level constants."""
        # Only track simple name assignments (not tuple unpacking, etc.)
        for target in node.targets:
            if isinstance(target, ast.Name):
                name = target.id
                is_all_caps = name.isupper() and "_" in name or (name.isupper() and len(name) > 1)

                # Determine value type
                value_type = None
                if isinstance(node.value, ast.Constant):
                    if isinstance(node.value.value, str):
                        value_type = "str"
                    elif isinstance(node.value.value, int):
                        value_type = "int"
                    elif isinstance(node.value.value, float):
                        value_type = "float"
                elif isinstance(node.value, ast.List):
                    value_type = "list"
                elif isinstance(node.value, ast.Dict):
                    value_type = "dict"
                elif isinstance(node.value, ast.Call):
                    call_name = get_dotted_name(node.value.func)
                    if call_name:
                        value_type = f"call:{call_name}"

                self.file_index.constants.append(ConstantInfo(
                    name=name,
                    line=node.lineno,
                    is_all_caps=is_all_caps,
                    value_type=value_type,
                ))
        self.generic_visit(node)

    def visit_Return(self, node: ast.Return) -> None:
        """Process return statements."""
        returns_none = node.value is None or (
            isinstance(node.value, ast.Constant) and node.value.value is None
        )

        self.file_index.returns.append(ReturnInfo(
            line=node.lineno,
            returns_none=returns_none,
        ))
        self.generic_visit(node)

    def visit_Raise(self, node: ast.Raise) -> None:
        """Process raise statements, tracking exception chaining."""
        exception_type: Optional[str] = None
        has_from_clause = node.cause is not None
        is_bare_raise = node.exc is None

        if node.exc is not None:
            if isinstance(node.exc, ast.Call):
                exception_type = get_dotted_name(node.exc.func)
            else:
                exception_type = get_dotted_name(node.exc)

        self.file_index.raises.append(RaiseInfo(
            line=node.lineno,
            exception_type=exception_type,
            has_from_clause=has_from_clause,
            is_bare_raise=is_bare_raise,
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

    Returns one of: api, service, db, test, docs, other
    """
    path_lower = relative_path.lower()
    parts = Path(relative_path).parts
    parts_lower = tuple(p.lower() for p in parts)

    # Test files
    if any(p in ("tests", "test") for p in parts_lower):
        return "test"
    if path_lower.endswith("_test.py") or path_lower.endswith("test_.py"):
        return "test"
    if "conftest" in path_lower:
        return "test"

    # Documentation/examples (deprioritized for convention detection)
    docs_patterns = (
        "docs", "doc", "documentation", "examples", "example",
        "tutorials", "tutorial", "samples", "sample", "demo", "demos",
        "docs_src", "doc_src", "sphinx", "mkdocs",
    )
    if any(p in docs_patterns for p in parts_lower):
        return "docs"

    # API/router files
    api_patterns = ("api", "routes", "routers", "endpoints", "views", "handlers", "controllers")
    if any(p in api_patterns for p in parts_lower):
        return "api"

    # Database/model files
    db_patterns = ("db", "database", "models", "repositories", "repo", "dal", "orm")
    if any(p in db_patterns for p in parts_lower):
        return "db"

    # Service layer
    service_patterns = ("services", "service", "business", "logic", "domain", "usecases")
    if any(p in service_patterns for p in parts_lower):
        return "service"

    # Schema/DTO files
    if any(p in ("schemas", "dtos", "dto") for p in parts_lower):
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
