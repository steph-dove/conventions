# Copyright © 2026 Dovatech LLC
# SPDX-License-Identifier: AGPL-3.0-or-later


"""CLI for conventions detection."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from .config import ConventionsConfig, load_config

app = typer.Typer(
    name="conventions",
    help="Discover coding conventions from source code.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def discover(
    repo: Path = typer.Option(
        ".",
        "-r", "--repo",
        help="Path to repository root",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    languages: Optional[str] = typer.Option(
        None,
        "-l", "--languages",
        help="Comma-separated languages to analyze (python,go,node). Auto-detect if not specified.",
    ),
    max_files: Optional[int] = typer.Option(
        None,
        "--max-files",
        help="Maximum files to scan per language (default: 2000)",
    ),
    verbose: bool = typer.Option(
        False,
        "-v", "--verbose",
        help="Show detailed progress",
    ),
    detailed: bool = typer.Option(
        False,
        "-d", "--detailed",
        help="Show detailed rule output",
    ),
    quiet: bool = typer.Option(
        False,
        "-q", "--quiet",
        help="Suppress console output, only write files",
    ),
    config: Optional[Path] = typer.Option(
        None,
        "-c", "--config",
        help="Path to configuration file",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    ignore_config: bool = typer.Option(
        False,
        "--ignore-config",
        help="Ignore configuration file even if present",
    ),
    output_format: Optional[str] = typer.Option(
        None,
        "--format",
        help="Output format(s), comma-separated (json,markdown,review,html,sarif,claude)",
    ),
    claude: bool = typer.Option(
        False,
        "--claude",
        help="Generate CLAUDE.md for Claude Code (writes to .claude/ directory)",
    ),
    init: bool = typer.Option(
        False,
        "--init",
        help="Enrich CLAUDE.md using Claude Code CLI (requires claude CLI installed)",
    ),
) -> None:
    """
    Discover coding conventions from a repository.

    Scans source code and writes detected conventions to
    .conventions/conventions.raw.json and .conventions/conventions.md
    """
    from .detectors.orchestrator import run_detectors, write_conventions_output
    from .ratings import rate_convention
    from .report import (
        print_detailed_rules,
        print_summary,
        write_markdown_report,
        write_review_report,
    )

    # Load configuration
    cfg = ConventionsConfig()
    if not ignore_config:
        try:
            cfg = load_config(repo, config)
            if verbose and (config or (repo / ".conventionsrc.json").exists()):
                console.print("[dim]Loaded configuration file[/dim]")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load config: {e}[/yellow]")

    # CLI options override config
    if languages:
        lang_set: set[str] | None = {lang.strip().lower() for lang in languages.split(",")}
    elif cfg.languages:
        lang_set = set(cfg.languages)
    else:
        lang_set = None

    if lang_set:
        valid_langs = {"python", "go", "node", "rust"}
        invalid = lang_set - valid_langs
        if invalid:
            console.print(f"[red]Invalid languages: {', '.join(invalid)}[/red]")
            console.print(f"Valid options: {', '.join(valid_langs)}")
            raise typer.Exit(1)

    # Use CLI max_files if provided, otherwise config value
    effective_max_files = max_files if max_files is not None else cfg.max_files

    # --init implies claude format
    if init and not claude and (not output_format or "claude" not in output_format):
        claude = True

    # Determine output formats
    if output_format:
        formats = {f.strip().lower() for f in output_format.split(",")}
    elif claude:
        # --claude without explicit --format: only write CLAUDE.md
        formats: set[str] = set()
    else:
        formats = set(cfg.output_formats)

    if not quiet:
        console.print(f"\n[bold blue]Scanning repository:[/bold blue] {repo}")

    # Run scan with config
    try:
        output = run_detectors(
            repo_root=repo,
            languages=lang_set,
            max_files=effective_max_files,
            progress_callback=console.print if verbose else None,
            disabled_detectors=set(cfg.disabled_detectors),
            disabled_rules=set(cfg.disabled_rules),
            exclude_patterns=cfg.exclude_patterns,
            plugin_paths=cfg.plugin_paths,
        )
    except Exception as e:
        console.print(f"[red]Error during scan: {e}[/red]")
        raise typer.Exit(1)

    # Write outputs based on format configuration
    if "json" in formats:
        try:
            output_path = write_conventions_output(output, repo)
            if not quiet:
                console.print(f"[green]Wrote conventions to:[/green] {output_path}")
        except Exception as e:
            console.print(f"[red]Error writing output: {e}[/red]")
            raise typer.Exit(1)

    if "markdown" in formats:
        try:
            markdown_path = write_markdown_report(output, repo)
            if not quiet:
                console.print(f"[green]Wrote markdown report to:[/green] {markdown_path}")
        except Exception as e:
            console.print(f"[red]Error writing markdown report: {e}[/red]")
            raise typer.Exit(1)

    if "review" in formats:
        try:
            review_path = write_review_report(output, repo)
            if not quiet:
                console.print(f"[green]Wrote review report to:[/green] {review_path}")
        except Exception as e:
            console.print(f"[red]Error writing review report: {e}[/red]")
            raise typer.Exit(1)

    if "html" in formats:
        try:
            from .outputs.html import write_html_report
            html_path = write_html_report(output, repo)
            if not quiet:
                console.print(f"[green]Wrote HTML report to:[/green] {html_path}")
        except ImportError:
            console.print("[yellow]HTML output not available[/yellow]")
        except Exception as e:
            console.print(f"[red]Error writing HTML report: {e}[/red]")
            raise typer.Exit(1)

    if "sarif" in formats:
        try:
            from .outputs.sarif import write_sarif_report
            sarif_path = write_sarif_report(output, repo)
            if not quiet:
                console.print(f"[green]Wrote SARIF report to:[/green] {sarif_path}")
        except ImportError:
            console.print("[yellow]SARIF output not available[/yellow]")
        except Exception as e:
            console.print(f"[red]Error writing SARIF report: {e}[/red]")
            raise typer.Exit(1)

    if "claude" in formats or claude:
        try:
            from .outputs.claude import write_claude_md
            claude_path = write_claude_md(output, repo, personal=claude)
            if not quiet:
                console.print(f"[green]Wrote CLAUDE.md to:[/green] {claude_path}")
        except Exception as e:
            console.print(f"[red]Error writing CLAUDE.md: {e}[/red]")
            raise typer.Exit(1)

        if init:
            try:
                from .outputs.claude import enrich_with_claude
                if not quiet:
                    console.print("[blue]Enriching CLAUDE.md with Claude Code...[/blue]")
                enrich_with_claude(claude_path, repo)
                if not quiet:
                    console.print(f"[green]Enriched CLAUDE.md at:[/green] {claude_path}")
            except Exception as e:
                if not quiet:
                    console.print(
                        f"[yellow]Warning: Could not enrich CLAUDE.md: {e}[/yellow]"
                    )

    # Print summary
    if not quiet:
        if detailed:
            print_detailed_rules(output, console)
        else:
            print_summary(output, console)

        # Exit with warning code if there were warnings
        if output.warnings:
            console.print(
                f"\n[yellow]Completed with {len(output.warnings)} warning(s)[/yellow]"
            )

    # Check min_score threshold
    if cfg.min_score is not None and output.rules:
        scores = [rate_convention(rule)[0] for rule in output.rules]
        avg_score = sum(scores) / len(scores)
        if avg_score < cfg.min_score:
            if not quiet:
                console.print(
                    f"\n[red]Average score {avg_score:.2f} is below minimum threshold {cfg.min_score}[/red]"
                )
            raise typer.Exit(2)


@app.command()
def show(
    repo: Path = typer.Option(
        ".",
        "-r", "--repo",
        help="Path to repository root",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    detailed: bool = typer.Option(
        False,
        "-d", "--detailed",
        help="Show detailed rule output",
    ),
) -> None:
    """
    Show previously detected conventions from .conventions/conventions.raw.json
    """
    import json

    from .report import print_detailed_rules, print_summary
    from .schemas import ConventionsOutput

    conventions_file = repo / ".conventions" / "conventions.raw.json"

    if not conventions_file.exists():
        console.print("[red]No conventions file found. Run 'discover' first.[/red]")
        raise typer.Exit(1)

    try:
        with open(conventions_file) as f:
            data = json.load(f)
        output = ConventionsOutput.model_validate(data)
    except Exception as e:
        console.print(f"[red]Error reading conventions file: {e}[/red]")
        raise typer.Exit(1)

    if detailed:
        print_detailed_rules(output, console)
    else:
        print_summary(output, console)


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
