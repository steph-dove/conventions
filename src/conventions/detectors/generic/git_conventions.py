"""Git conventions detector."""

from __future__ import annotations

import re
import subprocess

from ...fs import read_file_safe
from ..base import BaseDetector, DetectorContext, DetectorResult
from ..registry import DetectorRegistry


@DetectorRegistry.register
class GitConventionsDetector(BaseDetector):
    """Detect Git conventions and configuration."""

    name = "generic_git_conventions"
    description = "Detects Git commit conventions and configuration"

    def detect(self, ctx: DetectorContext) -> DetectorResult:
        """Detect Git conventions."""
        result = DetectorResult()

        # Detect commit message conventions
        self._detect_commit_conventions(ctx, result)

        # Detect branch naming conventions
        self._detect_branch_conventions(ctx, result)

        # Detect Git hooks
        self._detect_git_hooks(ctx, result)

        return result

    def _detect_commit_conventions(
        self,
        ctx: DetectorContext,
        result: DetectorResult,
    ) -> None:
        """Detect commit message conventions."""
        # Try to read recent commit messages
        try:
            git_result = subprocess.run(
                ["git", "log", "--oneline", "-50", "--format=%s"],
                cwd=ctx.repo_root,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if git_result.returncode != 0:
                return

            commits = git_result.stdout.strip().split("\n")
            if len(commits) < 10:
                return

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return

        # Conventional Commits pattern: type(scope): description
        conventional_pattern = r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(.+\))?!?:\s+"
        conventional_count = sum(1 for c in commits if re.match(conventional_pattern, c, re.IGNORECASE))

        # Gitmoji pattern: emoji at start
        gitmoji_pattern = r"^[\U0001F300-\U0001F9FF]|^:[a-z_]+:"
        gitmoji_count = sum(1 for c in commits if re.match(gitmoji_pattern, c))

        # Jira/ticket pattern: ABC-123
        ticket_pattern = r"^[A-Z]+-\d+"
        ticket_count = sum(1 for c in commits if re.match(ticket_pattern, c))

        total = len(commits)
        conventional_ratio = conventional_count / total
        gitmoji_ratio = gitmoji_count / total
        ticket_ratio = ticket_count / total

        if conventional_ratio >= 0.5:
            title = "Conventional Commits"
            description = (
                f"Uses Conventional Commits format. "
                f"{conventional_count}/{total} ({conventional_ratio:.0%}) commits follow the convention."
            )
            confidence = min(0.95, 0.6 + conventional_ratio * 0.3)
            convention = "conventional"
        elif gitmoji_ratio >= 0.3:
            title = "Gitmoji commits"
            description = (
                f"Uses Gitmoji in commit messages. "
                f"{gitmoji_count}/{total} ({gitmoji_ratio:.0%}) commits use emoji."
            )
            confidence = min(0.85, 0.5 + gitmoji_ratio * 0.3)
            convention = "gitmoji"
        elif ticket_ratio >= 0.3:
            title = "Ticket-prefixed commits"
            description = (
                f"Commits reference issue/ticket IDs. "
                f"{ticket_count}/{total} ({ticket_ratio:.0%}) commits have ticket prefix."
            )
            confidence = min(0.85, 0.5 + ticket_ratio * 0.3)
            convention = "ticket"
        else:
            title = "Freeform commit messages"
            description = "No specific commit message convention detected."
            confidence = 0.6
            convention = "freeform"

        result.rules.append(self.make_rule(
            rule_id="generic.conventions.commit_messages",
            category="git",
            title=title,
            description=description,
            confidence=confidence,
            language="generic",
            evidence=[],
            stats={
                "total_commits_analyzed": total,
                "conventional_count": conventional_count,
                "gitmoji_count": gitmoji_count,
                "ticket_count": ticket_count,
                "convention": convention,
                "conventional_ratio": round(conventional_ratio, 3),
            },
        ))

    def _detect_branch_conventions(
        self,
        ctx: DetectorContext,
        result: DetectorResult,
    ) -> None:
        """Detect branch naming conventions."""
        try:
            git_result = subprocess.run(
                ["git", "branch", "-r"],
                cwd=ctx.repo_root,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if git_result.returncode != 0:
                return

            branches = [
                b.strip().replace("origin/", "")
                for b in git_result.stdout.strip().split("\n")
                if b.strip() and "HEAD" not in b
            ]
            if len(branches) < 3:
                return

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return

        # GitFlow pattern: feature/, bugfix/, release/, hotfix/
        gitflow_pattern = r"^(feature|bugfix|release|hotfix|develop|main|master)/"
        gitflow_count = sum(1 for b in branches if re.match(gitflow_pattern, b))

        # GitHub Flow: main + feature branches
        has_main = any(b in ("main", "master") for b in branches)

        total = len(branches)
        gitflow_ratio = gitflow_count / total if total else 0

        if gitflow_ratio >= 0.3:
            title = "GitFlow branching"
            description = (
                f"Uses GitFlow-style branch naming. "
                f"{gitflow_count}/{total} branches follow pattern."
            )
            confidence = min(0.85, 0.5 + gitflow_ratio * 0.3)
            strategy = "gitflow"
        elif has_main:
            title = "Trunk-based/GitHub Flow"
            description = f"Uses trunk-based development with {total} branches."
            confidence = 0.7
            strategy = "trunk"
        else:
            return

        result.rules.append(self.make_rule(
            rule_id="generic.conventions.branch_naming",
            category="git",
            title=title,
            description=description,
            confidence=confidence,
            language="generic",
            evidence=[],
            stats={
                "total_branches": total,
                "gitflow_branches": gitflow_count,
                "strategy": strategy,
            },
        ))

    def _detect_git_hooks(
        self,
        ctx: DetectorContext,
        result: DetectorResult,
    ) -> None:
        """Detect Git hooks configuration."""
        # Check for pre-commit config
        pre_commit_config = ctx.repo_root / ".pre-commit-config.yaml"
        has_pre_commit = pre_commit_config.is_file()

        # Check for husky (Node.js)
        husky_dir = ctx.repo_root / ".husky"
        has_husky = husky_dir.is_dir()

        # Check for lefthook
        lefthook_config = ctx.repo_root / "lefthook.yml"
        has_lefthook = lefthook_config.is_file()

        hooks_tools = []
        if has_pre_commit:
            hooks_tools.append("pre-commit")
        if has_husky:
            hooks_tools.append("Husky")
        if has_lefthook:
            hooks_tools.append("Lefthook")

        if not hooks_tools:
            return

        # Analyze pre-commit config for hooks
        hooks_configured = []
        if has_pre_commit:
            content = read_file_safe(pre_commit_config)
            if content:
                if "trailing-whitespace" in content:
                    hooks_configured.append("whitespace")
                if "check-yaml" in content or "check-json" in content:
                    hooks_configured.append("file validation")
                if "black" in content or "prettier" in content or "ruff" in content:
                    hooks_configured.append("formatting")
                if "flake8" in content or "eslint" in content or "mypy" in content:
                    hooks_configured.append("linting")
                if "detect-secrets" in content or "gitleaks" in content:
                    hooks_configured.append("secrets detection")

        title = f"Git hooks: {', '.join(hooks_tools)}"
        description = f"Uses {', '.join(hooks_tools)} for Git hooks."
        if hooks_configured:
            description += f" Configured: {', '.join(hooks_configured)}."
        confidence = min(0.9, 0.7 + len(hooks_tools) * 0.1)

        # Determine primary hook tool (prefer pre-commit > husky > lefthook)
        hook_tool = None
        if has_pre_commit:
            hook_tool = "pre-commit"
        elif has_husky:
            hook_tool = "husky"
        elif has_lefthook:
            hook_tool = "lefthook"

        result.rules.append(self.make_rule(
            rule_id="generic.conventions.git_hooks",
            category="git",
            title=title,
            description=description,
            confidence=confidence,
            language="generic",
            evidence=[],
            stats={
                "hooks_tools": hooks_tools,
                "hooks_configured": hooks_configured,
                "hook_tool": hook_tool,
                "has_pre_commit": has_pre_commit,
                "has_husky": has_husky,
                "has_lefthook": has_lefthook,
            },
        ))
