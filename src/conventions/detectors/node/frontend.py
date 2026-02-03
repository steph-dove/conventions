"""Node.js frontend framework conventions detector."""

from __future__ import annotations

import json

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import NodeDetector
from .index import make_evidence


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
                examples.extend([(r, ln) for r, ln, _ in hook_patterns[:3]])

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
                examples.extend([(r, ln) for r, ln, _ in composition_matches[:3]])

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

        # Detect UI component library
        self._detect_ui_library(ctx, index, result, all_deps)

        return result

    def _detect_ui_library(
        self,
        ctx: DetectorContext,
        index,
        result: DetectorResult,
        all_deps: dict,
    ) -> None:
        """Detect UI component library (Material-UI, Chakra, Ant Design, etc.)."""
        ui_libs: dict[str, dict] = {}
        examples: list[tuple[str, int]] = []

        # Material-UI / MUI
        if "@mui/material" in all_deps:
            ui_libs["mui"] = {"name": "Material-UI (MUI)", "version": "v5+"}
            mui_imports = index.find_imports_matching("@mui/", limit=20)
            examples.extend([(r, ln) for r, _, ln in mui_imports[:3]])
        elif "@material-ui/core" in all_deps:
            ui_libs["mui"] = {"name": "Material-UI", "version": "v4"}
            mui_imports = index.find_imports_matching("@material-ui/", limit=20)
            examples.extend([(r, ln) for r, _, ln in mui_imports[:3]])

        # Chakra UI
        if "@chakra-ui/react" in all_deps:
            ui_libs["chakra"] = {"name": "Chakra UI"}
            chakra_imports = index.find_imports_matching("@chakra-ui/", limit=20)
            examples.extend([(r, ln) for r, _, ln in chakra_imports[:3]])

        # Ant Design
        if "antd" in all_deps:
            ui_libs["antd"] = {"name": "Ant Design"}
            antd_imports = index.find_imports_matching("antd", limit=20)
            examples.extend([(r, ln) for r, _, ln in antd_imports[:3]])

        # Radix UI
        if "@radix-ui/react-primitive" in all_deps or any(
            k.startswith("@radix-ui/") for k in all_deps
        ):
            ui_libs["radix"] = {"name": "Radix UI"}

        # Headless UI
        if "@headlessui/react" in all_deps:
            ui_libs["headless"] = {"name": "Headless UI"}

        # shadcn/ui (typically uses Radix + Tailwind)
        if "class-variance-authority" in all_deps and (
            "@radix-ui/react-slot" in all_deps or "cmdk" in all_deps
        ):
            ui_libs["shadcn"] = {"name": "shadcn/ui"}

        # React Bootstrap
        if "react-bootstrap" in all_deps:
            ui_libs["react_bootstrap"] = {"name": "React Bootstrap"}

        # Semantic UI React
        if "semantic-ui-react" in all_deps:
            ui_libs["semantic"] = {"name": "Semantic UI React"}

        # Mantine
        if "@mantine/core" in all_deps:
            ui_libs["mantine"] = {"name": "Mantine"}

        # Blueprint
        if "@blueprintjs/core" in all_deps:
            ui_libs["blueprint"] = {"name": "Blueprint"}

        # Vuetify (Vue)
        if "vuetify" in all_deps:
            ui_libs["vuetify"] = {"name": "Vuetify"}

        # PrimeReact / PrimeVue
        if "primereact" in all_deps:
            ui_libs["primereact"] = {"name": "PrimeReact"}
        if "primevue" in all_deps:
            ui_libs["primevue"] = {"name": "PrimeVue"}

        if not ui_libs:
            return

        # Determine primary library
        priority = ["mui", "chakra", "antd", "shadcn", "mantine", "radix"]
        primary = None
        for lib in priority:
            if lib in ui_libs:
                primary = lib
                break
        if primary is None:
            primary = list(ui_libs.keys())[0]

        lib_info = ui_libs[primary]
        title = f"UI library: {lib_info['name']}"
        description = f"Uses {lib_info['name']} for UI components."

        if lib_info.get("version"):
            description += f" ({lib_info['version']})"

        if len(ui_libs) > 1:
            others = [ui_libs[k]["name"] for k in ui_libs if k != primary]
            description += f" Also: {', '.join(others[:2])}."

        confidence = 0.95

        evidence = []
        for rel_path, line in examples[:ctx.max_evidence_snippets]:
            ev = make_evidence(index, rel_path, line, radius=3)
            if ev:
                evidence.append(ev)

        result.rules.append(self.make_rule(
            rule_id="node.conventions.ui_library",
            category="frontend",
            title=title,
            description=description,
            confidence=confidence,
            language="javascript",
            evidence=evidence,
            stats={
                "ui_libraries": list(ui_libs.keys()),
                "primary_library": primary,
                "library_details": ui_libs,
            },
        ))
