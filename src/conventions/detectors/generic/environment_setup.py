"""Environment setup conventions detector.

Detects required environment variables, services, and runtime prerequisites.
"""

from __future__ import annotations

import re

from ...fs import read_file_safe
from ..base import BaseDetector, DetectorContext, DetectorResult
from ..registry import DetectorRegistry

# Category patterns for environment variable names
_VAR_CATEGORIES = [
    ("database", re.compile(r"^(DB_|DATABASE_|MONGO|MYSQL|POSTGRES|PG_|SQLITE)")),
    ("auth", re.compile(r"^(JWT_|AUTH_|SECRET|API_KEY|API_SECRET|TOKEN|OAUTH|SESSION_SECRET)")),
    ("service", re.compile(r"^(REDIS_|RABBITMQ_|AMQP_|S3_|AWS_|ELASTICSEARCH|KAFKA|SMTP_|MAIL_)")),
    ("app", re.compile(r"^(PORT|HOST|NODE_ENV|APP_ENV|DEBUG|LOG_LEVEL|BASE_URL|ALLOWED_HOSTS)")),
]


def _categorize_var(name: str) -> str:
    """Categorize an environment variable by its name prefix."""
    for category, pattern in _VAR_CATEGORIES:
        if pattern.match(name):
            return category
    return "other"


