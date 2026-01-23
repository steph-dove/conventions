"""Output format generators for conventions reports."""

from .html import generate_html_report, write_html_report
from .sarif import generate_sarif_report, write_sarif_report

__all__ = [
    "generate_html_report",
    "write_html_report",
    "generate_sarif_report",
    "write_sarif_report",
]
