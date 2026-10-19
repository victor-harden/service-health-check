#!/usr/bin/env python3
"""Run systemd/TCP/HTTP health checks from a JSON config."""
from __future__ import annotations

import argparse
import json
import shutil
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path


def check_systemd(unit: str, timeout: float = 5.0) -> tuple[bool, str]:
    if shutil.which("systemctl") is None:
        return False, "systemctl not available"
    proc = subprocess.run(["systemctl", "is-active", unit],
                          capture_output=True, text=True, timeout=timeout)
    state = proc.stdout.strip() or "unknown"
    return proc.returncode == 0 and state == "active", state


def check_tcp(host: str, port: int, timeout: float = 3.0) -> tuple[bool, str]:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, "connected"
    except OSError as exc:
        return False, str(exc)


def check_http(url: str, expect: int = 200, timeout: float = 5.0) -> tuple[bool, str]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            code = response.status
            return code == expect, f"HTTP {code}"
    except urllib.error.HTTPError as exc:
        return exc.code == expect, f"HTTP {exc.code}"
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        return False, str(exc)


def run_checks(config: dict):
    results = []
    for check in config.get("checks", []):
        kind = check.get("type")
        name = check.get("name", kind or "check")
        timeout = float(check.get("timeout", 5.0))
        if kind == "systemd":
            ok, detail = check_systemd(check["unit"], timeout)
        elif kind == "tcp":
            ok, detail = check_tcp(check["host"], int(check["port"]), timeout)
        elif kind == "http":
            ok, detail = check_http(check["url"], int(check.get("expect", 200)), timeout)
        else:
            ok, detail = False, f"unknown check type: {kind}"
        results.append({"name": name, "type": kind, "ok": ok, "detail": detail})
    return results


def render(results) -> str:
    lines = []
    for row in results:
        lines.append(f"[{'OK' if row['ok'] else 'FAIL'}] {row['name']:<20} "
                     f"{row['type']:<8} {row['detail']}")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Service health checks")
    parser.add_argument("config", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"cannot read config: {exc}", file=sys.stderr)
        return 2

    results = run_checks(config)
    print(json.dumps(results, indent=2) if args.json else render(results))
    return 0 if results and all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
