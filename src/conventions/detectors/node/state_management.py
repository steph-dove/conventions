"""Node.js state management conventions detector."""

from __future__ import annotations

import json

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import NodeDetector
from .index import make_evidence


@DetectorRegistry.register
class NodeStateManagementDetector(NodeDetector):
    """Detect Node.js state management conventions."""

    name = "node_state_management"
    description = "Detects Redux, Zustand, Pinia, MobX, and other state management"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect state management conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        libraries: dict[str, dict] = {}
        examples: list[tuple[str, int]] = []

        pkg_json_path = ctx.repo_root / "package.json"
        all_deps = {}
        if pkg_json_path.exists():
            try:
                pkg_data = json.loads(pkg_json_path.read_text())
                all_deps = {
                    **pkg_data.get("dependencies", {}),
                    **pkg_data.get("devDependencies", {}),
                }
            except (json.JSONDecodeError, OSError):
                pass

        # Redux (and Redux Toolkit)
        if "@reduxjs/toolkit" in all_deps:
            libraries["redux_toolkit"] = {
                "name": "Redux Toolkit",
                "modern": True,
            }
        elif "redux" in all_deps:
            libraries["redux"] = {"name": "Redux"}

        # React Query / TanStack Query
        if "@tanstack/react-query" in all_deps:
            libraries["tanstack_query"] = {"name": "TanStack Query"}
        elif "react-query" in all_deps:
            libraries["react_query"] = {"name": "React Query"}

        # Zustand
        if "zustand" in all_deps:
            libraries["zustand"] = {"name": "Zustand"}
            zustand_imports = index.find_imports_matching("zustand", limit=20)
            examples.extend([(r, ln) for r, _, ln in zustand_imports[:3]])

        # Jotai
        if "jotai" in all_deps:
            libraries["jotai"] = {"name": "Jotai"}

        # Recoil
        if "recoil" in all_deps:
            libraries["recoil"] = {"name": "Recoil"}

        # MobX
        if "mobx" in all_deps:
            libraries["mobx"] = {"name": "MobX"}
            if "mobx-react" in all_deps or "mobx-react-lite" in all_deps:
                libraries["mobx"]["react_bindings"] = True

        # XState
        if "xstate" in all_deps:
            libraries["xstate"] = {"name": "XState (state machines)"}

        # Pinia (Vue)
        if "pinia" in all_deps:
            libraries["pinia"] = {"name": "Pinia"}

        # Vuex (legacy Vue)
        if "vuex" in all_deps:
            libraries["vuex"] = {"name": "Vuex"}

        # NgRx (Angular)
        if "@ngrx/store" in all_deps:
            libraries["ngrx"] = {"name": "NgRx"}

        # Effector
        if "effector" in all_deps:
            libraries["effector"] = {"name": "Effector"}

        # Valtio
        if "valtio" in all_deps:
            libraries["valtio"] = {"name": "Valtio"}

        # SWR
        if "swr" in all_deps:
            libraries["swr"] = {"name": "SWR (data fetching)"}

        if not libraries:
            return result

        # Determine primary (by typical popularity/preference)
        priority = [
            "redux_toolkit", "zustand", "tanstack_query", "pinia", "mobx",
            "jotai", "recoil", "ngrx", "redux", "react_query", "vuex",
            "xstate", "effector", "valtio", "swr",
        ]
        primary = None
        for lib in priority:
            if lib in libraries:
                primary = lib
                break
        if primary is None:
            primary = list(libraries.keys())[0]

        lib_info = libraries[primary]

        title = f"State management: {lib_info['name']}"
        description = f"Uses {lib_info['name']} for state management."

        if lib_info.get("modern"):
            description += " (modern approach)"

        if len(libraries) > 1:
            others = [lib["name"] for k, lib in libraries.items() if k != primary]
            description += f" Also: {', '.join(others[:3])}."

        confidence = 0.95

        evidence = []
        for rel_path, line in examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="node.conventions.state_management",
            category="patterns",
            title=title,
            description=description,
            confidence=confidence,
            language="javascript",
            evidence=evidence,
            stats={
                "libraries": list(libraries.keys()),
                "primary_library": primary,
                "library_details": libraries,
            },
        ))

        return result
