"""YAML for the mlops gate: PyYAML when installed, else a small reader for the subset config files use
(block mappings, block lists of scalars, flow lists [a, b] and flow mappings {a: b}, comments).

Ported from ds-factory's deploy-industrialize (jooaobrum).
"""

from __future__ import annotations

import re


def load(text: str):
    try:
        import yaml  # type: ignore
    except ImportError:
        return _Reader(text).parse()
    return yaml.safe_load(text)


def _scalar(s: str):
    s = s.strip()
    if not s:
        return None
    if (s[0] == s[-1]) and s[0] in "'\"" and len(s) >= 2:
        return s[1:-1]
    if s.startswith("[") and s.endswith("]"):
        return [_scalar(x) for x in _split(s[1:-1])] if s[1:-1].strip() else []
    if s.startswith("{") and s.endswith("}"):
        out = {}
        for part in _split(s[1:-1]):
            k, _, v = part.partition(":")
            out[k.strip()] = _scalar(v)
        return out
    low = s.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    if low in ("null", "~"):
        return None
    if re.fullmatch(r"[-+]?\d+", s):
        return int(s)
    if re.fullmatch(r"[-+]?\d*\.\d+(e[-+]?\d+)?", s, re.IGNORECASE):
        return float(s)
    return s


def _split(s: str):
    parts, depth, cur, quote = [], 0, "", None
    for ch in s:
        if quote:
            cur += ch
            quote = None if ch == quote else quote
        elif ch in "'\"":
            quote, cur = ch, cur + ch
        elif ch in "[{":
            depth, cur = depth + 1, cur + ch
        elif ch in "]}":
            depth, cur = depth - 1, cur + ch
        elif ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur)
    return parts


def _strip_comment(line: str) -> str:
    out, quote = "", None
    for i, ch in enumerate(line):
        if quote:
            quote = None if ch == quote else quote
        elif ch in "'\"":
            quote = ch
        elif ch == "#" and (i == 0 or line[i - 1] in " \t"):
            break
        out += ch
    return out.rstrip()


class _Reader:
    def __init__(self, text):
        self.lines = [(len(l) - len(l.lstrip(" ")), l.strip()) for l in
                      (_strip_comment(x) for x in text.splitlines()) if l.strip() and l.strip() != "---"]
        self.i = 0

    def parse(self):
        return self._block(0) if self.lines else None

    def _block(self, indent):
        if self.i < len(self.lines) and self.lines[self.i][1].startswith("- "):
            return self._list(indent)
        return self._map(indent)

    def _list(self, indent):
        out = []
        while self.i < len(self.lines):
            ind, s = self.lines[self.i]
            if ind < indent or not s.startswith("- "):
                break
            self.i += 1
            out.append(_scalar(s[2:]))
        return out

    def _map(self, indent):
        out = {}
        while self.i < len(self.lines):
            ind, s = self.lines[self.i]
            if ind < indent:
                break
            if ind > indent:
                raise ValueError(f"unexpected indentation at: {s}")
            key, sep, val = s.partition(":")
            if not sep:
                raise ValueError(f"expected 'key: value' at: {s}")
            self.i += 1
            if val.strip():
                out[key.strip()] = _scalar(val)
            elif self.i < len(self.lines) and self.lines[self.i][0] > indent:
                out[key.strip()] = self._block(self.lines[self.i][0])
            elif self.i < len(self.lines) and self.lines[self.i][0] == indent and self.lines[self.i][1].startswith("- "):
                out[key.strip()] = self._list(indent)
            else:
                out[key.strip()] = None
        return out
