"""Node.js frontend framework conventions detector."""

from __future__ import annotations

import json
from pathlib import Path

from ..base import DetectorContext, DetectorResult
from .base import NodeDetector
from .index import make_evidence
from ..registry import DetectorRegistry


@DetectorRegistry.register
class NodeFrontendDetector(NodeDetector):
    """Detect Node.js frontend framework conventions."""

    name = "node_frontend"
    description = "Detects React, Vue, Svelte, Angular patterns and conventions"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect frontend framework conventions."""
        result = DetectorResult()
        index = self.get_index(ctx)

        frameworks: dict[str, dict] = {}
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

        # React detection
        react_imports = index.find_imports_matching("react", limit=30)
        react_imports = [i for i in react_imports if i[1] in ("react", "react-dom", "react/")]
        if react_imports or "react" in all_deps:
            frameworks["react"] = {"name": "React", "import_count": len(react_imports)}

            # Check for React patterns
            react_features = []

            # Hooks usage
            hook_patterns = index.search_pattern(
                r"use[A-Z]\w+\s*\(",
                limit=50,
                exclude_tests=True,
            )
            if hook_patterns:
                frameworks["react"]["hooks"] = True
                react_features.append("hooks")
                examples.extend([(r, l) for r, l, _ in hook_patterns[:3]])

            # Context usage
            context_matches = index.search_pattern(
                r"(?:createContext|useContext)\s*\(",
                limit=20,
                exclude_tests=True,
            )
            if context_matches:
                react_features.append("Context API")

            # Check for Next.js
            if "next" in all_deps:
                frameworks["nextjs"] = {"name": "Next.js"}
                if (ctx.repo_root / "next.config.js").exists() or \
                   (ctx.repo_root / "next.config.mjs").exists() or \
                   (ctx.repo_root / "next.config.ts").exists():
                    frameworks["nextjs"]["has_config"] = True

            # Check for Remix
            if "@remix-run/react" in all_deps:
                frameworks["remix"] = {"name": "Remix"}

            # Check for Gatsby
            if "gatsby" in all_deps:
                frameworks["gatsby"] = {"name": "Gatsby"}

            frameworks["react"]["features"] = react_features

        # Vue detection
        vue_imports = index.find_imports_matching("vue", limit=30)
        if vue_imports or "vue" in all_deps:
            frameworks["vue"] = {"name": "Vue", "import_count": len(vue_imports)}

            vue_features = []

            # Composition API
            composition_matches = index.search_pattern(
                r"(?:defineComponent|ref|reactive|computed|watch|onMounted)\s*\(",
                limit=30,
                exclude_tests=True,
            )
            if composition_matches:
                vue_features.append("Composition API")
                examples.extend([(r, l) for r, l, _ in composition_matches[:3]])

            # script setup
            script_setup = index.search_pattern(
                r"<script\s+setup",
                limit=10,
            )
            if script_setup:
                vue_features.append("<script setup>")

            # Check for Nuxt
            if "nuxt" in all_deps or (ctx.repo_root / "nuxt.config.ts").exists():
                frameworks["nuxt"] = {"name": "Nuxt"}

            frameworks["vue"]["features"] = vue_features

        # Svelte detection
        svelte_files = list(ctx.repo_root.rglob("*.svelte"))[:20]
        if svelte_files or "svelte" in all_deps:
            frameworks["svelte"] = {
                "name": "Svelte",
                "file_count": len(svelte_files),
            }

            # Check for SvelteKit
            if "@sveltejs/kit" in all_deps:
                frameworks["sveltekit"] = {"name": "SvelteKit"}

        # Angular detection
        angular_imports = index.find_imports_matching("@angular/", limit=30)
        if angular_imports or "@angular/core" in all_deps:
            frameworks["angular"] = {
                "name": "Angular",
                "import_count": len(angular_imports),
            }

        # Solid.js detection
        if "solid-js" in all_deps:
            frameworks["solid"] = {"name": "Solid.js"}

        # Preact detection
        if "preact" in all_deps:
            frameworks["preact"] = {"name": "Preact"}

        # Qwik detection
        if "@builder.io/qwik" in all_deps:
            frameworks["qwik"] = {"name": "Qwik"}

        if not frameworks:
            return result

        # Determine primary framework
        priority = ["react", "vue", "angular", "svelte", "solid", "preact", "qwik"]
        primary = None
        for fw in priority:
            if fw in frameworks:
                primary = fw
                break
        if primary is None:
            primary = list(frameworks.keys())[0]

        fw_info = frameworks[primary]
        title = f"Frontend: {fw_info['name']}"
        description = f"Uses {fw_info['name']}."

        features = fw_info.get("features", [])
        if features:
            description += f" Patterns: {', '.join(features)}."

        # Meta-frameworks
        meta_frameworks = []
        for key in ["nextjs", "nuxt", "sveltekit", "remix", "gatsby"]:
            if key in frameworks:
                meta_frameworks.append(frameworks[key]["name"])

        if meta_frameworks:
            description += f" Meta-framework: {', '.join(meta_frameworks)}."

        confidence = 0.95

        evidence = []
        for rel_path, line in examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="node.conventions.frontend",
            category="frontend",
            title=title,
            description=description,
            confidence=confidence,
            language="javascript",
            evidence=evidence,
            stats={
                "frameworks": list(frameworks.keys()),
                "primary_framework": primary,
                "meta_frameworks": meta_frameworks,
                "framework_details": frameworks,
            },
        ))

        return result