@DetectorRegistry.register
class EnvironmentSetupDetector(BaseDetector):
    """Detect environment setup requirements."""

    name = "generic_environment_setup"
    description = "Detects environment variables, required services, and runtime prerequisites"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect environment setup patterns."""
        result = DetectorResult()

        self._detect_env_example(ctx, result)
        self._detect_required_services(ctx, result)
        self._detect_prerequisites(ctx, result)

        return result

    def _detect_env_example(
        self,
        ctx: DetectorContext,
        result: DetectorResult,
    ) -> None:
        """Parse .env.example for required environment variables."""
        env_file = None
        env_name = None
        for name in (".env.example", ".env.sample", ".env.template"):
            candidate = ctx.repo_root / name
            if candidate.is_file():
                env_file = candidate
                env_name = name
                break

        if env_file is None:
            return

        content = read_file_safe(env_file)
        if not content:
            return

        env_vars: list[dict[str, str | bool]] = []
        categories: dict[str, int] = {}

        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)?$", line)
            if not match:
                continue

            name = match.group(1)
            value = match.group(2) or ""
            has_default = bool(value.strip())

            category = _categorize_var(name)
            categories[category] = categories.get(category, 0) + 1

            var_info: dict[str, str | bool] = {
                "name": name,
                "category": category,
                "has_default": has_default,
            }
            if has_default:
                var_info["default"] = value.strip()
            env_vars.append(var_info)

        if not env_vars:
            return

        description = (
            f"{len(env_vars)} environment variables defined in {env_name}. "
            f"Categories: {', '.join(f'{k} ({v})' for k, v in sorted(categories.items()))}."
        )

        result.rules.append(self.make_rule(
            rule_id="generic.conventions.env_setup",
            category="environment",
            title="Environment variables",
            description=description,
            confidence=0.90,
            language="generic",
            evidence=[],
            stats={
                "env_file": env_name,
                "env_vars": env_vars,
                "var_categories": categories,
                "total_vars": len(env_vars),
            },
        ))

    def _detect_required_services(
        self,
        ctx: DetectorContext,
        result: DetectorResult,
    ) -> None:
        """Parse docker-compose.yml for required services."""
        compose_file = None
        for name in ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"):
            candidate = ctx.repo_root / name
            if candidate.is_file():
                compose_file = candidate
                break

        if compose_file is None:
            return

        content = read_file_safe(compose_file)
        if not content:
            return

        # Parse services section using regex
        services: list[dict[str, str | list[str]]] = []
        lines = content.splitlines()

        in_services = False
        current_service: str | None = None
        current_image = ""
        current_ports: list[str] = []
        for line in lines:
            stripped = line.strip()

            # Find services: top-level key
            if re.match(r"^services:\s*$", line):
                in_services = True
                continue

            if not in_services:
                continue

            # Non-indented line = left services section
            if line and not line[0].isspace():
                break

            # Service name at expected indent
            svc_match = re.match(r"^(\s{2})(\w[\w-]*):\s*$", line)
            if svc_match:
                # Save previous service
                if current_service:
                    svc_info: dict[str, str | list[str]] = {
                        "name": current_service,
                        "image": current_image,
                    }
                    if current_ports:
                        svc_info["ports"] = current_ports
                    services.append(svc_info)
                current_service = svc_match.group(2)
                current_image = ""
                current_ports = []
                continue

            # Image line
            if current_service and stripped.startswith("image:"):
                img_match = re.match(r"image:\s*['\"]?([^\s'\"]+)", stripped)
                if img_match:
                    current_image = img_match.group(1)

            # Port lines
            if current_service and stripped.startswith("- ") and ":" in stripped:
                port_match = re.match(r"-\s*['\"]?(\d+:\d+)", stripped)
                if port_match:
                    current_ports.append(port_match.group(1))

        # Save last service
        if current_service:
            svc_info = {"name": current_service, "image": current_image}
            if current_ports:
                svc_info["ports"] = current_ports
            services.append(svc_info)

        if not services:
            return

        svc_names = [s["name"] for s in services]
        description = (
            f"{len(services)} services in docker-compose: {', '.join(str(n) for n in svc_names[:5])}."
        )

        result.rules.append(self.make_rule(
            rule_id="generic.conventions.required_services",
            category="environment",
            title="Required services",
            description=description,
            confidence=0.90,
            language="generic",
            evidence=[],
            stats={
                "services": services,
                "total_services": len(services),
            },
        ))

    def _detect_prerequisites(
        self,
        ctx: DetectorContext,
        result: DetectorResult,
    ) -> None:
        """Detect runtime version prerequisites."""
        tools: list[dict[str, str]] = []

        # .node-version
        node_ver = ctx.repo_root / ".node-version"
        if node_ver.is_file():
            content = read_file_safe(node_ver)
            if content and content.strip():
                tools.append({"name": "node", "version": content.strip(), "source": ".node-version"})

        # .nvmrc
        nvmrc = ctx.repo_root / ".nvmrc"
        if nvmrc.is_file() and not any(t["name"] == "node" for t in tools):
            content = read_file_safe(nvmrc)
            if content and content.strip():
                tools.append({"name": "node", "version": content.strip(), "source": ".nvmrc"})

        # .python-version
        py_ver = ctx.repo_root / ".python-version"
        if py_ver.is_file():
            content = read_file_safe(py_ver)
            if content and content.strip():
                tools.append({"name": "python", "version": content.strip().splitlines()[0], "source": ".python-version"})

        # rust-toolchain.toml or rust-toolchain
        for name in ("rust-toolchain.toml", "rust-toolchain"):
            rust_tc = ctx.repo_root / name
            if rust_tc.is_file():
                content = read_file_safe(rust_tc)
                if content:
                    ch_match = re.search(r'channel\s*=\s*["\']?([^\s"\']+)', content)
                    if ch_match:
                        tools.append({"name": "rust", "version": ch_match.group(1), "source": name})
                    elif content.strip() and name == "rust-toolchain":
                        tools.append({"name": "rust", "version": content.strip(), "source": name})
                break

        # .tool-versions (asdf)
        tool_versions = ctx.repo_root / ".tool-versions"
        if tool_versions.is_file():
            content = read_file_safe(tool_versions)
            if content:
                existing_names = {t["name"] for t in tools}
                for line in content.splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split()
                    if len(parts) >= 2 and parts[0] not in existing_names:
                        tools.append({"name": parts[0], "version": parts[1], "source": ".tool-versions"})

        # .go-version
        go_ver = ctx.repo_root / ".go-version"
        if go_ver.is_file():
            content = read_file_safe(go_ver)
            if content and content.strip():
                if not any(t["name"] == "go" for t in tools):
                    tools.append({"name": "go", "version": content.strip(), "source": ".go-version"})

        if not tools:
            return

        tool_strs = [f"{t['name']} {t['version']}" for t in tools]
        description = f"Runtime prerequisites: {', '.join(tool_strs)}."

        result.rules.append(self.make_rule(
            rule_id="generic.conventions.runtime_prerequisites",
            category="environment",
            title="Runtime prerequisites",
            description=description,
            confidence=0.90,
            language="generic",
            evidence=[],
            stats={
                "tools": tools,
            },
        ))
