"""Task runner conventions detector.

Detects and parses Makefile, package.json scripts, Taskfile, and justfile.
"""

from __future__ import annotations

import json
import re

from ...fs import read_file_safe
from ..base import BaseDetector, DetectorContext, DetectorResult
from ..registry import DetectorRegistry


@DetectorRegistry.register
class TaskRunnerDetector(BaseDetector):
    """Detect task runner configurations."""

    name = "generic_task_runners"
    description = "Detects task runners: Makefile, package.json scripts, Taskfile, justfile"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect task runner patterns."""
        result = DetectorResult()

        targets: dict[str, list[dict[str, str]]] = {}

        self._detect_makefile(ctx, targets)
        self._detect_package_json_scripts(ctx, targets)
        self._detect_taskfile(ctx, targets)
        self._detect_justfile(ctx, targets)

        if not targets:
            return result

        total = sum(len(v) for v in targets.values())
        runners = sorted(targets.keys())

        # Primary runner: prefer Makefile > Taskfile > justfile > package_json
        priority = ["makefile", "taskfile", "justfile", "package_json"]
        primary = runners[0]
        for p in priority:
            if p in runners:
                primary = p
                break

        runner_labels = {
            "makefile": "Makefile",
            "package_json": "package.json scripts",
            "taskfile": "Taskfile",
            "justfile": "justfile",
        }
        runner_strs = [runner_labels.get(r, r) for r in runners]

        description = (
            f"Task runners detected: {', '.join(runner_strs)}. "
            f"{total} total targets/scripts."
        )

        confidence = min(0.95, 0.70 + len(runners) * 0.05 + total * 0.005)

        result.rules.append(self.make_rule(
            rule_id="generic.conventions.task_runner",
            category="build",
            title="Task runners",
            description=description,
            confidence=confidence,
            language="generic",
            evidence=[],
            stats={
                "runners_found": runners,
                "primary_runner": primary,
                "total_targets": total,
                "targets": targets,
            },
        ))

        return result

    def _detect_makefile(
        self,
        ctx: DetectorContext,
        targets: dict[str, list[dict[str, str]]],
    ) -> None:
        """Parse Makefile targets."""
        makefile = ctx.repo_root / "Makefile"
        if not makefile.is_file():
            return

        content = read_file_safe(makefile)
        if not content:
            return

        lines = content.splitlines()
        found: list[dict[str, str]] = []

        for i, line in enumerate(lines[:500]):
            # Match target lines: target_name: [dependencies]
            match = re.match(r"^([a-zA-Z_][\w-]*)\s*:", line)
            if not match:
                continue

            name = match.group(1)

            # Skip internal/special targets
            if name.startswith("_") or name.startswith("."):
                continue

            # Look for comment description on preceding line
            desc = ""
            if i > 0:
                prev = lines[i - 1].strip()
                if prev.startswith("## "):
                    desc = prev[3:].strip()
                elif prev.startswith("# "):
                    desc = prev[2:].strip()

            found.append({"name": name, "description": desc})

        if found:
            targets["makefile"] = found

    def _detect_package_json_scripts(
        self,
        ctx: DetectorContext,
        targets: dict[str, list[dict[str, str]]],
    ) -> None:
        """Parse package.json scripts."""
        pkg_json = ctx.repo_root / "package.json"
        if not pkg_json.is_file():
            return

        content = read_file_safe(pkg_json)
        if not content:
            return

        try:
            data = json.loads(content)
        except (json.JSONDecodeError, ValueError):
            return

        scripts = data.get("scripts", {})
        if not scripts or not isinstance(scripts, dict):
            return

        found: list[dict[str, str]] = []
        for name, command in scripts.items():
            found.append({"name": name, "command": str(command)})

        if found:
            targets["package_json"] = found

    def _detect_taskfile(
        self,
        ctx: DetectorContext,
        targets: dict[str, list[dict[str, str]]],
    ) -> None:
        """Parse Taskfile.yml tasks."""
        taskfile = None
        for name in ("Taskfile.yml", "Taskfile.yaml", "taskfile.yml", "taskfile.yaml"):
            candidate = ctx.repo_root / name
            if candidate.is_file():
                taskfile = candidate
                break

        if taskfile is None:
            return

        content = read_file_safe(taskfile)
        if not content:
            return

        lines = content.splitlines()
        found: list[dict[str, str]] = []

        in_tasks = False
        current_task: str | None = None
        current_desc = ""
        indent_level = 0

        for line in lines:
            stripped = line.strip()

            # Detect the tasks: top-level key
            if re.match(r"^tasks:\s*$", line):
                in_tasks = True
                indent_level = len(line) - len(line.lstrip()) + 2
                continue

            if not in_tasks:
                continue

            # If we encounter a non-indented line, we've left tasks section
            if line and not line[0].isspace() and not line.startswith(" "):
                break

            # Task name at the expected indent level
            task_match = re.match(r"^(\s+)(\w[\w-]*):\s*$", line)
            if task_match:
                leading = len(task_match.group(1))
                if leading == indent_level:
                    # Save previous task
                    if current_task:
                        found.append({"name": current_task, "description": current_desc})
                    current_task = task_match.group(2)
                    current_desc = ""
                continue

            # Description line under current task
            if current_task and stripped.startswith("desc:"):
                desc_match = re.match(r"desc:\s*['\"]?(.+?)['\"]?\s*$", stripped)
                if desc_match:
                    current_desc = desc_match.group(1)

        # Save last task
        if current_task:
            found.append({"name": current_task, "description": current_desc})

        if found:
            targets["taskfile"] = found

    def _detect_justfile(
        self,
        ctx: DetectorContext,
        targets: dict[str, list[dict[str, str]]],
    ) -> None:
        """Parse justfile recipes."""
        justfile = None
        for name in ("justfile", "Justfile", ".justfile"):
            candidate = ctx.repo_root / name
            if candidate.is_file():
                justfile = candidate
                break

        if justfile is None:
            return

        content = read_file_safe(justfile)
        if not content:
            return

        lines = content.splitlines()
        found: list[dict[str, str]] = []

        for i, line in enumerate(lines):
            # Recipe line: name [args]:
            match = re.match(r"^@?(\w[\w-]*)\s*(?:[^:]*)?:", line)
            if not match:
                continue

            name = match.group(1)

            # Skip if it looks like a variable assignment (name := value)
            if ":=" in line.split(":")[0]:
                continue

            # Look for comment description on preceding line
            desc = ""
            if i > 0:
                prev = lines[i - 1].strip()
                if prev.startswith("# "):
                    desc = prev[2:].strip()

            found.append({"name": name, "description": desc})

        if found:
            targets["justfile"] = found
