"""Diff-based file sync for team-query.

Syncs generated files to a target directory, only copying files
whose content has actually changed. Optionally removes files from
the target that no longer exist in the source.
"""
import filecmp
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SyncResult:
    """Result of a sync operation."""

    copied: List[str] = field(default_factory=list)
    unchanged: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)

    @property
    def summary(self) -> str:
        parts = []
        if self.copied:
            parts.append(f"{len(self.copied)} copied")
        if self.unchanged:
            parts.append(f"{len(self.unchanged)} unchanged")
        if self.removed:
            parts.append(f"{len(self.removed)} removed")
        return ", ".join(parts) if parts else "nothing to sync"


def _find_config_file(start_dir: str) -> Optional[str]:
    """Walk up from start_dir looking for a formatter config file.

    Searches for ruff.toml, .ruff.toml, or pyproject.toml (with a [tool.ruff]
    section). Returns the first match, or None.
    """
    current = os.path.abspath(start_dir)
    for _ in range(50):  # safety limit
        for name in ("ruff.toml", ".ruff.toml"):
            candidate = os.path.join(current, name)
            if os.path.isfile(candidate):
                return candidate

        pyproject = os.path.join(current, "pyproject.toml")
        if os.path.isfile(pyproject):
            try:
                with open(pyproject, "r", encoding="utf-8") as f:
                    if "[tool.ruff" in f.read():
                        return pyproject
            except OSError:
                pass

        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return None


def format_directory(
    directory: str, formatter: str, config_path: Optional[str] = None
) -> None:
    """Run a formatter on all files in a directory.

    Args:
        directory: Path to the directory to format.
        formatter: Formatter command to run (e.g. "ruff format").
        config_path: Optional path to a config file to pass via --config.
    """
    parts = formatter.split()
    tool = parts[0]

    # Look for the tool on PATH first
    resolved = shutil.which(tool)

    # Also check the bin directory of the current Python interpreter
    # (handles pipx/venv installs where the tool isn't on system PATH)
    if not resolved:
        bin_dir = os.path.dirname(sys.executable)
        candidate = os.path.join(bin_dir, tool)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            resolved = candidate

    if not resolved:
        raise RuntimeError(
            f"Formatter '{tool}' not found. Install it with:\n"
            f"  pipx install 'team-query[format]'   # includes ruff\n"
            f"  pip install '{tool}'                 # or install it directly"
        )

    cmd = [resolved] + parts[1:]
    if config_path and "--config" not in parts:
        cmd.extend(["--config", config_path])
    cmd.append(directory)

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Formatter '{formatter}' failed (exit {result.returncode}):\n{result.stderr}"
        )


def sync_directory(
    source_dir: str,
    target_dir: str,
    formatters: Optional[tuple] = None,
) -> SyncResult:
    """Sync files from source_dir to target_dir, copying only changed files.

    - Files that exist in source but not target are copied.
    - Files that exist in both are compared by content; only differing files are copied.
    - Files that exist in target but not source are removed.

    Args:
        source_dir: Path to the generated output directory.
        target_dir: Path to the sync target directory.
        formatters: Optional sequence of formatter commands to run on source
                    before comparing (e.g. ("ruff check --fix", "ruff format")).

    Returns:
        SyncResult with details of what was synced.
    """
    result = SyncResult()

    source_dir = os.path.abspath(source_dir)
    target_dir = os.path.abspath(target_dir)

    if not os.path.isdir(source_dir):
        raise FileNotFoundError(f"Source directory does not exist: {source_dir}")

    # Find formatter config from the sync target's project
    config_path = _find_config_file(target_dir) if formatters else None
    if config_path:
        print(f"Using formatter config: {config_path}")

    # Format generated files before comparing, so diffs are only real changes
    for fmt in formatters or ():
        format_directory(source_dir, fmt, config_path=config_path)

    skip_dirs = {"__pycache__", "node_modules", ".git"}

    # Collect all relative file paths in source
    source_files = set()
    for root, dirs, files in os.walk(source_dir):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fname in files:
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, source_dir)
            source_files.add(rel)

    # Collect all relative file paths in target (if it exists)
    target_files = set()
    if os.path.isdir(target_dir):
        for root, dirs, files in os.walk(target_dir):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for fname in files:
                full = os.path.join(root, fname)
                rel = os.path.relpath(full, target_dir)
                target_files.add(rel)

    # Copy new or changed files
    for rel_path in sorted(source_files):
        src = os.path.join(source_dir, rel_path)
        dst = os.path.join(target_dir, rel_path)

        if os.path.exists(dst) and filecmp.cmp(src, dst, shallow=False):
            result.unchanged.append(rel_path)
        else:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            result.copied.append(rel_path)

    # Remove files in target that are no longer in source
    stale = target_files - source_files
    for rel_path in sorted(stale):
        dst = os.path.join(target_dir, rel_path)
        os.remove(dst)
        result.removed.append(rel_path)

    # Clean up empty directories in target
    if os.path.isdir(target_dir):
        for root, dirs, _files in os.walk(target_dir, topdown=False):
            for d in dirs:
                dirpath = os.path.join(root, d)
                if not os.listdir(dirpath):
                    os.rmdir(dirpath)

    return result
