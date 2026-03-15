#!/usr/bin/env python3
import os
import json
import argparse

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Genome Time Machine - Story Export</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #0f111a;
            color: #f8fafc;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
        }}
        h1 {{ text-align: center; margin-bottom: 40px; }}
        .chapter {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        h2 {{ color: #a5b4fc; margin-top: 0; }}
        .disclaimer {{
            font-size: 0.8em;
            color: #94a3b8;
            border-top: 1px solid #334155;
            padding-top: 20px;
            margin-top: 40px;
        }}
        .inference-stats {{
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }}
        .stat-box {{
            flex: 1;
            background: rgba(0, 0, 0, 0.2);
            padding: 16px;
            border-radius: 8px;
            text-align: center;
        }}
        .warn {{ color: #fbbf24; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Your Genetic Journey</h1>
        
        {warnings_html}

        <div class="inference-stats">
            {stats_html}
        </div>

        <div id="story-content">
            {chapters_html}
        </div>

        <div class="disclaimer">
            <strong>Scientific Note:</strong>
            <ul>
                {disclaimers_html}
            </ul>
        </div>
    </div>
</body>
</html>
"""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", required=True)
    parser.add_argument("--out-html", required=True)
    args = parser.parse_args()
    
    with open(args.json, 'r') as f:
        data = json.load(f)
        
    inf = data.get("inference", {})
    story = data.get("story", {})
    
    warnings_html = ""
    for w in inf.get("warnings", []):
        warnings_html += f"<p class='warn'>⚠️ {w}</p>"
        
    stats_html = ""
    if inf.get("top_regions"):
        top_r = inf["top_regions"][0]["name"]
        stats_html += f"<div class='stat-box'><h3>Top Match</h3><p>{top_r}</p></div>"
        
    if inf.get("top_populations"):
        top_p = inf["top_populations"][0]["name"]
        stats_html += f"<div class='stat-box'><h3>Population</h3><p>{top_p}</p></div>"
        
    chapters_html = ""
    for ch in story.get("chapters", []):
        chapters_html += f"<div class='chapter'><h2>{ch['title']}</h2><p>{ch['text']}</p></div>"
        
    disclaimers_html = ""
    for d in story.get("disclaimers", []):
        disclaimers_html += f"<li>{d}</li>"
        
    html = HTML_TEMPLATE.format(
        warnings_html=warnings_html,
        stats_html=stats_html,
        chapters_html=chapters_html,
        disclaimers_html=disclaimers_html
    )
    
    os.makedirs(os.path.dirname(args.out_html), exist_ok=True)
    with open(args.out_html, 'w') as f:
        f.write(html)
        
    print(f"Exported HTML to {args.out_html}")

if __name__ == "__main__":
    main()
