# build-mcp

An MCP server that runs a build tool and returns **structured** compiler errors
to an LLM agent in opencode.

The value is in the parser: instead of dumping thousands of lines of noisy
build output into the agent's context, it returns a clean list of
`{file, line, severity, message}` diagnostics.

## Files

- `build_mcp.py` — the MCP server. Exposes `build` and `clean` tools.
- `fake_junkbuild.py` — a noisy fake build tool for testing without a real toolchain.
- `opencode.jsonc` — example opencode config registering the server.
- `requirements.txt` — the `mcp` package.

## Setup

```sh
git clone https://github.com/bpbenpatterson/build-mcp.git
cd build-mcp
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## Smoke test (no opencode needed)

```sh
python build_mcp.py --selftest
```

You should see JSON with `"error_count": 3` and structured error objects.

## Wire into opencode

Copy the `mcp` block from `opencode.jsonc` into your opencode config
(`~/.config/opencode/opencode.jsonc` or a project `opencode.json`), replacing
`/absolute/path/to/build-mcp` with the path you cloned to. Point
`BUILD_CMD` at the real build tool, and `command` at the venv's python.

Then restart opencode and prompt:

```
use the build-tools tool to build the project, then fix the errors
```

The agent will call `build`, receive the structured diagnostics, and act on them.

## Using the real build tool

Set `BUILD_CMD` to your real command. The server appends `--target <name>`
(or `--clean --target <name>`). If your tool uses different flags, edit
`run_build()` in `build_mcp.py`.

Adapt `ERROR_RE` in `build_mcp.py` to match your tool's actual error format.
That regex is the part that carries your domain knowledge, and it is what
makes the tool useful.

## Safety

- `build` has a timeout (`BUILD_TIMEOUT_S`, default 300s).
- No destructive targets are exposed. If you add `deploy` or similar, put an
  approval gate in front of it.
