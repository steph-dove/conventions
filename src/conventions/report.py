"""Report generation for conventions detection."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

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
