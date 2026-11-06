#!/usr/bin/env python3
"""check_path_leaks.py - block leaked local machine paths from entering git.

Zero dependencies (Python 3 stdlib only).

Usage:
  check_path_leaks.py            # scan staged files (pre-commit mode)
  check_path_leaks.py --all      # scan all tracked text files
  check_path_leaks.py FILE...    # scan the given files

Exit codes: 0 = clean, 1 = leaks found, 2 = usage / git error.

Patterns flagged:
  /Users/<name>         macOS home directories
  /private/tmp/         macOS private temp
  /tmp/claude-          Claude Code scratch directories
  C:\\Users\\<name>      Windows home directories
  /home/<name>/         Linux home directories
  -Users-<name>         Claude Code project-dir slugs (~/.claude/projects/...)
  Generic placeholder names (user, runner, ubuntu, name, alice, <name>, ...)
  are not flagged for any home pattern.

Lines containing `path-leak: allow` are ignored.
"""
import os
import re
import subprocess
import sys

TEXT_EXT = {
    ".md", ".txt", ".json", ".yaml", ".yml", ".py", ".js", ".ts", ".tsx",
    ".jsx", ".sh", ".html", ".toml", ".css", ".csv", ".ini", ".cfg", ".env",
    ".xml", ".svg", ".mjs", ".cjs", ".rst", ".mdx", ".vue", ".sql",
}
TEXT_NAMES = {"Dockerfile", "Makefile", "README", "LICENSE", ".gitignore",
              ".gitattributes", ".env.example", "pre-commit"}
SKIP_DIRS = {"node_modules", ".venv", "venv", "dist", "build", ".git",
             "__pycache__", ".next", ".cache"}
GENERIC_HOMES = {"user", "users", "runner", "ubuntu", "ec2-user", "vscode",
                 "node", "app", "deploy", "ci", "username", "USER", "me",
                 "you", "yourname", "your-name", "your_name", "name", "alice",
                 "bob", "example", "<user>", "<name>", "<username>", "<you>",
                 "$USER", "${USER}", "%USERNAME%", "...", "<LOCAL_USER>",
                 "<LOCAL_ROOT>"}
ALLOW_MARK = "path-leak: allow"
SELF_NAME = os.path.basename(__file__)

# `(?<![\w./])` keeps URL path segments such as example.com/en_US/home/x
# from being mistaken for a filesystem home directory.
_NAME = r"[^/\\\s'\"`)\]）」]+"
PATTERNS = [
    ("macos-home", re.compile(r"(?<![\w./])/Users/(" + _NAME + ")")),
    ("macos-private-tmp", re.compile(r"(?<![\w./])/private/tmp/")),
    ("claude-scratch", re.compile(r"(?<![\w./])/tmp/claude-")),
    ("windows-home", re.compile(r"[A-Za-z]:\\\\?Users\\\\?(" + _NAME + ")")),
    ("linux-home", re.compile(r"(?<![\w./])/home/(" + _NAME + ")/")),
    # Claude Code project-dir slugs such as ~/.claude/projects/-Users-<name>/
    ("home-slug", re.compile(r"-Users-(" + _NAME + ")")),
]
HOME_PATTERNS = {"macos-home", "windows-home", "linux-home", "home-slug"}


def git(*args):
    try:
        out = subprocess.run(["git", *args], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        sys.stderr.write("git error: %s\n" % e)
        sys.exit(2)
    return out.stdout.decode("utf-8", "replace")


def staged_files():
    return [f for f in git("diff", "--cached", "--name-only",
                           "--diff-filter=ACMR", "-z").split("\0") if f]


def tracked_files():
    return [f for f in git("ls-files", "-z").split("\0") if f]


def is_text_candidate(path):
    parts = path.replace("\\", "/").split("/")
    if any(p in SKIP_DIRS for p in parts[:-1]):
        return False
    base = parts[-1]
    if base == SELF_NAME:  # the guard documents the very patterns it flags
        return False
    _, ext = os.path.splitext(base)
    return ext.lower() in TEXT_EXT or base in TEXT_NAMES


def looks_binary(data):
    return b"\0" in data[:8192]


def scan_line(line):
    hits = []
    if ALLOW_MARK in line:
        return hits
    for name, rx in PATTERNS:
        for m in rx.finditer(line):
            if name in HOME_PATTERNS and m.group(1) in GENERIC_HOMES:
                continue
            hits.append((name, m.group(0)))
    return hits


def scan_file(path):
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except (OSError, IOError):
        return []
    if looks_binary(data):
        return []
    text = data.decode("utf-8", "replace")
    results = []
    for n, line in enumerate(text.splitlines(), 1):
        for name, frag in scan_line(line):
            results.append((n, name, frag, line.strip()))
    return results


def main(argv):
    args = argv[1:]
    if args and args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if args and args[0] == "--all":
        files = tracked_files()
    elif args:
        files = args
    else:
        files = staged_files()

    total = 0
    for f in files:
        if not is_text_candidate(f) or not os.path.isfile(f):
            continue
        for n, name, frag, line in scan_file(f):
            total += 1
            print("%s:%d: [%s] %s" % (f, n, name, line[:160]))
    if total:
        sys.stderr.write(
            "\npath-leak guard: %d leaked local path(s) found. "
            "Replace with placeholders such as <LOCAL_ROOT>/... or "
            "<BUILD_SCRATCH>/..., or append `%s` to the line.\n" % (total, ALLOW_MARK))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
