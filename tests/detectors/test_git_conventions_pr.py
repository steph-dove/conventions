"""Tests for PR template detection."""
from __future__ import annotations

from pathlib import Path

from conventions.detectors.base import DetectorContext
from conventions.detectors.generic.git_conventions import GitConventionsDetector


class TestPRTemplateDetection:
    """Tests for PR template detection."""

    def test_detect_github_pr_template(self, tmp_path: Path):
        """Detects .github/pull_request_template.md."""
        github_dir = tmp_path / ".github"
        github_dir.mkdir()
        template = github_dir / "pull_request_template.md"
        template.write_text(
            "## Description\n\nDescribe your changes.\n\n"
            "## Testing\n\nHow was this tested?\n\n"
            "## Checklist\n\n- [ ] Tests added\n"
        )

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages=set(),
            max_files=100,
        )
        result = GitConventionsDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "generic.conventions.pr_template"]
        assert len(rules) == 1
        rule = rules[0]
        assert rule.stats["template_path"] == ".github/pull_request_template.md"
        assert "Description" in rule.stats["sections"]
        assert "Testing" in rule.stats["sections"]
        assert "Checklist" in rule.stats["sections"]

    def test_detect_root_pr_template(self, tmp_path: Path):
        """Detects PULL_REQUEST_TEMPLATE.md in root."""
        template = tmp_path / "PULL_REQUEST_TEMPLATE.md"
        template.write_text("## Summary\n\nBrief summary.\n")

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages=set(),
            max_files=100,
        )
        result = GitConventionsDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "generic.conventions.pr_template"]
        assert len(rules) == 1
        assert rules[0].stats["template_path"] == "PULL_REQUEST_TEMPLATE.md"
        assert "Summary" in rules[0].stats["sections"]

    def test_detect_multiple_pr_templates(self, tmp_path: Path):
        """Detects multiple PR template directory."""
        tmpl_dir = tmp_path / ".github" / "PULL_REQUEST_TEMPLATE"
        tmpl_dir.mkdir(parents=True)
        (tmpl_dir / "feature.md").write_text("## Feature\n")
        (tmpl_dir / "bugfix.md").write_text("## Bugfix\n")

        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages=set(),
            max_files=100,
        )
        result = GitConventionsDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "generic.conventions.pr_template"]
        assert len(rules) == 1
        assert rules[0].stats["has_multiple_templates"] is True
        assert rules[0].stats["template_count"] == 2

    def test_no_pr_template(self, tmp_path: Path):
        """No PR template emits no rule."""
        ctx = DetectorContext(
            repo_root=tmp_path,
            selected_languages=set(),
            max_files=100,
        )
        result = GitConventionsDetector().detect(ctx)

        rules = [r for r in result.rules if r.id == "generic.conventions.pr_template"]
        assert len(rules) == 0
