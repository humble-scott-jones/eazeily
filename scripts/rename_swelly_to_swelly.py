#!/usr/bin/env python3
"""
Safe repo-wide rename tool: swelly -> swelly

What it does:
- Scans the repository tree (defaults to current directory)
- In text files, replaces:
    swelly  -> swelly
    Swelly  -> Swelly
    SWELLY  -> SWELLY
- Renames files and directories whose names contain 'swelly' (same casing rules)
- Produces a dry-run summary by default
- Optionally applies changes and makes a backup of changed files

IMPORTANT:
- This tool only edits text files it can decode as UTF-8. Binary files are skipped.
- It will not rename the remote GitHub repository for you (that must be done via GitHub UI or gh API/CLI).
- Review the dry-run output before running with --apply.
"""

from __future__ import annotations
import argparse
import os
import sys
import shutil
import time
from typing import List, Tuple

# Directories to skip entirely
SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".idea",
    ".venv/*",
}

# File extensions to definitely treat as binary/skip text replacement (images, db, compiled, etc.)
SKIP_EXTS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".exe", ".dll", ".so", ".dylib",
    ".pyc", ".class", ".db", ".sqlite", ".sqlite3", ".bin", ".woff", ".woff2",
    ".ttf", ".otf", ".zip", ".tar", ".gz", ".bz2",
}

REPLACEMENTS: List[Tuple[str, str]] = [
    ("swelly", "swelly"),
    ("Swelly", "Swelly"),
    ("SWELLY", "SWELLY"),
]


def is_ignored_dir(name: str) -> bool:
    return name in SKIP_DIRS


def has_skip_ext(filename: str) -> bool:
    _, ext = os.path.splitext(filename)
    return ext.lower() in SKIP_EXTS


def collect_paths(root: str) -> List[str]:
    files = []
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        # mutate dirnames in-place to skip dirs
        dirnames[:] = [d for d in dirnames if not is_ignored_dir(d)]
        for fn in filenames:
            files.append(os.path.join(dirpath, fn))
    return files


def is_text_file(path: str) -> bool:
    if has_skip_ext(path):
        return False
    # Try to decode small portion or whole file as utf-8
    try:
        with open(path, "rb") as fh:
            chunk = fh.read(4096)
            if not chunk:
                return True
            chunk.decode("utf-8")
        return True
    except Exception:
        return False


def preview_replacements_in_text(text: str) -> Tuple[str, bool]:
    new = text
    changed = False
    for old, new_word in REPLACEMENTS:
        if old in new:
            new = new.replace(old, new_word)
            changed = True
    return new, changed


def transform_filename(name: str) -> Tuple[str, bool]:
    new_name = name
    changed = False
    for old, new_word in REPLACEMENTS:
        if old in new_name:
            new_name = new_name.replace(old, new_word)
            changed = True
    return new_name, changed


def make_backup(backup_root: str, path: str) -> None:
    dest = os.path.join(backup_root, os.path.relpath(path))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copy2(path, dest)


