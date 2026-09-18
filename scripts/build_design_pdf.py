"""Regenerate DESIGN.pdf from DESIGN.md.

Converts the markdown to a styled HTML file (rendering ```mermaid``` blocks
via mermaid.js), then leaves the HTML for a headless browser to print to
PDF. Run this after editing DESIGN.md; see the accompanying README section
"Regenerating DESIGN.pdf" for the full two-step command.

Requires: pip install markdown
"""
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "DESIGN.md"
HTML_OUT = ROOT / "DESIGN.html"

text = SRC.read_text(encoding="utf-8")

# Pull out ```mermaid ... ``` blocks and replace with <div class="mermaid">
# so mermaid.js can find and render them in the browser.
mermaid_blocks = []

def stash_mermaid(match):
    mermaid_blocks.append(match.group(1))
    return f"@@MERMAID{len(mermaid_blocks) - 1}@@"

text = re.sub(r"```mermaid\n(.*?)```", stash_mermaid, text, flags=re.DOTALL)

body = markdown.markdown(text, extensions=["extra", "tables", "fenced_code", "sane_lists"])

for i, diagram in enumerate(mermaid_blocks):
    body = body.replace(
        f"<p>@@MERMAID{i}@@</p>",
        f'<div class="mermaid">{diagram}</div>',
    )

html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>AI Multi-Agent Sports Trade Analyzer -- Design Document</title>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<style>
  @page {{ size: A4; margin: 22mm 18mm; }}
  body {{
    font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
    color: #1a1a1a;
    line-height: 1.55;
    font-size: 11.5pt;
    max-width: 780px;
    margin: 0 auto;
  }}
  h1 {{ font-size: 22pt; border-bottom: 3px solid #2c3e50; padding-bottom: 8px; margin-top: 0; }}
  h2 {{ font-size: 16pt; border-bottom: 1px solid #ccc; padding-bottom: 4px; margin-top: 34px; color: #2c3e50; page-break-after: avoid; }}
  h3 {{ font-size: 13pt; margin-top: 22px; color: #34495e; page-break-after: avoid; }}
  code {{ background: #f4f4f4; padding: 1px 5px; border-radius: 3px; font-family: "SFMono-Regular", Consolas, monospace; font-size: 10pt; }}
  pre {{ background: #f6f8fa; border: 1px solid #e1e4e8; border-radius: 6px; padding: 12px 14px; overflow-x: auto; page-break-inside: avoid; }}
  pre code {{ background: none; padding: 0; }}
  table {{ border-collapse: collapse; width: 100%; margin: 14px 0; font-size: 10.5pt; page-break-inside: avoid; }}
  th, td {{ border: 1px solid #ddd; padding: 6px 10px; text-align: left; vertical-align: top; }}
  th {{ background: #2c3e50; color: white; }}
  tr:nth-child(even) {{ background: #f8f9fa; }}
  .mermaid {{ text-align: center; margin: 20px 0; page-break-inside: avoid; }}
  blockquote {{ border-left: 4px solid #ccc; margin: 12px 0; padding: 2px 16px; color: #555; background: #fafafa; }}
  hr {{ border: none; border-top: 1px solid #ddd; margin: 28px 0; }}
</style>
</head>
<body>
{body}
<script>
  mermaid.initialize({{ startOnLoad: true, theme: "neutral" }});
</script>
</body>
</html>
"""

HTML_OUT.write_text(html, encoding="utf-8")
print("Wrote", HTML_OUT)
