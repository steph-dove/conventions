"""Report generation for conventions detection."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .ratings import get_score_label, rate_convention
from .schemas import ConventionsOutput


def print_summary(output: ConventionsOutput, console: Optional[Console] = None) -> None:
    """Print a summary of detected conventions to the console."""
    if console is None:
        console = Console()

    # Header
    console.print()
    console.print(Panel.fit(
        "[bold]Conventions Detection Summary[/bold]",
        border_style="blue",
    ))

    # Metadata
    console.print(f"\n[bold]Repository:[/bold] {output.metadata.path}")
    console.print(f"[bold]Languages:[/bold] {', '.join(output.metadata.detected_languages) or 'none'}")
    console.print(f"[bold]Files scanned:[/bold] {output.metadata.total_files_scanned}")
    console.print(f"[bold]Rules detected:[/bold] {len(output.rules)}")
    console.print(f"[bold]Warnings:[/bold] {len(output.warnings)}")

    # Rules table
    if output.rules:
        console.print("\n[bold]Detected Conventions:[/bold]\n")

        table = Table(show_header=True, header_style="bold")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Title", style="white")
        table.add_column("Confidence", justify="right", style="green")
        table.add_column("Evidence", justify="right")

        for rule in sorted(output.rules, key=lambda r: (-r.confidence, r.id)):
            confidence_pct = f"{rule.confidence * 100:.0f}%"
            evidence_count = str(len(rule.evidence))
            table.add_row(rule.id, rule.title, confidence_pct, evidence_count)

        console.print(table)

    # Warnings
    if output.warnings:
        console.print("\n[bold yellow]Warnings:[/bold yellow]\n")
        for warning in output.warnings:
            console.print(f"  [yellow]{warning.detector}:[/yellow] {warning.message[:100]}...")

    console.print()


def print_detailed_rules(output: ConventionsOutput, console: Optional[Console] = None) -> None:
    """Print detailed information about each detected rule."""
    if console is None:
        console = Console()

    for rule in sorted(output.rules, key=lambda r: (-r.confidence, r.id)):
        console.print()
        console.print(Panel(
            f"[bold]{rule.title}[/bold]\n\n"
            f"[dim]{rule.description}[/dim]\n\n"
            f"[bold]Category:[/bold] {rule.category}\n"
            f"[bold]Language:[/bold] {rule.language or 'any'}\n"
            f"[bold]Confidence:[/bold] {rule.confidence * 100:.0f}%\n"
            f"[bold]Stats:[/bold] {rule.stats}",
            title=f"[cyan]{rule.id}[/cyan]",
            border_style="blue",
        ))

        if rule.evidence:
            console.print("\n[bold]Evidence:[/bold]")
            for i, ev in enumerate(rule.evidence[:3], 1):
                console.print(f"\n  [dim]{i}. {ev.file_path}:{ev.line_start}-{ev.line_end}[/dim]")
                for line in ev.excerpt.split("\n")[:5]:
                    console.print(f"     {line}")


def generate_markdown_report(output: ConventionsOutput) -> str:
    """Generate a markdown report of detected conventions."""
    lines: list[str] = []

    # Header
    lines.append("# Code Conventions Report")
    lines.append("")
    lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    lines.append("")

    # Metadata
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Repository:** `{output.metadata.path}`")
    lines.append(f"- **Languages:** {', '.join(output.metadata.detected_languages) or 'none'}")
    lines.append(f"- **Files scanned:** {output.metadata.total_files_scanned}")
    lines.append(f"- **Conventions detected:** {len(output.rules)}")
    if output.warnings:
        lines.append(f"- **Warnings:** {len(output.warnings)}")
    lines.append("")

    # Rules table
    if output.rules:
        lines.append("## Detected Conventions")
        lines.append("")
        lines.append("| ID | Title | Confidence | Evidence |")
        lines.append("|:---|:------|:----------:|:--------:|")

        for rule in sorted(output.rules, key=lambda r: (-r.confidence, r.id)):
            confidence_pct = f"{rule.confidence * 100:.0f}%"
            evidence_count = len(rule.evidence)
            lines.append(f"| `{rule.id}` | {rule.title} | {confidence_pct} | {evidence_count} |")

        lines.append("")

        # Detailed rules
        lines.append("## Convention Details")
        lines.append("")

        for rule in sorted(output.rules, key=lambda r: (-r.confidence, r.id)):
            lines.append(f"### {rule.title}")
            lines.append("")
            lines.append(f"**ID:** `{rule.id}`  ")
            lines.append(f"**Category:** {rule.category}  ")
            lines.append(f"**Language:** {rule.language or 'any'}  ")
            lines.append(f"**Confidence:** {rule.confidence * 100:.0f}%")
            lines.append("")
            lines.append(rule.description)
            lines.append("")

            if rule.stats:
                lines.append("**Statistics:**")
                lines.append("")
                for key, value in rule.stats.items():
                    lines.append(f"- {key}: `{value}`")
                lines.append("")

            if rule.evidence:
                lines.append("**Evidence:**")
                lines.append("")
                for i, ev in enumerate(rule.evidence[:3], 1):
                    lines.append(f"{i}. `{ev.file_path}:{ev.line_start}-{ev.line_end}`")
                    lines.append("")
                    lines.append("```")
                    for line in ev.excerpt.split("\n")[:10]:
                        lines.append(line)
                    lines.append("```")
                    lines.append("")

            lines.append("---")
            lines.append("")

    # Warnings
    if output.warnings:
        lines.append("## Warnings")
        lines.append("")
        for warning in output.warnings:
            lines.append(f"- **{warning.detector}:** {warning.message}")
        lines.append("")

    return "\n".join(lines)


def write_markdown_report(output: ConventionsOutput, repo_path: Path) -> Path:
    """Write a markdown report to the .conventions directory."""
    conventions_dir = repo_path / ".conventions"
    conventions_dir.mkdir(exist_ok=True)

    report_path = conventions_dir / "conventions.md"
    report_content = generate_markdown_report(output)
    report_path.write_text(report_content)

    return report_path


def generate_review_markdown(output: ConventionsOutput) -> str:
    """Generate a review report with ratings and improvement suggestions."""
    lines: list[str] = []

    # Header
    lines.append("# Conventions Review Report")
    lines.append("")
    lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    lines.append("")

    # Score legend
    lines.append("## Score Legend")
    lines.append("")
    lines.append("| Score | Rating |")
    lines.append("|:-----:|:-------|")
    lines.append("| 5 | Excellent |")
    lines.append("| 4 | Good |")
    lines.append("| 3 | Average |")
    lines.append("| 2 | Below Average |")
    lines.append("| 1 | Poor |")
    lines.append("")

    if not output.rules:
        lines.append("*No conventions detected to review.*")
        return "\n".join(lines)

    # Calculate overall score
    scores: list[int] = []
    rated_rules: list[tuple[str, str, int, str, str | None]] = []

    for rule in output.rules:
        score, reason, suggestion = rate_convention(rule)
        scores.append(score)
        rated_rules.append((rule.id, rule.title, score, reason, suggestion))

    avg_score = sum(scores) / len(scores) if scores else 0

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Conventions Reviewed:** {len(output.rules)}")
    lines.append(f"- **Average Score:** {avg_score:.1f}/5 ({get_score_label(round(avg_score))})")
    lines.append(f"- **Excellent (5):** {scores.count(5)}")
    lines.append(f"- **Good (4):** {scores.count(4)}")
    lines.append(f"- **Average (3):** {scores.count(3)}")
    lines.append(f"- **Below Average (2):** {scores.count(2)}")
    lines.append(f"- **Poor (1):** {scores.count(1)}")
    lines.append("")

    # Scores overview table
    lines.append("## Scores Overview")
    lines.append("")
    lines.append("| Convention | Score | Rating |")
    lines.append("|:-----------|:-----:|:-------|")

    for rule_id, title, score, reason, suggestion in sorted(rated_rules, key=lambda x: (-x[2], x[0])):
        rating_label = get_score_label(score)
        lines.append(f"| {title} | {score}/5 | {rating_label} |")

    lines.append("")

    # Detailed reviews
    lines.append("## Detailed Reviews")
    lines.append("")

    # Group by score for better organization
    for target_score in [5, 4, 3, 2, 1]:
        rules_with_score = [r for r in rated_rules if r[2] == target_score]
        if not rules_with_score:
            continue

        lines.append(f"### {get_score_label(target_score)} ({target_score}/5)")
        lines.append("")

        for rule_id, title, score, reason, suggestion in sorted(rules_with_score, key=lambda x: x[0]):
            lines.append(f"#### {title}")
            lines.append("")
            lines.append(f"**ID:** `{rule_id}`  ")
            lines.append(f"**Score:** {score}/5 ({get_score_label(score)})")
            lines.append("")
            lines.append(f"**Assessment:** {reason}")
            lines.append("")

            if suggestion:
                lines.append(f"**Suggestion:** {suggestion}")
                lines.append("")

            lines.append("---")
            lines.append("")

    # Improvement priorities section
    improvements_needed = [r for r in rated_rules if r[4] is not None]
    if improvements_needed:
        lines.append("## Improvement Priorities")
        lines.append("")
        lines.append("Conventions sorted by priority (lowest scores first):")
        lines.append("")

        for i, (rule_id, title, score, reason, suggestion) in enumerate(
            sorted(improvements_needed, key=lambda x: (x[2], x[0])), 1
        ):
            if suggestion:
                lines.append(f"{i}. **{title}** (Score: {score}/5)")
                lines.append(f"   - {suggestion}")
                lines.append("")

    return "\n".join(lines)


def write_review_report(output: ConventionsOutput, repo_path: Path) -> Path:
    """Write a review report to the .conventions directory."""
    conventions_dir = repo_path / ".conventions"
    conventions_dir.mkdir(exist_ok=True)

    report_path = conventions_dir / "conventions-review.md"
    report_content = generate_review_markdown(output)
    report_path.write_text(report_content)

    return report_path
