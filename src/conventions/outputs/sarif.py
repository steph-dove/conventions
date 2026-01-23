"""SARIF (Static Analysis Results Interchange Format) output for conventions detection.

SARIF is a standard format for static analysis tools, supported by GitHub Code Scanning.
See: https://sarifweb.azurewebsites.net/
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..ratings import get_score_label, rate_convention
from ..schemas import ConventionsOutput

SARIF_SCHEMA = "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json"
SARIF_VERSION = "2.1.0"
TOOL_NAME = "conventions-cli"
TOOL_VERSION = "1.0.0"
TOOL_INFO_URI = "https://github.com/conventions-cli/conventions-cli"


def _score_to_level(score: int) -> str:
    """Convert score (1-5) to SARIF level."""
    if score >= 4:
        return "note"  # Good practices, informational
    if score == 3:
        return "warning"  # Average, could be improved
    return "error"  # Below average or poor


def _score_to_kind(score: int) -> str:
    """Convert score to SARIF result kind."""
    if score >= 4:
        return "pass"  # Meets or exceeds expectations
    if score == 3:
        return "review"  # Needs review
    return "fail"  # Needs improvement


def generate_sarif_report(output: ConventionsOutput) -> dict[str, Any]:
    """Generate SARIF report from conventions output.

    Args:
        output: ConventionsOutput with detected conventions

    Returns:
        SARIF-formatted dictionary
    """
    # Build rules (one per convention type)
    rules: list[dict[str, Any]] = []
    rule_index_map: dict[str, int] = {}

    for idx, rule in enumerate(output.rules):
        score, reason, suggestion = rate_convention(rule)
        rule_index_map[rule.id] = idx

        sarif_rule: dict[str, Any] = {
            "id": rule.id,
            "name": rule.title,
            "shortDescription": {
                "text": rule.title,
            },
            "fullDescription": {
                "text": rule.description,
            },
            "helpUri": f"{TOOL_INFO_URI}#rules",
            "properties": {
                "category": rule.category,
                "language": rule.language or "generic",
                "score": score,
                "scoreLabel": get_score_label(score),
                "precision": "high" if rule.confidence >= 0.8 else "medium",
            },
        }

        # Add help text with suggestion if available
        help_text = f"Assessment: {reason}"
        if suggestion:
            help_text += f"\n\nSuggestion: {suggestion}"

        sarif_rule["help"] = {
            "text": help_text,
            "markdown": f"**Assessment:** {reason}\n\n" + (f"**Suggestion:** {suggestion}" if suggestion else ""),
        }

        # Default configuration based on score
        sarif_rule["defaultConfiguration"] = {
            "level": _score_to_level(score),
            "enabled": True,
        }

        rules.append(sarif_rule)

    # Build results (one per convention with location evidence)
    results: list[dict[str, Any]] = []

    for rule in output.rules:
        score, reason, suggestion = rate_convention(rule)
        rule_index = rule_index_map[rule.id]

        result: dict[str, Any] = {
            "ruleId": rule.id,
            "ruleIndex": rule_index,
            "level": _score_to_level(score),
            "kind": _score_to_kind(score),
            "message": {
                "text": f"{rule.title}: {reason}",
            },
            "properties": {
                "confidence": rule.confidence,
                "score": score,
                "scoreLabel": get_score_label(score),
                "stats": rule.stats,
            },
        }

        # Add suggestion as fix suggestion
        if suggestion:
            result["fixes"] = [{
                "description": {
                    "text": suggestion,
                },
                "changes": [],  # No automatic changes
            }]

        # Add locations from evidence
        locations = []
        for ev in rule.evidence:
            location: dict[str, Any] = {
                "physicalLocation": {
                    "artifactLocation": {
                        "uri": ev.file_path,
                        "uriBaseId": "%SRCROOT%",
                    },
                    "region": {
                        "startLine": ev.line_start,
                        "endLine": ev.line_end,
                        "snippet": {
                            "text": ev.excerpt,
                        },
                    },
                },
            }
            locations.append(location)

        if locations:
            result["locations"] = locations
        else:
            # If no specific evidence, create a placeholder location
            result["locations"] = [{
                "physicalLocation": {
                    "artifactLocation": {
                        "uri": ".",
                        "uriBaseId": "%SRCROOT%",
                    },
                },
            }]

        results.append(result)

    # Build the complete SARIF document
    sarif: dict[str, Any] = {
        "$schema": SARIF_SCHEMA,
        "version": SARIF_VERSION,
        "runs": [{
            "tool": {
                "driver": {
                    "name": TOOL_NAME,
                    "version": TOOL_VERSION,
                    "informationUri": TOOL_INFO_URI,
                    "rules": rules,
                    "properties": {
                        "supportedLanguages": ["python", "go", "node", "rust", "generic"],
                    },
                },
            },
            "results": results,
            "invocations": [{
                "executionSuccessful": True,
                "startTimeUtc": datetime.now(timezone.utc).isoformat(),
                "workingDirectory": {
                    "uri": output.metadata.path,
                },
            }],
            "originalUriBaseIds": {
                "%SRCROOT%": {
                    "uri": output.metadata.path + "/",
                },
            },
            "properties": {
                "conventionsVersion": output.version,
                "detectedLanguages": output.metadata.detected_languages,
                "totalFilesScanned": output.metadata.total_files_scanned,
            },
        }],
    }

    # Add warnings as notifications
    if output.warnings:
        notifications = []
        for warning in output.warnings:
            notifications.append({
                "descriptor": {
                    "id": f"warning/{warning.detector}",
                },
                "level": "warning",
                "message": {
                    "text": warning.message,
                },
                "properties": {
                    "detector": warning.detector,
                },
            })
        sarif["runs"][0]["invocations"][0]["toolExecutionNotifications"] = notifications

    return sarif


def write_sarif_report(output: ConventionsOutput, repo_root: Path) -> Path:
    """Write SARIF report to .conventions directory.

    Args:
        output: ConventionsOutput with detected conventions
        repo_root: Repository root path

    Returns:
        Path to the written SARIF file
    """
    conventions_dir = repo_root / ".conventions"
    conventions_dir.mkdir(exist_ok=True)

    report_path = conventions_dir / "conventions.sarif"
    sarif_data = generate_sarif_report(output)

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(sarif_data, f, indent=2)

    return report_path