def run_dry_run(root: str) -> Tuple[List[str], List[str]]:
    modified_files = []
    renamed_paths = []

    paths = collect_paths(root)
    for path in paths:
        if not is_text_file(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as fh:
                text = fh.read()
        except Exception:
            # skip files we can't decode as text
            continue
        new_text, changed = preview_replacements_in_text(text)
        if changed:
            modified_files.append(path)

    # check renames for files and directories
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        # directories
        for d in list(dirnames):
            new_d, changed = transform_filename(d)
            if changed:
                renamed_paths.append(os.path.join(dirpath, d))
        # files
        for f in filenames:
            new_f, changed = transform_filename(f)
            if changed:
                renamed_paths.append(os.path.join(dirpath, f))

    return modified_files, renamed_paths


def apply_changes(root: str, modified_files: List[str], renamed_paths: List[str], backup_root: str) -> None:
    # Backup and apply content changes
    if modified_files:
        print(f"Backing up {len(modified_files)} modified files to: {backup_root}")
    for path in modified_files:
        make_backup(backup_root, path)
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
        new_text, changed = preview_replacements_in_text(text)
        if changed:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(new_text)

    # Rename files and directories.
    # To avoid conflicts when renaming directories, walk bottom-up
    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        # files first
        for f in filenames:
            old_path = os.path.join(dirpath, f)
            new_f, changed = transform_filename(f)
            if changed:
                new_path = os.path.join(dirpath, new_f)
                print(f"Renaming file: {old_path} -> {new_path}")
                make_backup(backup_root, old_path)
                os.replace(old_path, new_path)
        # directories
        for d in dirnames:
            old_dir = os.path.join(dirpath, d)
            new_d, changed = transform_filename(d)
            if changed:
                new_dir = os.path.join(dirpath, new_d)
                print(f"Renaming directory: {old_dir} -> {new_dir}")
                # it's safer to move than replace
                make_backup(backup_root, old_dir)  # this will copy the dir (fails for large trees)
                os.replace(old_dir, new_dir)


def main():
    parser = argparse.ArgumentParser(description="Rename swelly -> swelly across a repo (dry-run by default).")
    parser.add_argument("--path", "-p", default=".", help="Root path to run the rename (default: current directory).")
    parser.add_argument("--apply", action="store_true", help="Apply the changes. Without this flag a dry-run is performed.")
    parser.add_argument("--no-backup", action="store_true", help="Do not create a backup when applying changes.")
    parser.add_argument("--yes", "-y", action="store_true", help="Implicitly answer yes to prompts (used with --apply).")
    args = parser.parse_args()

    root = os.path.abspath(args.path)
    if not os.path.isdir(root):
        print("Path is not a directory:", root)
        sys.exit(1)

    print(f"Scanning repository tree at: {root}")
    modified_files, renamed_paths = run_dry_run(root)

    print("\n=== Dry-run summary ===")
    print(f"Files that will be modified (content replacements): {len(modified_files)}")
    for p in modified_files[:50]:
        print("  -", os.path.relpath(p, root))
    if len(modified_files) > 50:
        print(f"  ... and {len(modified_files)-50} more")

    print(f"\nFiles/directories that will be renamed: {len(renamed_paths)}")
    for p in renamed_paths[:50]:
        print("  -", os.path.relpath(p, root))
    if len(renamed_paths) > 50:
        print(f"  ... and {len(renamed_paths)-50} more")

    # Show some example content snippets for the first few modified files
    if modified_files:
        print("\nSample snippets (original -> preview):")
        for p in modified_files[:5]:
            try:
                with open(p, "r", encoding="utf-8") as fh:
                    text = fh.read()
            except Exception:
                continue
            preview = text[:800].replace("\n", "\\n")
            preview_new = preview
            for old, new_word in REPLACEMENTS:
                preview_new = preview_new.replace(old, new_word)
            print(f"\nFile: {os.path.relpath(p, root)}")
            print("  original snippet: ", preview[:300])
            print("  new snippet     : ", preview_new[:300])

    if not args.apply:
        print("\nNo changes applied. Run this script with --apply to perform the rename.")
        print("Example: python3 rename_swelly_to_swelly.py --apply")
        sys.exit(0)

    # Confirm
    if not args.yes:
        confirm = input("\nProceed with applying changes? Type 'yes' to continue: ").strip().lower()
        if confirm != "yes":
            print("Aborted by user.")
            sys.exit(1)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_root = os.path.join(root, f"rename_backup_{timestamp}") if not args.no_backup else None
    if backup_root:
        print(f"Creating backup root: {backup_root}")
        os.makedirs(backup_root, exist_ok=True)

    # Apply
    apply_changes(root, modified_files, renamed_paths, backup_root or "/tmp")

    print("\nApply complete.")
    print("Manual follow-ups you should consider:")
    print(" - Inspect the backup directory and changed files.")
    print(" - Update the SQLite DB filename if you renamed swelly.db -> swelly.db in code/config.")
    print(" - Update any CI/CD references, Docker images, or external integrations that expect the old name.")
    print(" - Rename the GitHub repository if desired (this script does NOT change the remote repo name).")
    print("   You can rename via GitHub UI or with GitHub CLI: `gh repo rename OWNER/old-name --new-name swelly`")
    print(" - If you changed the repo root directory name, update your git remote URLs and local remotes as needed.")
    print(" - Run your test suite: `PYTHONPATH=. pytest -q`")


if __name__ == "__main__":
    main()
