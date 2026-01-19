"""CLI for conventions detection."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

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
    max_files: int = typer.Option(
        2000,
        "--max-files",
        help="Maximum files to scan per language",
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
) -> None:
    """
    Discover coding conventions from a repository.

    Scans source code and writes detected conventions to
    .conventions/conventions.raw.json and .conventions/conventions.md
    """
    from .detectors.orchestrator import write_conventions_output
    from .report import print_detailed_rules, print_summary, write_markdown_report
    from .scan import scan_repository

    # Parse languages
    lang_set: Optional[set[str]] = None
    if languages:
        lang_set = {lang.strip().lower() for lang in languages.split(",")}
        valid_langs = {"python", "go", "node"}
        invalid = lang_set - valid_langs
        if invalid:
            console.print(f"[red]Invalid languages: {', '.join(invalid)}[/red]")
            console.print(f"Valid options: {', '.join(valid_langs)}")
            raise typer.Exit(1)

    if not quiet:
        console.print(f"\n[bold blue]Scanning repository:[/bold blue] {repo}")

    # Run scan
    try:
        output = scan_repository(
            repo_path=repo,
            languages=lang_set,
            max_files=max_files,
            verbose=verbose,
        )
    except Exception as e:
        console.print(f"[red]Error during scan: {e}[/red]")
        raise typer.Exit(1)

    # Write output
    try:
        output_path = write_conventions_output(output, repo)
        if not quiet:
            console.print(f"[green]Wrote conventions to:[/green] {output_path}")
    except Exception as e:
        console.print(f"[red]Error writing output: {e}[/red]")
        raise typer.Exit(1)

    # Write markdown report
    try:
        markdown_path = write_markdown_report(output, repo)
        if not quiet:
            console.print(f"[green]Wrote markdown report to:[/green] {markdown_path}")
    except Exception as e:
        console.print(f"[red]Error writing markdown report: {e}[/red]")
        raise typer.Exit(1)

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
