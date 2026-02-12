"""Node.js package manager conventions detector."""

from __future__ import annotations

import json
import re

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import NodeDetector


@DetectorRegistry.register
class NodePackageManagerDetector(NodeDetector):
    """Detect Node.js package manager conventions."""

    name = "node_package_manager"
    description = "Detects npm, yarn, pnpm, or bun usage"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect package manager conventions."""
        result = DetectorResult()

        managers: dict[str, dict] = {}

        # Check for lockfiles
        if (ctx.repo_root / "package-lock.json").exists():
            managers["npm"] = {
                "name": "npm",
                "lockfile": "package-lock.json",
            }

        if (ctx.repo_root / "yarn.lock").exists():
            managers["yarn"] = {
                "name": "Yarn",
                "lockfile": "yarn.lock",
            }
            # Check for Yarn version
            if (ctx.repo_root / ".yarnrc.yml").exists():
                managers["yarn"]["version"] = "berry (2+)"
            elif (ctx.repo_root / ".yarnrc").exists():
                managers["yarn"]["version"] = "classic (1.x)"

        if (ctx.repo_root / "pnpm-lock.yaml").exists():
            managers["pnpm"] = {
                "name": "pnpm",
                "lockfile": "pnpm-lock.yaml",
            }

        if (ctx.repo_root / "bun.lockb").exists():
            managers["bun"] = {
                "name": "Bun",
                "lockfile": "bun.lockb",
            }

        # Check package.json for packageManager field
        pkg_json_path = ctx.repo_root / "package.json"
        if pkg_json_path.exists():
            try:
                pkg_data = json.loads(pkg_json_path.read_text())
                if "packageManager" in pkg_data:
                    pm_spec = pkg_data["packageManager"]
                    if pm_spec.startswith("npm"):
                        if "npm" not in managers:
                            managers["npm"] = {"name": "npm"}
                        managers["npm"]["corepack"] = True
                    elif pm_spec.startswith("yarn"):
                        if "yarn" not in managers:
                            managers["yarn"] = {"name": "Yarn"}
                        managers["yarn"]["corepack"] = True
                    elif pm_spec.startswith("pnpm"):
                        if "pnpm" not in managers:
                            managers["pnpm"] = {"name": "pnpm"}
                        managers["pnpm"]["corepack"] = True
            except (json.JSONDecodeError, OSError):
                pass

        # Check for engine restrictions
        if pkg_json_path.exists():
            try:
                pkg_data = json.loads(pkg_json_path.read_text())
                engines = pkg_data.get("engines", {})
                for key in managers:
                    if key in engines:
                        managers[key]["engine_constraint"] = engines[key]
            except (json.JSONDecodeError, OSError):
                pass

        if not managers:
            # Default to npm if package.json exists
            if pkg_json_path.exists():
                managers["npm"] = {"name": "npm", "inferred": True}
            else:
                return result

        # Determine primary manager
        # Prefer explicit lockfiles over inferred
        if len(managers) == 1:
            primary = list(managers.keys())[0]
        else:
            # If multiple, prefer the one that's not inferred
            for key in ["pnpm", "yarn", "bun", "npm"]:
                if key in managers and not managers[key].get("inferred"):
                    primary = key
                    break
            else:
                primary = list(managers.keys())[0]

        pm_info = managers[primary]
        title = f"Package manager: {pm_info['name']}"
        description = f"Uses {pm_info['name']} for dependency management."

        if pm_info.get("version"):
            description += f" Version: {pm_info['version']}."

        if pm_info.get("corepack"):
            description += " Uses Corepack for version management."

        if len(managers) > 1:
            others = [m["name"] for k, m in managers.items() if k != primary]
            description += f" Also detected: {', '.join(others)}."

        confidence = 0.95
        if pm_info.get("inferred"):
            confidence = 0.6

        result.rules.append(self.make_rule(
            rule_id="node.conventions.package_manager",
            category="tooling",
            title=title,
            description=description,
            confidence=confidence,
            language="javascript",
            evidence=[],
            stats={
                "managers": list(managers.keys()),
                "primary_manager": primary,
                "manager_details": managers,
            },
        ))

        self._detect_dependency_health(ctx, managers, result)

        return result

    def _detect_dependency_health(
        self,
        ctx: DetectorContext,
        managers: dict[str, dict],
        result: DetectorResult,
    ) -> None:
        """Analyze dependency health: pinning strategy, lock file, engines."""
        pkg_json_path = ctx.repo_root / "package.json"
        if not pkg_json_path.is_file():
            return

        try:
            pkg_data = json.loads(pkg_json_path.read_text())
        except (json.JSONDecodeError, OSError):
            return

        # Analyze pinning strategy
        exact_count = 0
        caret_count = 0
        tilde_count = 0
        range_count = 0
        other_count = 0

        for deps_key in ("dependencies", "devDependencies"):
            deps = pkg_data.get(deps_key, {})
            if not isinstance(deps, dict):
                continue
            for _, version in deps.items():
                v = str(version).strip()
                if re.match(r"^\d+\.\d+\.\d+$", v):
                    exact_count += 1
                elif v.startswith("^"):
                    caret_count += 1
                elif v.startswith("~"):
                    tilde_count += 1
                elif v.startswith(">=") or v.startswith(">") or " " in v:
                    range_count += 1
                else:
                    other_count += 1

        total_deps = exact_count + caret_count + tilde_count + range_count + other_count
        if total_deps == 0:
            return

        # Determine dominant pinning strategy
        counts = {
            "exact": exact_count,
            "caret": caret_count,
            "tilde": tilde_count,
            "range": range_count,
        }
        pinning_strategy = max(counts, key=counts.get)  # type: ignore[arg-type]

        has_lock_file = any(
            (ctx.repo_root / lf).is_file()
            for lf in ("package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb")
        )

        engines = pkg_data.get("engines", {})
        has_engine_constraint = bool(engines)

        parts = [f"{total_deps} deps"]
        parts.append(f"pinning: {pinning_strategy} ({counts[pinning_strategy]}/{total_deps})")
        if has_lock_file:
            parts.append("lock file present")
        else:
            parts.append("no lock file")
        if has_engine_constraint:
            parts.append(f"engines: {', '.join(f'{k} {v}' for k, v in engines.items())}")

        description = f"Dependency health: {'; '.join(parts)}."

        result.rules.append(self.make_rule(
            rule_id="node.conventions.dependency_health",
            category="dependencies",
            title="Dependency health",
            description=description,
            confidence=0.85,
            language="node",
            evidence=[],
            stats={
                "total_deps": total_deps,
                "exact_count": exact_count,
                "caret_count": caret_count,
                "tilde_count": tilde_count,
                "range_count": range_count,
                "pinning_strategy": pinning_strategy,
                "has_lock_file": has_lock_file,
                "has_engine_constraint": has_engine_constraint,
                "engines": engines,
            },
        ))
