"""Reads config/project.yml (its two-level subset) and resolves the environment's write target."""

from __future__ import annotations

import re
from pathlib import Path


def _value(text: str):
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return {k.strip(): _value(v) for k, v in (p.split(":", 1) for p in text[1:-1].split(","))}
    if text.startswith("[") and text.endswith("]"):
        return [p.strip() for p in text[1:-1].split(",")]
    return float(text) if re.fullmatch(r"\d+\.\d+", text) else text


def parse(text: str) -> dict:
    out: dict = {}
    section = None
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, _, rest = line.strip().partition(":")
        if not line.startswith(" "):
            section = key
            out[key] = _value(rest) if rest.strip() else {}
        else:
            out[section][key] = _value(rest)
    return out


def load(env: str, path: str = "config/project.yml") -> dict:
    cfg = parse(Path(path).read_text())
    target = cfg["environments"][env]
    cfg["env"] = env
    cfg["target"] = f"{target['catalog']}.{target['schema']}"
    return cfg
