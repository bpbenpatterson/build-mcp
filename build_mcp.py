"""MCP server that runs a build tool and returns structured compiler errors.

The point is not to run the build. The point is to parse the build's noisy
output into clean, structured diagnostics so an LLM agent can act on them
without burning its context window on log spam.

Run standalone for a smoke test:
    python build_mcp.py --selftest
Run as an MCP server (used by opencode):
    python build_mcp.py
"""

from __future__ import annotations

import os
import re
import subprocess
import sys

try:
    from mcp.server.mcpserver import MCPServer
except ImportError:  # mcp < 2.0
    from mcp.server.fastmcp import FastMCP as MCPServer

BUILD_CMD = os.environ.get(
    "BUILD_CMD",
    f"{sys.executable} {os.path.join(os.path.dirname(__file__), 'fake_junkbuild.py')}",
)
DEFAULT_TIMEOUT_S = int(os.environ.get("BUILD_TIMEOUT_S", "300"))

ERROR_RE = re.compile(
    r"^(?P<file>[^\s:][^:]*):(?P<line>\d+):(?:\d+:)?\s*"
    r"(?P<severity>error|warning|fatal error):\s*(?P<msg>.*)$",
    re.MULTILINE,
)
SUMMARY_RE = re.compile(r"Build (?:FAILED|SUCCEEDED).*", re.IGNORECASE)

mcp = MCPServer("build-tools")


def parse_diagnostics(text: str) -> list[dict]:
    """Turn raw build output into structured diagnostics."""
    out: list[dict] = []
    for m in ERROR_RE.finditer(text):
        out.append(
            {
                "file": m.group("file"),
                "line": int(m.group("line")),
                "severity": m.group("severity"),
                "message": m.group("msg").strip(),
            }
        )
    return out


def run_build(target: str, timeout_s: int) -> dict:
    cmd = BUILD_CMD.split() + (["--target", target] if target else [])
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout_s
        )
    except subprocess.TimeoutExpired:
        return {
            "exit_code": None,
            "timed_out": True,
            "errors": [],
            "warnings": [],
            "summary": f"build timed out after {timeout_s}s",
            "raw_tail": "",
        }

    combined = proc.stdout + "\n" + proc.stderr
    diags = parse_diagnostics(combined)
    errors = [d for d in diags if "error" in d["severity"]]
    warnings = [d for d in diags if d["severity"] == "warning"]
    summary_match = SUMMARY_RE.search(combined)

    return {
        "exit_code": proc.returncode,
        "timed_out": False,
        "errors": errors,
        "error_count": len(errors),
        "warnings": warnings,
        "warning_count": len(warnings),
        "summary": summary_match.group(0) if summary_match else "",
        "raw_tail": combined[-2000:],
    }


@mcp.tool()
def build(target: str = "all", timeout_s: int = DEFAULT_TIMEOUT_S) -> dict:
    """Run the project build and return structured compiler errors.

    Args:
        target: build target name (default "all").
        timeout_s: abort the build after this many seconds.

    Returns a dict with exit_code, errors (file/line/severity/message),
    warning counts, a summary line, and the raw tail of the log.
    """
    return run_build(target, timeout_s)


@mcp.tool()
def clean(target: str = "all") -> dict:
    """Run the project clean. Read-only with respect to source; safe to call."""
    cmd = BUILD_CMD.split() + ["--clean", "--target", target]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return {"exit_code": proc.returncode, "output": proc.stdout[-500:]}


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        import json

        print(json.dumps(run_build("all", 30), indent=2))
    else:
        mcp.run()
