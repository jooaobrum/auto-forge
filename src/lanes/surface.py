"""The Behavioral Surface: which paths a touched item maps to, Edit Scope matching, and content hashes."""

from __future__ import annotations

import fnmatch
import hashlib
import subprocess
from pathlib import Path


def in_scope(path: str, scope: list[str]) -> bool:
    """A path is in scope when it equals an entry, sits under an entry ending in `/`, or matches a glob."""
    for entry in scope:
        if path == entry or fnmatch.fnmatch(path, entry):
            return True
        if entry.endswith("/") and path.startswith(entry):
            return True
    return False


def overlaps(path: str, scope: list[str]) -> bool:
    """A surface path overlaps the scope when it is in scope or is a directory that holds a scope entry."""
    if in_scope(path, scope):
        return True
    prefix = path if path.endswith("/") else path + "/"
    return any(entry.startswith(prefix) for entry in scope)


def item_paths(surface: dict, items: list[str]) -> list[str]:
    paths: set[str] = set()
    for item in items:
        paths.update(surface.get(item, {}).get("paths", []))
    return sorted(paths)


def _files_at(root: Path, commit: str | None, path: str) -> list[tuple[str, bytes]]:
    if commit is None:
        target = root / path
        if target.is_dir():
            return [(str(p.relative_to(root)), p.read_bytes()) for p in sorted(target.rglob("*")) if p.is_file()]
        return [(path, target.read_bytes())] if target.exists() else [(path, b"<absent>")]
    listing = subprocess.run(["git", "ls-tree", "-r", "--name-only", commit, "--", path.rstrip("/")],
                             check=False, cwd=root, capture_output=True, text=True).stdout.split()
    if not listing:
        return [(path, b"<absent>")]
    files = []
    for name in listing:
        blob = subprocess.run(["git", "show", f"{commit}:{name}"], check=False, cwd=root, capture_output=True).stdout
        files.append((name, blob))
    return files


def content_hash(root: Path, paths: list[str], commit: str | None = None) -> str:
    """Hash of the content behind `paths`, read from the working tree or from `commit`."""
    digest = hashlib.sha256()
    for path in sorted(paths):
        for name, data in _files_at(root, commit, path):
            digest.update(name.encode() + b"\0" + hashlib.sha256(data).digest())
    return digest.hexdigest()
