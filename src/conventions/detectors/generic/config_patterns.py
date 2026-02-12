"""Config and secret access patterns detector.

Detects how the project accesses configuration and secrets.
"""

from __future__ import annotations

import re

from ...fs import read_file_safe, walk_files
from ..base import BaseDetector, DetectorContext, DetectorResult
from ..registry import DetectorRegistry

# Config access patterns to search for in source files
_ENV_ACCESS_PATTERNS = [
    ("python_os_environ", re.compile(r"""os\.environ|os\.getenv\(""")),
    ("node_process_env", re.compile(r"""process\.env\.""")),
    ("go_os_getenv", re.compile(r"""os\.Getenv\(""")),
    ("rust_std_env", re.compile(r"""std::env::var""")),
]

_CONFIG_LIBRARY_PATTERNS = [
    ("pydantic_settings", re.compile(r"""(?:from\s+pydantic_settings|BaseSettings)""")),
    ("python_dotenv", re.compile(r"""(?:from\s+dotenv|load_dotenv)""")),
    ("python_dynaconf", re.compile(r"""(?:from\s+dynaconf|Dynaconf)""")),
    ("go_viper", re.compile(r"""(?:viper\.|"github\.com/spf13/viper")""")),
    ("go_envconfig", re.compile(r'"github\.com/kelseyhightower/envconfig"')),
    ("node_dotenv", re.compile(r"""(?:require\(['"]dotenv|from\s+['"]dotenv)""")),
    ("node_config", re.compile(r"""(?:require\(['"]config['"]|from\s+['"]config['"])""")),
    ("node_convict", re.compile(r"""(?:require\(['"]convict|from\s+['"]convict)""")),
]

_SECRETS_PATTERNS = [
    ("aws_secrets_manager", re.compile(r"""(?:secretsmanager|SecretsManager|GetSecretValue)""")),
    ("hashicorp_vault", re.compile(r"""(?:hvac|vault\.read|VaultClient)""")),
    ("gcp_secret_manager", re.compile(r"""(?:secretmanager|SecretManagerService)""")),
    ("azure_keyvault", re.compile(r"""(?:azure.*keyvault|KeyVaultClient|SecretClient)""")),
    ("doppler", re.compile(r"""(?:doppler|DOPPLER_)""")),
    ("infisical", re.compile(r"""(?:infisical|InfisicalClient)""")),
]

# Source file extensions to scan
_SOURCE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs",
    ".mjs", ".cjs",
}


@DetectorRegistry.register
class ConfigPatternsDetector(BaseDetector):
    """Detect config and secret access patterns."""

    name = "generic_config_patterns"
    description = "Detects config access patterns, config libraries, and secrets management"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect config patterns."""
        result = DetectorResult()

        self._detect_config_access(ctx, result)
        self._detect_config_files(ctx, result)

        return result

    def _detect_config_access(
        self,
        ctx: DetectorContext,
        result: DetectorResult,
    ) -> None:
        """Scan source files for config access patterns."""
        env_counts: dict[str, int] = {}
        lib_counts: dict[str, int] = {}
        secrets_counts: dict[str, int] = {}

        for file_path in walk_files(
            ctx.repo_root,
            extensions=_SOURCE_EXTENSIONS,
            max_files=ctx.max_files,
        ):
            content = read_file_safe(file_path)
            if not content:
                continue

            for name, pattern in _ENV_ACCESS_PATTERNS:
                count = len(pattern.findall(content))
                if count:
                    env_counts[name] = env_counts.get(name, 0) + count

            for name, pattern in _CONFIG_LIBRARY_PATTERNS:
                count = len(pattern.findall(content))
                if count:
                    lib_counts[name] = lib_counts.get(name, 0) + count

            for name, pattern in _SECRETS_PATTERNS:
                count = len(pattern.findall(content))
                if count:
                    secrets_counts[name] = secrets_counts.get(name, 0) + count

        total = sum(env_counts.values()) + sum(lib_counts.values())
        if total < 2:
            return

        # Determine primary access style
        if lib_counts:
            primary_lib = max(lib_counts, key=lib_counts.get)  # type: ignore[arg-type]
            access_style = f"library ({primary_lib})"
        elif env_counts:
            primary_env = max(env_counts, key=env_counts.get)  # type: ignore[arg-type]
            access_style = f"direct env ({primary_env})"
        else:
            access_style = "unknown"

        parts = []
        if env_counts:
            parts.append(f"{sum(env_counts.values())} direct env accesses")
        if lib_counts:
            parts.append(f"libraries: {', '.join(lib_counts.keys())}")
        if secrets_counts:
            parts.append(f"secrets mgmt: {', '.join(secrets_counts.keys())}")

        description = f"Config access: {'; '.join(parts)}."

        result.rules.append(self.make_rule(
            rule_id="generic.conventions.config_access",
            category="configuration",
            title="Config access patterns",
            description=description,
            confidence=min(0.90, 0.65 + total * 0.01),
            language="generic",
            evidence=[],
            stats={
                "access_style": access_style,
                "env_access_counts": env_counts,
                "libraries": lib_counts,
                "secrets_managers": secrets_counts,
                "total_env_accesses": sum(env_counts.values()),
            },
        ))

    def _detect_config_files(
        self,
        ctx: DetectorContext,
        result: DetectorResult,
    ) -> None:
        """Detect config file patterns."""
        config_files: list[str] = []

        # Check for well-known config files
        candidates = [
            "config.yaml", "config.yml", "config.json", "config.toml",
            "application.yml", "application.yaml", "application.properties",
            "settings.yaml", "settings.yml", "settings.json", "settings.toml",
            "appsettings.json",
        ]
        for name in candidates:
            if (ctx.repo_root / name).is_file():
                config_files.append(name)

        # Check for config directories
        config_dirs: list[str] = []
        for dir_name in ("config", "settings", "conf"):
            d = ctx.repo_root / dir_name
            if d.is_dir():
                config_dirs.append(dir_name)

        if not config_files and not config_dirs:
            return

        parts = []
        if config_files:
            parts.append(f"files: {', '.join(config_files[:5])}")
        if config_dirs:
            parts.append(f"directories: {', '.join(config_dirs)}")

        description = f"Config structure: {'; '.join(parts)}."

        result.rules.append(self.make_rule(
            rule_id="generic.conventions.config_files",
            category="configuration",
            title="Config file structure",
            description=description,
            confidence=0.85,
            language="generic",
            evidence=[],
            stats={
                "config_files": config_files,
                "config_dirs": config_dirs,
            },
        ))
