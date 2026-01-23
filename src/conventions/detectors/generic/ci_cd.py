"""CI/CD conventions detector."""

from __future__ import annotations

from ...fs import read_file_safe
from ..base import BaseDetector, DetectorContext, DetectorResult
from ..registry import DetectorRegistry


@DetectorRegistry.register
class CICDDetector(BaseDetector):
    """Detect CI/CD configuration patterns."""

    name = "generic_ci_cd"
    description = "Detects CI/CD platform configuration and patterns"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect CI/CD configuration patterns."""
        result = DetectorResult()

        # Detect CI/CD platform
        self._detect_ci_platform(ctx, result)

        # Detect CI configuration quality
        self._detect_ci_quality(ctx, result)

        return result

    def _detect_ci_platform(
        self,
        ctx: DetectorContext,
        result: DetectorResult,
    ) -> None:
        """Detect which CI/CD platform is used."""
        platforms: dict[str, dict] = {}

        # GitHub Actions
        gh_workflows = ctx.repo_root / ".github" / "workflows"
        if gh_workflows.is_dir():
            workflow_files = list(gh_workflows.glob("*.yml")) + list(gh_workflows.glob("*.yaml"))
            if workflow_files:
                platforms["github_actions"] = {
                    "name": "GitHub Actions",
                    "workflow_count": len(workflow_files),
                    "files": [f.name for f in workflow_files[:5]],
                }

        # GitLab CI
        gitlab_ci = ctx.repo_root / ".gitlab-ci.yml"
        if gitlab_ci.is_file():
            platforms["gitlab_ci"] = {
                "name": "GitLab CI",
                "files": [".gitlab-ci.yml"],
            }

        # CircleCI
        circleci = ctx.repo_root / ".circleci" / "config.yml"
        if circleci.is_file():
            platforms["circleci"] = {
                "name": "CircleCI",
                "files": ["config.yml"],
            }

        # Jenkins
        jenkinsfile = ctx.repo_root / "Jenkinsfile"
        if jenkinsfile.is_file():
            platforms["jenkins"] = {
                "name": "Jenkins",
                "files": ["Jenkinsfile"],
            }

        # Travis CI
        travis = ctx.repo_root / ".travis.yml"
        if travis.is_file():
            platforms["travis"] = {
                "name": "Travis CI",
                "files": [".travis.yml"],
            }

        # Azure Pipelines
        azure = ctx.repo_root / "azure-pipelines.yml"
        if azure.is_file():
            platforms["azure"] = {
                "name": "Azure Pipelines",
                "files": ["azure-pipelines.yml"],
            }

        # Bitbucket Pipelines
        bitbucket = ctx.repo_root / "bitbucket-pipelines.yml"
        if bitbucket.is_file():
            platforms["bitbucket"] = {
                "name": "Bitbucket Pipelines",
                "files": ["bitbucket-pipelines.yml"],
            }

        if not platforms:
            return

        platform_names = [p["name"] for p in platforms.values()]

        if len(platforms) == 1:
            primary = list(platforms.values())[0]
            title = f"CI/CD: {primary['name']}"
            description = f"Uses {primary['name']} for CI/CD."
            if primary.get("workflow_count"):
                description += f" {primary['workflow_count']} workflow(s) configured."
        else:
            title = "Multiple CI/CD platforms"
            description = f"Uses multiple CI/CD platforms: {', '.join(platform_names)}."

        confidence = min(0.95, 0.7 + len(platforms) * 0.1)

        result.rules.append(self.make_rule(
            rule_id="generic.conventions.ci_platform",
            category="ci_cd",
            title=title,
            description=description,
            confidence=confidence,
            language="generic",
            evidence=[],
            stats={
                "platforms": list(platforms.keys()),
                "platform_details": platforms,
            },
        ))

    def _detect_ci_quality(
        self,
        ctx: DetectorContext,
        result: DetectorResult,
    ) -> None:
        """Detect CI configuration quality indicators."""
        gh_workflows = ctx.repo_root / ".github" / "workflows"
        if not gh_workflows.is_dir():
            return

        workflow_files = list(gh_workflows.glob("*.yml")) + list(gh_workflows.glob("*.yaml"))
        if not workflow_files:
            return

        has_test_workflow = False
        has_lint_workflow = False
        has_deploy_workflow = False
        has_caching = False
        has_matrix = False

        for wf_file in workflow_files:
            content = read_file_safe(wf_file)
            if content is None:
                continue

            content_lower = content.lower()
            name_lower = wf_file.name.lower()

            # Check for test workflow
            if "test" in name_lower or "pytest" in content_lower or "npm test" in content_lower:
                has_test_workflow = True

            # Check for lint workflow
            if "lint" in name_lower or "eslint" in content_lower or "ruff" in content_lower or "flake8" in content_lower:
                has_lint_workflow = True

            # Check for deploy workflow
            if "deploy" in name_lower or "release" in name_lower:
                has_deploy_workflow = True

            # Check for caching
            if "actions/cache" in content or "cache:" in content:
                has_caching = True

            # Check for matrix builds
            if "matrix:" in content:
                has_matrix = True

        features = []
        if has_test_workflow:
            features.append("testing")
        if has_lint_workflow:
            features.append("linting")
        if has_deploy_workflow:
            features.append("deployment")
        if has_caching:
            features.append("caching")
        if has_matrix:
            features.append("matrix builds")

        if len(features) < 2:
            return

        title = "CI/CD best practices"
        description = f"CI configuration includes: {', '.join(features)}."
        confidence = min(0.9, 0.5 + len(features) * 0.1)

        result.rules.append(self.make_rule(
            rule_id="generic.conventions.ci_quality",
            category="ci_cd",
            title=title,
            description=description,
            confidence=confidence,
            language="generic",
            evidence=[],
            stats={
                "has_test_workflow": has_test_workflow,
                "has_lint_workflow": has_lint_workflow,
                "has_deploy_workflow": has_deploy_workflow,
                "has_caching": has_caching,
                "has_matrix": has_matrix,
                "features": features,
            },
        ))
