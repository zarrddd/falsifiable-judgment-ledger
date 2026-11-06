#!/usr/bin/env python3
"""check_path_leaks.py - block leaked local machine paths from entering git.

Zero dependencies (Python 3 stdlib only).

Usage:
  check_path_leaks.py            # scan staged files (pre-commit mode)
  check_path_leaks.py --all      # scan all tracked text files
  check_path_leaks.py FILE...    # scan the given files
  check_path_leaks.py --rev REV  # scan every text blob in commit REV (no checkout)

Exit codes: 0 = clean, 1 = leaks found, 2 = usage / git error.

Patterns flagged:
  /Users/<name>         macOS home directories
  /private/tmp/         macOS private temp
  /tmp/claude-          Claude Code scratch directories
  C:\\Users\\<name>      Windows home directories
  /home/<name>/         Linux home directories
  -Users-<name>         Claude Code project-dir slugs (~/.claude/projects/...)
  <PLACEHOLDER>/...//Users/<name>, ...//Users/<name>
                        half-scrubbed paths (placeholder prefix + real home)
  owner username        the machine owner's login name anywhere in text
                        (word-bounded, case-insensitive). Never hardcoded:
                        read from $PATH_LEAK_OWNER_NAMES (comma-separated),
                        the file named by $PATH_LEAK_OWNER_FILE,
                        ~/.config/path-leak-guard/owner_names, or an
                        UNTRACKED <repo>/.path-leak-owner (one name per line).
                        Printed output always masks it as <OWNER>.
  ls -l owner column    `-rw-r--r--@ 1 <name> staff ...` style listings
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
    ".patch", ".diff", ".log", ".jsonl", ".ndjson", ".tsv", ".out", ".err",
    ".ipynb", ".yamllint", ".conf",
}
TEXT_NAMES = {"Dockerfile", "Makefile", "README", "LICENSE", ".gitignore",
              ".gitattributes", ".env.example", "pre-commit", "pre-push",
              "commit-msg"}
# Anything not known-binary is scanned (NUL-sniffed), so backups such as
# foo.py.bak-20260607, *.orig, *.rej or extension-less files are not missed.
BINARY_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".icns", ".bmp", ".tif",
    ".tiff", ".heic", ".psd", ".pdf", ".zip", ".gz", ".tgz", ".bz2", ".xz",
    ".7z", ".rar", ".tar", ".jar", ".whl", ".so", ".dylib", ".dll", ".exe",
    ".bin", ".o", ".a", ".class", ".pyc", ".woff", ".woff2", ".ttf", ".otf",
    ".eot", ".mp3", ".mp4", ".m4a", ".wav", ".mov", ".avi", ".mkv", ".webm",
    ".flac", ".ogg", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".key", ".numbers", ".pages", ".sqlite", ".db", ".parquet", ".npy",
    ".pkl", ".pt", ".onnx", ".dmg", ".iso",
}
SKIP_DIRS = {"node_modules", ".venv", "venv", "dist", "build", ".git",
             "__pycache__", ".next", ".cache"}
GENERIC_HOMES = {"user", "users", "runner", "ubuntu", "ec2-user", "vscode",
                 "node", "app", "deploy", "ci", "username", "USER", "me",
                 "you", "yourname", "your-name", "your_name", "name", "alice",
                 "bob", "example", "<user>", "<name>", "<username>", "<you>",
                 "$USER", "${USER}", "%USERNAME%", "...", "<LOCAL_USER>",
                 "<LOCAL_ROOT>", "<OWNER>"}
LS_GENERIC_OWNERS = GENERIC_HOMES | {"root", "nobody", "wheel", "staff",
                                     "admin", "daemon", "_www", "www-data"}
ALLOW_MARK = "path-leak: allow"
SELF_NAME = os.path.basename(__file__)

# `(?<![\w.])` keeps URL path segments such as example.com/Users/x or
# example.com/en_US/home/x from being mistaken for a filesystem home
# directory, while still catching `//Users/x` (doubled slash) and
# `<BUILD_SCRATCH>/...//Users/x` (half-scrubbed path).
_NAME = r"[^/\\\s'\"`)\]）」]+"
_LB = r"(?<![\w.])"
PATTERNS = [
    ("macos-home", re.compile(_LB + r"/Users/(" + _NAME + ")")),
    # placeholder or ellipsis directly followed by a real home, e.g.
    # <BUILD_SCRATCH>/.../Users/x or .../Users/x (the `.` blocks _LB above)
    ("half-scrubbed-home", re.compile(
        r"(?:<[A-Z_]+>|\.\.\.)/*(?:\.\.\./*)?/Users/(" + _NAME + ")")),
    ("macos-private-tmp", re.compile(_LB + r"/private/tmp/")),
    ("claude-scratch", re.compile(_LB + r"/tmp/claude-")),
    ("windows-home", re.compile(r"[A-Za-z]:\\\\?Users\\\\?(" + _NAME + ")")),
    ("linux-home", re.compile(_LB + r"/home/(" + _NAME + ")/")),
    # Claude Code project-dir slugs such as ~/.claude/projects/-Users-<name>/
    ("home-slug", re.compile(r"-Users-(" + _NAME + ")")),
    # `ls -l` listings: mode, optional xattr/ACL flag, links, OWNER, group
    ("ls-owner", re.compile(
        r"(?:^|(?<=[\s`'\"(（|]))[-dlcbps][rwxsStT-]{9}[@+.]?\s+\d+\s+"
        r"([^\s`'\"|]+)\s+[^\s`'\"|]+\s+\d")),
]
HOME_PATTERNS = {"macos-home", "half-scrubbed-home", "windows-home",
                 "linux-home", "home-slug"}
OWNER_MASK = "<OWNER>"


def _read_names(path):
    try:
        with open(os.path.expanduser(path), encoding="utf-8") as fh:
            return [l.strip() for l in fh if l.strip() and not l.lstrip().startswith("#")]
    except OSError:
        return []


def _repo_root():
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                             capture_output=True, check=True)
        return out.stdout.decode().strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _is_tracked(root, rel):
    r = subprocess.run(["git", "-C", root, "ls-files", "--error-unmatch", rel],
                       capture_output=True)
    return r.returncode == 0


def load_owner_names():
    """Owner login names to flag anywhere. Never stored in a tracked file."""
    names = []
    env = os.environ.get("PATH_LEAK_OWNER_NAMES", "")
    names += [n.strip() for n in env.split(",") if n.strip()]
    if os.environ.get("PATH_LEAK_OWNER_FILE"):
        names += _read_names(os.environ["PATH_LEAK_OWNER_FILE"])
    names += _read_names("~/.config/path-leak-guard/owner_names")
    root = _repo_root()
    if root and os.path.isfile(os.path.join(root, ".path-leak-owner")):
        if _is_tracked(root, ".path-leak-owner"):
            sys.stderr.write("path-leak guard: .path-leak-owner is TRACKED by git; "
                             "untrack it and add it to .gitignore\n")
            sys.exit(2)
        names += _read_names(os.path.join(root, ".path-leak-owner"))
    out = []
    for n in names:
        if len(n) >= 3 and n not in GENERIC_HOMES and n not in out:
            out.append(n)
    return out


OWNER_NAMES = None
OWNER_RX = None


def set_owner_names(names):
    global OWNER_NAMES, OWNER_RX
    OWNER_NAMES = list(names)
    OWNER_RX = (re.compile(r"(?<![A-Za-z0-9])(?:" + "|".join(map(re.escape, OWNER_NAMES))
                           + r")(?![A-Za-z0-9])", re.I) if OWNER_NAMES else None)


def mask(s):
    if OWNER_NAMES is None:
        set_owner_names(load_owner_names())
    return OWNER_RX.sub(OWNER_MASK, s) if OWNER_RX else s


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
    if ext.lower() in TEXT_EXT or base in TEXT_NAMES:
        return True
    return ext.lower() not in BINARY_EXT  # content is NUL-sniffed later


def looks_binary(data):
    return b"\0" in data[:8192]


def _generic(n):
    if n in GENERIC_HOMES:
        return True
    # `<LOCAL_USER>-rest-of-slug`: a placeholder followed by slug text
    return n.startswith("<") and n[:n.find(">") + 1] in GENERIC_HOMES


def scan_line(line):
    if OWNER_NAMES is None:
        set_owner_names(load_owner_names())
    hits = []
    if ALLOW_MARK in line:
        return hits
    for name, rx in PATTERNS:
        for m in rx.finditer(line):
            if name in HOME_PATTERNS and _generic(m.group(1)):
                continue
            if name == "ls-owner" and m.group(1) in LS_GENERIC_OWNERS:
                continue
            hits.append((name, m.group(0)))
    if OWNER_RX:
        covered = " ".join(f for _, f in hits)
        for m in OWNER_RX.finditer(line):
            if not OWNER_RX.search(covered):
                hits.append(("owner-name", m.group(0)))
    return hits


def scan_file(path):
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except (OSError, IOError):
        return []
    return scan_bytes(data)


def scan_bytes(data):
    if looks_binary(data):
        return []
    text = data.decode("utf-8", "replace")
    results = []
    for n, line in enumerate(text.splitlines(), 1):
        for name, frag in scan_line(line):
            results.append((n, name, frag, line.strip()))
    return results


def rev_blobs(rev):
    """Yield (path, bytes) for every text-candidate blob in commit `rev`."""
    entries = []
    for rec in git("ls-tree", "-r", "-z", rev).split("\0"):
        if not rec:
            continue
        meta, path = rec.split("\t", 1)
        mode, typ, sha = meta.split()
        if typ == "blob" and mode != "120000" and is_text_candidate(path):
            entries.append((path, sha))
    if not entries:
        return
    p = subprocess.Popen(["git", "cat-file", "--batch"], stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE)
    p.stdin.write("".join(sha + "\n" for _, sha in entries).encode())
    p.stdin.close()
    for path, _ in entries:
        header = p.stdout.readline().split()
        size = int(header[2])
        data = p.stdout.read(size)
        p.stdout.read(1)
        yield path, data
    p.wait()


def main(argv):
    args = argv[1:]
    if args and args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    total = 0
    if args and args[0] == "--rev":
        if len(args) != 2:
            sys.stderr.write("usage: check_path_leaks.py --rev REV\n")
            return 2
        for f, data in rev_blobs(args[1]):
            for n, name, frag, line in scan_bytes(data):
                total += 1
                print("%s:%d: [%s] %s" % (mask(f), n, name, mask(line[:160])))
    else:
        if args and args[0] == "--all":
            files = tracked_files()
        elif args:
            files = args
        else:
            files = staged_files()
        for f in files:
            if not is_text_candidate(f) or not os.path.isfile(f):
                continue
            for n, name, frag, line in scan_file(f):
                total += 1
                print("%s:%d: [%s] %s" % (mask(f), n, name, mask(line[:160])))
    if total:
        sys.stderr.write(
            "\npath-leak guard: %d leaked local path(s) found. "
            "Replace with placeholders such as <LOCAL_ROOT>/... or "
            "<BUILD_SCRATCH>/..., or append `%s` to the line.\n" % (total, ALLOW_MARK))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
