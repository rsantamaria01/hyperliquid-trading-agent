#!/usr/bin/env python3
"""Bootstrap launcher for the Hyperliquid Trading Agent MCP server.

On first run, creates a local venv inside the plugin folder and installs the
Python dependencies from requirements.txt. On subsequent runs, skips straight
to launching the server.

Why this exists:
- Cowork (desktop app) doesn't inherit your shell PATH, so depending on `uv`,
  `uvx`, or a globally-installed package is fragile.
- This script only needs `python3` to be reachable (it almost always is on
  Linux and macOS). Everything else is bootstrapped locally.

All progress output goes to stderr — MCP servers communicate over stdout.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN_ROOT = HERE.parent
VENV = HERE / ".venv"
SENTINEL = VENV / ".deps-installed"
REQUIREMENTS = HERE / "requirements.txt"

if os.name == "nt":
    VENV_PY = VENV / "Scripts" / "python.exe"
else:
    VENV_PY = VENV / "bin" / "python"


def _log(msg: str) -> None:
    print(f"[hyperliquid-mcp bootstrap] {msg}", file=sys.stderr, flush=True)


def _create_venv_if_missing() -> None:
    if VENV_PY.exists():
        return
    _log(f"creating venv at {VENV}")
    try:
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV)])
    except subprocess.CalledProcessError as e:
        _log(f"venv creation failed: {e}")
        _log("on Debian/Ubuntu you may need: sudo apt install python3-venv")
        sys.exit(2)


def _install_deps_if_needed() -> None:
    if SENTINEL.exists():
        return
    _log("installing dependencies (first run only, ~30 seconds)")
    pip_args = [str(VENV_PY), "-m", "pip", "install", "--upgrade", "pip", "--quiet"]
    subprocess.check_call(pip_args)
    install_args = [str(VENV_PY), "-m", "pip", "install", "-r", str(REQUIREMENTS), "--quiet"]
    subprocess.check_call(install_args)
    SENTINEL.write_text("ok\n")
    _log("dependencies installed")


def main() -> None:
    try:
        _create_venv_if_missing()
        _install_deps_if_needed()
    except subprocess.CalledProcessError as e:
        _log(f"bootstrap failed: {e}")
        sys.exit(1)

    # Make `mcp_server` importable from PLUGIN_ROOT when we exec the venv python
    env = os.environ.copy()
    existing_pp = env.get("PYTHONPATH", "")
    sep = ";" if os.name == "nt" else ":"
    env["PYTHONPATH"] = (str(PLUGIN_ROOT) + (sep + existing_pp if existing_pp else ""))

    args = [str(VENV_PY), "-m", "mcp_server.server"]
    _log("starting MCP server")
    os.execvpe(str(VENV_PY), args, env)


if __name__ == "__main__":
    main()
