"""
Builder agent tools — agent-specific utilities.

LeftClaw and BGIPFS tools are provided by the shared dead-simple-agent library.
"""

import urllib.request
import subprocess


# ---------------------------------------------------------------------------
# Fetch / inspection tools
# ---------------------------------------------------------------------------

def _run_deep_fetch(args):
    """Fetch a URL with a larger response limit (16k chars) for reading codebases and skill docs."""
    try:
        import re
        import time
        time.sleep(1)
        url = args["url"]
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 builder-agent/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        if args.get("raw", False):
            return raw[:16000]
        raw = re.sub(r"<script[^>]*>.*?</script>", "", raw, flags=re.DOTALL)
        raw = re.sub(r"<style[^>]*>.*?</style>", "", raw, flags=re.DOTALL)
        raw = re.sub(r"<[^>]+>", " ", raw)
        raw = re.sub(r"\s+", " ", raw).strip()
        return raw[:16000] + ("..." if len(raw) > 16000 else "")
    except Exception as e:
        return f"ERROR: {e}"


def _run_source_grep(args):
    """Run grep -rn on a directory to find code patterns."""
    try:
        pattern = args["pattern"]
        path = args.get("path", ".")
        exclude = args.get("exclude", "node_modules,.next,out,.git,dist,build")
        exclude_args = []
        for d in exclude.split(","):
            d = d.strip()
            if d:
                exclude_args.extend(["--exclude-dir", d])
        cmd = ["grep", "-rn", "--include=*.ts", "--include=*.tsx",
               "--include=*.js", "--include=*.jsx", "--include=*.css",
               "--include=*.json", "--include=*.sol", "--include=*.html",
               "--include=*.md"] + exclude_args + [pattern, path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        output = result.stdout.strip()
        if not output:
            return f"No matches for pattern: {pattern}"
        return output[:8000] + ("..." if len(output) > 8000 else "")
    except subprocess.TimeoutExpired:
        return "ERROR: grep timed out after 15s"
    except Exception as e:
        return f"ERROR: {e}"


# ---------------------------------------------------------------------------
# Tool registry (agent-specific only)
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "spec": {"type": "function", "function": {
            "name": "deep_fetch",
            "description": "Fetch a URL with a 16k char limit. Use for reading skill docs, source files, READMEs, contract code, and API responses.",
            "parameters": {"type": "object", "properties": {
                "url": {"type": "string", "description": "The URL to fetch"},
                "raw": {"type": "boolean", "description": "Return raw response without HTML stripping (default: false). Use for JSON APIs."},
            }, "required": ["url"]},
        }},
        "run": _run_deep_fetch,
    },
    {
        "spec": {"type": "function", "function": {
            "name": "source_grep",
            "description": "Search source code for patterns using grep -rn. Returns matching lines with file paths and line numbers. Searches .ts/.tsx/.js/.jsx/.css/.json/.sol/.html/.md files, excludes node_modules/.next/out/.git by default.",
            "parameters": {"type": "object", "properties": {
                "pattern": {"type": "string", "description": "The grep pattern to search for (basic regex)"},
                "path": {"type": "string", "description": "Directory to search in (default: current directory)"},
                "exclude": {"type": "string", "description": "Comma-separated directory names to exclude (default: node_modules,.next,out,.git,dist,build)"},
            }, "required": ["pattern"]},
        }},
        "run": _run_source_grep,
    },
]
