#!/usr/bin/env python3
"""
Render social media images from HTML templates using Chrome headless.

Usage:
    python render_social_image.py --template social-image.html --output image.png --vars vars.json

Why HTML + Chrome Headless?
- Familiar web tech, full CSS support (Inter font, gradients, flexbox)
- Templates preview in browser before generating
- ~1s render time is acceptable for this use case

Alternatives considered:
- Pillow: Complex layouts painful, no CSS
- Satori/Vercel OG: Limited CSS subset
- Cairo: Lower-level API
- Figma API: External dependency, costs
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def fill_template(template_path: str, variables: dict) -> str:
    """Fill template variables using {{variable}} syntax."""
    with open(template_path, "r") as f:
        content = f.read()

    # Replace {{var}} and {{var|default:value}} patterns
    def replace_var(match):
        var_expr = match.group(1)
        if "|default:" in var_expr:
            var_name, default = var_expr.split("|default:")
            return str(variables.get(var_name.strip(), default))
        return str(variables.get(var_expr.strip(), match.group(0)))

    return re.sub(r"\{\{([^}]+)\}\}", replace_var, content)


def render_image(html_path: str, output_path: str, width: int = 1200, height: int = 630) -> bool:
    """Render HTML to PNG using Chrome headless."""
    chrome_paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser",
        "google-chrome",
    ]

    chrome_path = None
    for path in chrome_paths:
        if os.path.exists(path) or subprocess.run(
            ["which", path], capture_output=True
        ).returncode == 0:
            chrome_path = path
            break

    if not chrome_path:
        print("Error: Chrome not found", file=sys.stderr)
        return False

    cmd = [
        chrome_path,
        "--headless",
        "--disable-gpu",
        f"--screenshot={output_path}",
        f"--window-size={width},{height}",
        "--hide-scrollbars",
        f"file://{os.path.abspath(html_path)}",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0 and os.path.exists(output_path)


def main():
    parser = argparse.ArgumentParser(description="Render social images from HTML templates")
    parser.add_argument("--template", required=True, help="Path to HTML template")
    parser.add_argument("--output", required=True, help="Output PNG path")
    parser.add_argument("--vars", help="JSON file with template variables")
    parser.add_argument("--var", action="append", help="Variable in key=value format")
    parser.add_argument("--width", type=int, default=1200, help="Image width")
    parser.add_argument("--height", type=int, default=630, help="Image height")
    args = parser.parse_args()

    # Load variables
    variables = {}
    if args.vars:
        with open(args.vars) as f:
            variables = json.load(f)
    if args.var:
        for v in args.var:
            key, value = v.split("=", 1)
            variables[key] = value

    # Fill template
    filled_html = fill_template(args.template, variables)

    # Write to temp file and render
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        f.write(filled_html)
        temp_path = f.name

    try:
        success = render_image(temp_path, args.output, args.width, args.height)
        if success:
            print(f"Generated: {args.output}")
        else:
            print("Failed to generate image", file=sys.stderr)
            sys.exit(1)
    finally:
        os.unlink(temp_path)


if __name__ == "__main__":
    main()
