"""Rust Cargo.toml conventions detector."""

from __future__ import annotations

import re

from ..base import DetectorContext, DetectorResult
from ..registry import DetectorRegistry
from .base import RustDetector


@DetectorRegistry.register
class RustCargoDetector(RustDetector):
    """Detect Rust Cargo conventions."""

    name = "rust_cargo"
    description = "Analyzes Cargo.toml for dependencies and configuration"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect Cargo conventions."""
        result = DetectorResult()

        cargo_toml = ctx.repo_root / "Cargo.toml"
        if not cargo_toml.exists():
            return result

        content = cargo_toml.read_text()

        # Parse basic info
        info: dict = {}

        # Check for workspace
        is_workspace = "[workspace]" in content
        info["is_workspace"] = is_workspace

        # Count dependencies
        re.findall(r"\[(?:dev-)?dependencies(?:\.[^\]]+)?\]", content)
        dep_count = len(re.findall(r"^\s*\w+\s*=", content, re.MULTILINE))
        info["dependency_count"] = dep_count

        # Check edition
        edition_match = re.search(r'edition\s*=\s*"(\d+)"', content)
        if edition_match:
            info["edition"] = edition_match.group(1)

        # Check for Rust version (MSRV)
        rust_version_match = re.search(r'rust-version\s*=\s*"([^"]+)"', content)
        if rust_version_match:
            info["rust_version"] = rust_version_match.group(1)

        # Check for common features
        features = []

        # Check for workspace dependencies (Cargo 1.64+)
        if "[workspace.dependencies]" in content:
            features.append("workspace dependencies")

        # Check for build script
        if (ctx.repo_root / "build.rs").exists():
            features.append("build script")

        # Check for proc-macro
        if 'proc-macro = true' in content:
            features.append("proc-macro crate")

        # Check for multiple binaries
        bin_count = len(re.findall(r"\[\[bin\]\]", content))
        if bin_count > 1:
            features.append(f"{bin_count} binaries")

        # Check for features section
        if "[features]" in content:
            feature_count = len(re.findall(r"^\s*\w+\s*=\s*\[", content, re.MULTILINE))
            if feature_count > 0:
                features.append(f"{feature_count} feature flags")

        # Check Cargo.lock
        has_lock = (ctx.repo_root / "Cargo.lock").exists()
        info["has_lock"] = has_lock

        # Check for vendored dependencies
        has_vendor = (ctx.repo_root / "vendor").is_dir()
        if has_vendor:
            features.append("vendored dependencies")

        # Determine crate type
        if is_workspace:
            crate_type = "workspace"
            members = re.findall(r'members\s*=\s*\[(.*?)\]', content, re.DOTALL)
            if members:
                member_count = len(re.findall(r'"[^"]+"', members[0]))
                info["workspace_members"] = member_count
        elif 'proc-macro = true' in content:
            crate_type = "proc-macro"
        elif (ctx.repo_root / "src" / "main.rs").exists():
            crate_type = "binary"
        else:
            crate_type = "library"

        info["crate_type"] = crate_type

        title = f"Cargo: {crate_type} crate"
        description = f"Rust {crate_type} crate with {dep_count} dependencies."

        if info.get("edition"):
            description += f" Edition {info['edition']}."

        if info.get("rust_version"):
            description += f" MSRV: {info['rust_version']}."

        if features:
            description += f" Features: {', '.join(features[:3])}."

        confidence = 0.95

        result.rules.append(self.make_rule(
            rule_id="rust.conventions.cargo",
            category="project",
            title=title,
            description=description,
            confidence=confidence,
            language="rust",
            evidence=[],
            stats={
                "crate_type": crate_type,
                "is_workspace": is_workspace,
                "dependency_count": dep_count,
                "edition": info.get("edition"),
                "rust_version": info.get("rust_version"),
                "has_lock": has_lock,
                "features": features,
            },
        ))

        return result
