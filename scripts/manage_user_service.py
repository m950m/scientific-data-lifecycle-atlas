#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ipaddress
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "scripts/serve_lifecycle_atlas.py"
UNIT_NAME = "scientific-data-lifecycle-atlas.service"


def unit_path() -> Path:
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return config_home / "systemd/user" / UNIT_NAME


def systemd_quote(value: str | Path) -> str:
    escaped = (
        str(value)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("%", "%%")
    )
    return f'"{escaped}"'


def systemd_path(value: str | Path) -> str:
    """Escape a path for directives that require an unquoted absolute path."""
    return str(value).replace("%", "%%").replace(" ", "\\x20")


def render_unit(bind: str, port: int) -> str:
    ipaddress.ip_address(bind)
    if not 1 <= port <= 65535:
        raise ValueError("port must be between 1 and 65535")
    python = shutil.which("python3")
    if python is None:
        raise RuntimeError("python3 is required to run the user service")

    return f"""[Unit]
Description=Scientific Data Lifecycle Atlas
After=network.target

[Service]
Type=simple
WorkingDirectory={systemd_path(ROOT)}
ExecStart={systemd_quote(python)} {systemd_quote(SERVER)} --bind {bind} --port {port}
Environment=PYTHONDONTWRITEBYTECODE=1
Restart=always
RestartSec=2
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only

[Install]
WantedBy=default.target
"""


def systemctl(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["systemctl", "--user", *args],
        check=check,
        text=True,
    )


def install(bind: str, port: int) -> int:
    target = unit_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_unit(bind, port), encoding="utf-8")
    systemctl("daemon-reload")
    systemctl("enable", "--now", UNIT_NAME)
    active = systemctl("is-active", "--quiet", UNIT_NAME, check=False)
    if active.returncode != 0:
        raise RuntimeError(
            f"{UNIT_NAME} was installed but did not become active; "
            f"run `systemctl --user status {UNIT_NAME}`"
        )
    print(f"Installed and started {UNIT_NAME}")
    print(f"Open http://{bind}:{port}")
    return 0


def remove() -> int:
    target = unit_path()
    systemctl("disable", "--now", UNIT_NAME, check=False)
    if target.exists():
        target.unlink()
    systemctl("daemon-reload")
    systemctl("reset-failed", UNIT_NAME, check=False)
    print(f"Removed {UNIT_NAME}")
    return 0


def status() -> int:
    return systemctl("status", "--no-pager", UNIT_NAME, check=False).returncode


def logs(lines: int) -> int:
    result = subprocess.run(
        [
            "journalctl",
            "--user",
            "--unit",
            UNIT_NAME,
            "--lines",
            str(lines),
            "--no-pager",
        ],
        check=False,
    )
    return result.returncode


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage the Atlas user service.")
    commands = parser.add_subparsers(dest="command", required=True)

    install_parser = commands.add_parser("install")
    install_parser.add_argument("--bind", default="127.0.0.1")
    install_parser.add_argument("--port", type=int, default=8000)

    commands.add_parser("status")
    logs_parser = commands.add_parser("logs")
    logs_parser.add_argument("--lines", type=int, default=50)
    commands.add_parser("remove")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "install":
        return install(args.bind, args.port)
    if args.command == "status":
        return status()
    if args.command == "logs":
        return logs(args.lines)
    if args.command == "remove":
        return remove()
    raise AssertionError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
