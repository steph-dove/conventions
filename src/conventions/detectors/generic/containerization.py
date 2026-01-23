"""Containerization conventions detector."""

from __future__ import annotations

import re
from pathlib import Path

from ..base import BaseDetector, DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from ...fs import read_file_safe


@DetectorRegistry.register
class ContainerizationDetector(BaseDetector):
    """Detect containerization patterns."""

    name = "generic_containerization"
    description = "Detects Docker and container configuration patterns"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect containerization patterns."""
        result = DetectorResult()

        # Detect Dockerfile patterns
        self._detect_dockerfile(ctx, result)

        # Detect Docker Compose
        self._detect_docker_compose(ctx, result)

        # Detect Kubernetes manifests
        self._detect_kubernetes(ctx, result)

        return result

    def _detect_dockerfile(
        self,
        ctx: DetectorContext,
        result: DetectorResult,
    ) -> None:
        """Detect Dockerfile patterns and best practices."""
        dockerfile_paths = [
            ctx.repo_root / "Dockerfile",
            ctx.repo_root / "docker" / "Dockerfile",
        ]

        # Also look for multi-stage Dockerfiles
        dockerfile_patterns = list(ctx.repo_root.glob("Dockerfile*")) + \
                             list(ctx.repo_root.glob("*.Dockerfile"))

        dockerfile = None
        for path in dockerfile_paths + dockerfile_patterns:
            if path.is_file():
                dockerfile = path
                break

        if dockerfile is None:
            return

        content = read_file_safe(dockerfile)
        if content is None:
            return

        # Analyze Dockerfile best practices
        practices: dict[str, bool] = {}

        # Multi-stage build
        from_count = len(re.findall(r"^FROM\s+", content, re.MULTILINE))
        practices["multi_stage"] = from_count > 1

        # Non-root user
        practices["non_root_user"] = bool(re.search(r"^USER\s+(?!root)", content, re.MULTILINE))

        # Health check
        practices["healthcheck"] = "HEALTHCHECK" in content

        # .dockerignore
        practices["dockerignore"] = (ctx.repo_root / ".dockerignore").is_file()

        # Specific base image (not :latest)
        latest_pattern = r"^FROM\s+\S+:latest"
        practices["pinned_version"] = not bool(re.search(latest_pattern, content, re.MULTILINE))

        # Layer caching optimization (COPY before RUN for dependencies)
        practices["layer_optimization"] = bool(
            re.search(r"COPY.*requirements.*\nRUN.*pip", content) or
            re.search(r"COPY.*package.*json.*\nRUN.*npm", content) or
            re.search(r"COPY.*go\.(mod|sum).*\nRUN.*go", content)
        )

        good_practices = [k for k, v in practices.items() if v]
        practice_count = len(good_practices)

        practice_names = {
            "multi_stage": "multi-stage build",
            "non_root_user": "non-root user",
            "healthcheck": "health check",
            "dockerignore": ".dockerignore",
            "pinned_version": "pinned base image",
            "layer_optimization": "layer caching",
        }

        if practice_count >= 3:
            title = "Dockerfile best practices"
            description = (
                f"Dockerfile follows best practices: "
                f"{', '.join(practice_names[p] for p in good_practices)}."
            )
        elif practice_count >= 1:
            title = "Dockerfile present"
            description = f"Dockerfile with {practice_count}/6 best practices."
        else:
            title = "Basic Dockerfile"
            description = "Dockerfile present but could use improvements."

        confidence = min(0.9, 0.5 + practice_count * 0.08)

        result.rules.append(self.make_rule(
            rule_id="generic.conventions.dockerfile",
            category="containerization",
            title=title,
            description=description,
            confidence=confidence,
            language="generic",
            evidence=[],
            stats={
                "practices": practices,
                "good_practice_count": practice_count,
                "from_count": from_count,
            },
        ))

    def _detect_docker_compose(
        self,
        ctx: DetectorContext,
        result: DetectorResult,
    ) -> None:
        """Detect Docker Compose configuration."""
        compose_paths = [
            ctx.repo_root / "docker-compose.yml",
            ctx.repo_root / "docker-compose.yaml",
            ctx.repo_root / "compose.yml",
            ctx.repo_root / "compose.yaml",
        ]

        compose_file = None
        for path in compose_paths:
            if path.is_file():
                compose_file = path
                break

        if compose_file is None:
            return

        content = read_file_safe(compose_file)
        if content is None:
            return

        # Count services
        service_count = len(re.findall(r"^\s{2}\w+:", content, re.MULTILINE))

        # Check for features
        features = []
        if "volumes:" in content:
            features.append("volumes")
        if "networks:" in content:
            features.append("networks")
        if "environment:" in content or "env_file:" in content:
            features.append("environment config")
        if "healthcheck:" in content:
            features.append("health checks")
        if "depends_on:" in content:
            features.append("dependencies")
        if "profiles:" in content:
            features.append("profiles")

        # Check for multiple compose files (override pattern)
        override_files = list(ctx.repo_root.glob("docker-compose.*.yml")) + \
                        list(ctx.repo_root.glob("docker-compose.*.yaml"))
        has_overrides = len(override_files) > 0

        title = "Docker Compose"
        description = f"Docker Compose with {service_count} services."
        if features:
            description += f" Features: {', '.join(features[:3])}."
        if has_overrides:
            description += f" Has {len(override_files)} override file(s)."

        confidence = min(0.9, 0.6 + service_count * 0.05)

        result.rules.append(self.make_rule(
            rule_id="generic.conventions.docker_compose",
            category="containerization",
            title=title,
            description=description,
            confidence=confidence,
            language="generic",
            evidence=[],
            stats={
                "service_count": service_count,
                "features": features,
                "has_overrides": has_overrides,
                "override_count": len(override_files),
            },
        ))

    def _detect_kubernetes(
        self,
        ctx: DetectorContext,
        result: DetectorResult,
    ) -> None:
        """Detect Kubernetes manifests."""
        k8s_dirs = [
            ctx.repo_root / "k8s",
            ctx.repo_root / "kubernetes",
            ctx.repo_root / "deploy",
            ctx.repo_root / "manifests",
            ctx.repo_root / "charts",  # Helm
        ]

        k8s_files = []
        for k8s_dir in k8s_dirs:
            if k8s_dir.is_dir():
                k8s_files.extend(k8s_dir.glob("**/*.yaml"))
                k8s_files.extend(k8s_dir.glob("**/*.yml"))

        # Also check for Helm Chart.yaml
        helm_chart = None
        for k8s_dir in k8s_dirs:
            chart_file = k8s_dir / "Chart.yaml"
            if chart_file.is_file():
                helm_chart = chart_file
                break

        # Check for kustomization
        kustomize_file = None
        for k8s_dir in k8s_dirs:
            for name in ["kustomization.yaml", "kustomization.yml"]:
                kust = k8s_dir / name
                if kust.is_file():
                    kustomize_file = kust
                    break

        if not k8s_files and not helm_chart and not kustomize_file:
            return

        tools = []
        if helm_chart:
            tools.append("Helm")
        if kustomize_file:
            tools.append("Kustomize")
        if k8s_files and not (helm_chart or kustomize_file):
            tools.append("raw manifests")

        title = f"Kubernetes: {', '.join(tools)}"
        description = f"Kubernetes deployment using {', '.join(tools)}."
        if k8s_files:
            description += f" {len(k8s_files)} manifest file(s)."

        confidence = min(0.9, 0.7 + len(tools) * 0.1)

        result.rules.append(self.make_rule(
            rule_id="generic.conventions.kubernetes",
            category="containerization",
            title=title,
            description=description,
            confidence=confidence,
            language="generic",
            evidence=[],
            stats={
                "tools": tools,
                "manifest_count": len(k8s_files),
                "has_helm": helm_chart is not None,
                "has_kustomize": kustomize_file is not None,
            },
        ))
