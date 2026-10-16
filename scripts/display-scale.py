#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

USER_CONFIG = Path.home() / ".config/caelestia/hypr-user.lua"
BASE_CONFIG = Path.home() / ".config/hypr/hyprland.lua"


def hypr_env() -> dict[str, str]:
    env = os.environ.copy()
    if env.get("HYPRLAND_INSTANCE_SIGNATURE"):
        return env
    try:
        proc = subprocess.run(
            ["systemctl", "--user", "show-environment"],
            capture_output=True, text=True, timeout=2,
        )
        for line in proc.stdout.splitlines():
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key in {"HYPRLAND_INSTANCE_SIGNATURE", "XDG_RUNTIME_DIR", "WAYLAND_DISPLAY", "DISPLAY"}:
                env[key] = value
    except Exception:
        pass
    return env


def scale_lua(value: str) -> str:
    value = value.strip().lower()
    if value == "auto":
        return '"auto"'
    number = float(value)
    if not 0.5 <= number <= 4.0:
        raise ValueError("scale must be auto or between 0.5 and 4")
    return f"{number:g}"


def ensure_global_auto() -> None:
    if not BASE_CONFIG.exists():
        return
    text = BASE_CONFIG.read_text()
    # Caelestia's generic default must not force every output to scale 1;
    # per-output rules below are then able to win predictably.
    pattern = re.compile(
        r'(hl\.monitor\(\{\s*output\s*=\s*""\s*,\s*mode\s*=\s*"preferred"\s*,\s*position\s*=\s*"auto"\s*,\s*scale\s*=\s*)(?:1|"auto")(\s*,?\s*\}\))',
        re.S,
    )
    new, count = pattern.subn(r'\1"auto"\2', text, count=1)
    if count and new != text:
        BASE_CONFIG.write_text(new)


def replace_monitor_scale(text: str, monitor: str, scale_expr: str) -> tuple[str, bool]:
    # Find hl.monitor({...}) blocks and replace only the block whose output
    # matches the requested monitor. This preserves mode, position, refresh,
    # transforms and any other user choices.
    block_re = re.compile(r'hl\.monitor\(\{.*?\}\)', re.S)
    for match in block_re.finditer(text):
        block = match.group(0)
        out = re.search(r'\boutput\s*=\s*"([^"]+)"', block)
        if not out or out.group(1) != monitor:
            continue
        if re.search(r'\bscale\s*=', block):
            updated = re.sub(r'(\bscale\s*=\s*)(?:"auto"|[-+]?[0-9]*\.?[0-9]+)', rf'\g<1>{scale_expr}', block, count=1)
        else:
            updated = block[:-2].rstrip() + f', scale = {scale_expr} }})'
        return text[:match.start()] + updated + text[match.end():], True
    return text, False


def persist(monitor: str, scale_expr: str) -> None:
    text = USER_CONFIG.read_text() if USER_CONFIG.exists() else ""
    text, found = replace_monitor_scale(text, monitor, scale_expr)
    if not found:
        if text and not text.endswith("\n"):
            text += "\n"
        text += (
            "\n-- DisplayScale plugin managed monitor rule\n"
            f'hl.monitor({{ output = "{monitor}", mode = "preferred", position = "auto", scale = {scale_expr} }})\n'
        )
    USER_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    USER_CONFIG.write_text(text)


def current_monitor(monitor: str, env: dict[str, str]) -> dict | None:
    try:
        proc = subprocess.run(["hyprctl", "monitors", "-j"], capture_output=True, text=True, timeout=2, env=env)
        data = json.loads(proc.stdout or "[]")
        return next((item for item in data if item.get("name") == monitor), None)
    except Exception:
        return None


def apply_live(monitor: str, scale_expr: str) -> None:
    env = hypr_env()
    info = current_monitor(monitor, env)
    if not info:
        return
    width = int(info.get("width") or 0)
    height = int(info.get("height") or 0)
    refresh = float(info.get("refreshRate") or 60.0)
    x = int(info.get("x") or 0)
    y = int(info.get("y") or 0)
    # Scale updates must not reset a rotation forced by TabletMode. A missing
    # transform entry is equivalent to the compositor's normal (0) value.
    transform = int(info.get("transform") or 0) % 4
    if width <= 0 or height <= 0:
        mode = "preferred"
    else:
        mode = f"{width}x{height}@{refresh:.2f}"
    expr = (
        "hl.monitor({ "
        f'output = "{monitor}", mode = "{mode}", position = "{x}x{y}", scale = {scale_expr}, transform = {transform}'
        " })"
    )
    subprocess.run(["hyprctl", "eval", expr], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3, env=env)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["apply", "status"])
    parser.add_argument("--monitor", default="eDP-1")
    parser.add_argument("--scale", default="2")
    args = parser.parse_args()

    if args.command == "status":
        env = hypr_env()
        info = current_monitor(args.monitor, env) or {}
        print(json.dumps({"monitor": args.monitor, "scale": info.get("scale"), "connected": bool(info)}))
        return 0

    expr = scale_lua(args.scale)
    ensure_global_auto()
    persist(args.monitor, expr)
    apply_live(args.monitor, expr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
