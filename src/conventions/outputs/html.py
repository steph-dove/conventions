"""HTML report generator for conventions detection."""

from __future__ import annotations

import html
from datetime import datetime
from pathlib import Path

from ..ratings import get_score_label, rate_convention
from ..schemas import ConventionsOutput


def _escape(text: str) -> str:
    """Escape HTML special characters."""
    return html.escape(str(text))


def _score_color(score: int) -> str:
    """Get color class for score."""
    colors = {
        1: "#dc3545",  # Red
        2: "#fd7e14",  # Orange
        3: "#ffc107",  # Yellow
        4: "#28a745",  # Green
        5: "#20c997",  # Teal
    }
    return colors.get(score, "#6c757d")


def _score_badge(score: int) -> str:
    """Generate score badge HTML."""
    color = _score_color(score)
    label = get_score_label(score)
    return f'<span class="badge" style="background-color: {color};">{score}/5 - {label}</span>'


def generate_html_report(output: ConventionsOutput) -> str:
    """Generate a self-contained HTML report."""
    # Calculate scores
    rated_rules = []
    scores = []
    for rule in output.rules:
        score, reason, suggestion = rate_convention(rule)
        scores.append(score)
        rated_rules.append((rule, score, reason, suggestion))

    avg_score = sum(scores) / len(scores) if scores else 0
    score_counts = {i: scores.count(i) for i in range(1, 6)}

    # Sort rules by score (lowest first for improvement priority)
    rated_rules_sorted = sorted(rated_rules, key=lambda x: (-x[1], x[0].id))

    # Generate HTML
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html_parts = [_html_header(timestamp, output.metadata.path)]

    # Summary section
    html_parts.append(_html_summary(output, avg_score, score_counts))

    # Rules table
    html_parts.append(_html_rules_table(rated_rules_sorted))

    # Detailed sections
    html_parts.append(_html_detailed_rules(rated_rules_sorted))

    # Footer and scripts
    html_parts.append(_html_footer())

    return "\n".join(html_parts)


