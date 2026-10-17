#!/usr/bin/env python3
"""Fake, noisy build tool for testing the MCP server without real hardware.

Simulates the kind of output a junky proprietary build system produces:
timestamps, progress noise, verbose diagnostics, and a non-zero exit code.

    python fake_junkbuild.py --target all
    python fake_junkbuild.py --clean
"""

from __future__ import annotations

import random
import sys
import time

NOISE = [
    "[{t}] INFO  toolchain shim v0.3.7 (built 2009)",
    "[{t}] INFO  loading module registry...",
    "[{t}] WARN  deprecated flag --legacy-abi ignored",
    "[{t}] INFO  preprocessing src/core/engine.cpp",
    "[{t}] DEBUG cache hit ratio 0.42",
    "[{t}] INFO  linking libjunk.so",
]

ERRORS = [
    "src/core/engine.cpp:142: error: 'int' and 'Widget' are not convertible",
    "src/core/engine.cpp:188:9: error: expected ';' before '}' token",
    "src/net/socket.cpp:77: warning: unused parameter 'timeout'",
    "src/core/engine.cpp:201: fatal error: junk.h: No such file or directory",
]


def stamp() -> str:
    return time.strftime("%H:%M:%S")


def main() -> int:
    args = sys.argv[1:]
    if "--clean" in args:
        print(f"[{stamp()}] INFO  clean complete")
        return 0

    target = "all"
    if "--target" in args:
        target = args[args.index("--target") + 1]

    print(f"[{stamp()}] INFO  build target={target}")
    for _ in range(4):
        print(random.choice(NOISE).format(t=stamp()))
        time.sleep(0.02)

    print(f"[{stamp()}] ERROR compilation of target '{target}' failed")
    for e in ERRORS:
        print(e)
        time.sleep(0.01)

    print(f"[{stamp()}] Build FAILED with 3 errors, 1 warning")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
