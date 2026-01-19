"""Go code generation conventions detector."""

from __future__ import annotations

import re

from ..base import DetectorContext, DetectorResult
from .base import GoDetector
from .index import GoIndex, make_evidence
from ..registry import DetectorRegistry


@DetectorRegistry.register
class GoCodegenDetector(GoDetector):
    """Detect Go code generation conventions."""

    name = "go_codegen"
    description = "Detects go:generate directives and code generation tools"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect go:generate and code generation conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        if not index.files:
            return result

        generate_directives: list[tuple[str, int, str]] = []
        tools_used: dict[str, int] = {}

        for file_idx in index.get_non_test_files():
            for i, line in enumerate(file_idx.lines, 1):
                if "//go:generate" in line:
                    generate_directives.append((file_idx.relative_path, i, line.strip()))

                    # Identify the tool
                    match = re.search(r'//go:generate\s+(\S+)', line)
                    if match:
                        tool = match.group(1)
                        # Normalize tool name
                        if "mockgen" in tool:
                            tool = "mockgen"
                        elif "stringer" in tool:
                            tool = "stringer"
                        elif "protoc" in tool:
                            tool = "protoc"
                        elif "sqlc" in tool:
                            tool = "sqlc"
                        elif "ent" in tool:
                            tool = "ent"
                        elif "go-enum" in tool:
                            tool = "go-enum"
                        elif "wire" in tool:
                            tool = "wire"

                        tools_used[tool] = tools_used.get(tool, 0) + 1

        if not generate_directives:
            return result

        tool_list = sorted(tools_used.keys(), key=lambda k: -tools_used[k])

        title = f"Code generation: {len(generate_directives)} directives"
        description = f"Uses go:generate with {len(generate_directives)} directive(s)."

        if tool_list:
            top_tools = tool_list[:3]
            description += f" Tools: {', '.join(top_tools)}."

        confidence = min(0.9, 0.6 + len(generate_directives) * 0.03)

        evidence = []
        for rel_path, line, _ in generate_directives[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=2)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="go.conventions.codegen",
            category="tooling",
            title=title,
            description=description,
            confidence=confidence,
            language="go",
            evidence=evidence,
            stats={
                "directive_count": len(generate_directives),
                "tools_used": tools_used,
                "top_tools": tool_list[:5],
            },
        ))

        return result