def _html_header(timestamp: str, repo_path: str) -> str:
    """Generate HTML header with CSS."""
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Conventions Report - {_escape(repo_path)}</title>
    <style>
        :root {{
            --bg-primary: #ffffff;
            --bg-secondary: #f8f9fa;
            --text-primary: #212529;
            --text-secondary: #6c757d;
            --border-color: #dee2e6;
            --link-color: #0d6efd;
            --code-bg: #f1f3f5;
        }}

        [data-theme="dark"] {{
            --bg-primary: #1a1a2e;
            --bg-secondary: #16213e;
            --text-primary: #e4e4e4;
            --text-secondary: #a0a0a0;
            --border-color: #404040;
            --link-color: #6ea8fe;
            --code-bg: #2d2d44;
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: var(--text-primary);
            background-color: var(--bg-primary);
            margin: 0;
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }}

        h1, h2, h3 {{
            color: var(--text-primary);
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }}

        h1 {{
            border-bottom: 2px solid var(--border-color);
            padding-bottom: 10px;
        }}

        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        }}

        .meta {{
            color: var(--text-secondary);
            font-size: 0.9em;
        }}

        .theme-toggle {{
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            padding: 8px 16px;
            cursor: pointer;
            color: var(--text-primary);
        }}

        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}

        .card {{
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        }}

        .card-value {{
            font-size: 2em;
            font-weight: bold;
        }}

        .card-label {{
            color: var(--text-secondary);
            font-size: 0.85em;
        }}

        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            color: white;
            font-size: 0.85em;
            font-weight: 500;
        }}

        .filters {{
            display: flex;
            gap: 10px;
            margin: 20px 0;
            flex-wrap: wrap;
        }}

        .filters select, .filters input {{
            padding: 8px 12px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            background: var(--bg-primary);
            color: var(--text-primary);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}

        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }}

        th {{
            background: var(--bg-secondary);
            font-weight: 600;
            cursor: pointer;
        }}

        th:hover {{
            background: var(--border-color);
        }}

        tr:hover {{
            background: var(--bg-secondary);
        }}

        .rule-detail {{
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            margin: 20px 0;
            overflow: hidden;
        }}

        .rule-header {{
            padding: 15px 20px;
            background: var(--bg-primary);
            border-bottom: 1px solid var(--border-color);
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .rule-header:hover {{
            background: var(--bg-secondary);
        }}

        .rule-body {{
            padding: 20px;
            display: none;
        }}

        .rule-body.expanded {{
            display: block;
        }}

        .rule-meta {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            margin-bottom: 15px;
            color: var(--text-secondary);
            font-size: 0.9em;
        }}

        pre {{
            background: var(--code-bg);
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
            font-size: 0.85em;
        }}

        code {{
            font-family: 'SF Mono', 'Menlo', 'Monaco', 'Courier New', monospace;
        }}

        .suggestion {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 4px;
            padding: 12px;
            margin-top: 15px;
        }}

        [data-theme="dark"] .suggestion {{
            background: #332701;
            border-color: #664d03;
        }}

        .evidence {{
            margin-top: 15px;
        }}

        .evidence-item {{
            margin-bottom: 15px;
        }}

        .evidence-path {{
            color: var(--text-secondary);
            font-size: 0.85em;
            margin-bottom: 5px;
        }}

        .expand-icon {{
            transition: transform 0.2s;
        }}

        .expanded .expand-icon {{
            transform: rotate(90deg);
        }}

        @media (max-width: 768px) {{
            .filters {{
                flex-direction: column;
            }}

            .rule-meta {{
                flex-direction: column;
                gap: 5px;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>Conventions Report</h1>
            <p class="meta">Generated: {timestamp} | Repository: <code>{_escape(repo_path)}</code></p>
        </div>
        <button class="theme-toggle" onclick="toggleTheme()">Toggle Dark Mode</button>
    </div>
'''


def _html_summary(output: ConventionsOutput, avg_score: float, score_counts: dict) -> str:
    """Generate summary section."""
    languages = ", ".join(output.metadata.detected_languages) or "None"

    return f'''
    <section id="summary">
        <h2>Summary</h2>
        <div class="summary-cards">
            <div class="card">
                <div class="card-value">{len(output.rules)}</div>
                <div class="card-label">Conventions Detected</div>
            </div>
            <div class="card">
                <div class="card-value">{avg_score:.1f}</div>
                <div class="card-label">Average Score</div>
            </div>
            <div class="card">
                <div class="card-value">{output.metadata.total_files_scanned}</div>
                <div class="card-label">Files Scanned</div>
            </div>
            <div class="card">
                <div class="card-value" style="font-size: 1.2em;">{_escape(languages)}</div>
                <div class="card-label">Languages</div>
            </div>
        </div>
        <div class="summary-cards">
            <div class="card">
                <div class="card-value" style="color: #20c997;">{score_counts.get(5, 0)}</div>
                <div class="card-label">Excellent (5)</div>
            </div>
            <div class="card">
                <div class="card-value" style="color: #28a745;">{score_counts.get(4, 0)}</div>
                <div class="card-label">Good (4)</div>
            </div>
            <div class="card">
                <div class="card-value" style="color: #ffc107;">{score_counts.get(3, 0)}</div>
                <div class="card-label">Average (3)</div>
            </div>
            <div class="card">
                <div class="card-value" style="color: #fd7e14;">{score_counts.get(2, 0)}</div>
                <div class="card-label">Below Avg (2)</div>
            </div>
            <div class="card">
                <div class="card-value" style="color: #dc3545;">{score_counts.get(1, 0)}</div>
                <div class="card-label">Poor (1)</div>
            </div>
        </div>
    </section>
'''


def _html_rules_table(rated_rules: list) -> str:
    """Generate rules overview table."""
    rows = []
    for rule, score, reason, _ in rated_rules:
        lang = rule.language or "generic"
        docs_cell = f'<a href="{_escape(rule.docs_url)}" target="_blank" rel="noopener">docs</a>' if rule.docs_url else ""
        rows.append(f'''
            <tr data-language="{_escape(lang)}" data-category="{_escape(rule.category)}" data-score="{score}">
                <td><code>{_escape(rule.id)}</code></td>
                <td>{_escape(rule.title)}</td>
                <td>{_escape(lang)}</td>
                <td>{_escape(rule.category)}</td>
                <td>{_score_badge(score)}</td>
                <td>{rule.confidence * 100:.0f}%</td>
                <td>{docs_cell}</td>
            </tr>
        ''')

    return f'''
    <section id="overview">
        <h2>Conventions Overview</h2>

        <div class="filters">
            <select id="filter-language" onchange="filterTable()">
                <option value="">All Languages</option>
                <option value="python">Python</option>
                <option value="go">Go</option>
                <option value="node">Node.js</option>
                <option value="rust">Rust</option>
                <option value="generic">Generic</option>
            </select>
            <select id="filter-score" onchange="filterTable()">
                <option value="">All Scores</option>
                <option value="5">Excellent (5)</option>
                <option value="4">Good (4)</option>
                <option value="3">Average (3)</option>
                <option value="2">Below Average (2)</option>
                <option value="1">Poor (1)</option>
            </select>
            <input type="text" id="filter-search" placeholder="Search..." oninput="filterTable()">
        </div>

        <table id="rules-table">
            <thead>
                <tr>
                    <th onclick="sortTable(0)">ID</th>
                    <th onclick="sortTable(1)">Title</th>
                    <th onclick="sortTable(2)">Language</th>
                    <th onclick="sortTable(3)">Category</th>
                    <th onclick="sortTable(4)">Score</th>
                    <th onclick="sortTable(5)">Confidence</th>
                    <th>Docs</th>
                </tr>
            </thead>
            <tbody>
                {"".join(rows)}
            </tbody>
        </table>
    </section>
'''


def _html_detailed_rules(rated_rules: list) -> str:
    """Generate detailed rules sections."""
    details = []
    for rule, score, reason, suggestion in rated_rules:
        evidence_html = ""
        if rule.evidence:
            evidence_items = []
            for ev in rule.evidence[:5]:
                evidence_items.append(f'''
                    <div class="evidence-item">
                        <div class="evidence-path">{_escape(ev.file_path)}:{ev.line_start}-{ev.line_end}</div>
                        <pre><code>{_escape(ev.excerpt)}</code></pre>
                    </div>
                ''')
            evidence_html = f'''
                <div class="evidence">
                    <strong>Evidence:</strong>
                    {"".join(evidence_items)}
                </div>
            '''

        suggestion_html = ""
        if suggestion:
            suggestion_html = f'''
                <div class="suggestion">
                    <strong>Suggestion:</strong> {_escape(suggestion)}
                </div>
            '''

        stats_html = ""
        if rule.stats:
            stats_items = [f"<li><code>{_escape(k)}</code>: {_escape(str(v))}</li>" for k, v in rule.stats.items()]
            stats_html = f'''
                <div>
                    <strong>Statistics:</strong>
                    <ul>{"".join(stats_items)}</ul>
                </div>
            '''

        docs_html = ""
        if rule.docs_url:
            docs_html = f'<span><strong>Docs:</strong> <a href="{_escape(rule.docs_url)}" target="_blank" rel="noopener">{_escape(rule.docs_url)}</a></span>'

        details.append(f'''
            <div class="rule-detail" id="rule-{_escape(rule.id.replace('.', '-'))}">
                <div class="rule-header" onclick="toggleRule(this)">
                    <div>
                        <strong>{_escape(rule.title)}</strong>
                        <span class="meta" style="margin-left: 10px;"><code>{_escape(rule.id)}</code></span>
                    </div>
                    <div>
                        {_score_badge(score)}
                        <span class="expand-icon">&#9654;</span>
                    </div>
                </div>
                <div class="rule-body">
                    <div class="rule-meta">
                        <span><strong>Category:</strong> {_escape(rule.category)}</span>
                        <span><strong>Language:</strong> {_escape(rule.language or 'generic')}</span>
                        <span><strong>Confidence:</strong> {rule.confidence * 100:.0f}%</span>
                        {docs_html}
                    </div>
                    <p>{_escape(rule.description)}</p>
                    <p><strong>Assessment:</strong> {_escape(reason)}</p>
                    {suggestion_html}
                    {stats_html}
                    {evidence_html}
                </div>
            </div>
        ''')

    return f'''
    <section id="details">
        <h2>Detailed Analysis</h2>
        {"".join(details)}
    </section>
'''


def _html_footer() -> str:
    """Generate HTML footer with JavaScript."""
    return '''
    <footer style="margin-top: 40px; padding: 20px 0; border-top: 1px solid var(--border-color); color: var(--text-secondary); text-align: center;">
        <p>Generated by <strong>conventions-cli</strong></p>
    </footer>

    <script>
        // Theme toggle
        function toggleTheme() {
            const body = document.body;
            if (body.getAttribute('data-theme') === 'dark') {
                body.removeAttribute('data-theme');
                localStorage.setItem('theme', 'light');
            } else {
                body.setAttribute('data-theme', 'dark');
                localStorage.setItem('theme', 'dark');
            }
        }

        // Load saved theme
        if (localStorage.getItem('theme') === 'dark') {
            document.body.setAttribute('data-theme', 'dark');
        }

        // Toggle rule details
        function toggleRule(header) {
            const body = header.nextElementSibling;
            body.classList.toggle('expanded');
            header.classList.toggle('expanded');
        }

        // Filter table
        function filterTable() {
            const language = document.getElementById('filter-language').value.toLowerCase();
            const score = document.getElementById('filter-score').value;
            const search = document.getElementById('filter-search').value.toLowerCase();

            const rows = document.querySelectorAll('#rules-table tbody tr');
            rows.forEach(row => {
                const rowLang = row.getAttribute('data-language').toLowerCase();
                const rowScore = row.getAttribute('data-score');
                const rowText = row.textContent.toLowerCase();

                const matchLang = !language || rowLang === language;
                const matchScore = !score || rowScore === score;
                const matchSearch = !search || rowText.includes(search);

                row.style.display = (matchLang && matchScore && matchSearch) ? '' : 'none';
            });
        }

        // Sort table
        let sortDirection = {};
        function sortTable(columnIndex) {
            const table = document.getElementById('rules-table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));

            sortDirection[columnIndex] = !sortDirection[columnIndex];
            const direction = sortDirection[columnIndex] ? 1 : -1;

            rows.sort((a, b) => {
                let aVal = a.children[columnIndex].textContent.trim();
                let bVal = b.children[columnIndex].textContent.trim();

                // Handle numeric sorting for score and confidence
                if (columnIndex === 4) {
                    aVal = parseInt(aVal) || 0;
                    bVal = parseInt(bVal) || 0;
                    return (aVal - bVal) * direction;
                }
                if (columnIndex === 5) {
                    aVal = parseFloat(aVal) || 0;
                    bVal = parseFloat(bVal) || 0;
                    return (aVal - bVal) * direction;
                }

                return aVal.localeCompare(bVal) * direction;
            });

            rows.forEach(row => tbody.appendChild(row));
        }
    </script>
</body>
</html>
'''


def write_html_report(output: ConventionsOutput, repo_root: Path) -> Path:
    """Write HTML report to .conventions directory."""
    conventions_dir = repo_root / ".conventions"
    conventions_dir.mkdir(exist_ok=True)

    report_path = conventions_dir / "conventions.html"
    report_content = generate_html_report(output)
    report_path.write_text(report_content, encoding="utf-8")

    return report_path
