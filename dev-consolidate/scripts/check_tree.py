#!/usr/bin/env python3
"""Mechanical audit of the agent docs tree (stdlib only).

Usage:
  python3 -I check_tree.py [--root DIR] [--agents-md FILE] [--skip KIND ...] [--pointers]

Prints one line per finding: "<level> <kind> <path>: <detail>".
Exits 1 if any finding is an error, else 0.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple
from urllib.parse import quote

SOFT_LIMIT = 150
HARD_LIMIT = 300
MAX_TABLE_ROWS = 15
SKIP_DIRS = ("inbox",)

DISPATCH_BEGIN = re.compile(r"<!--\s*dispatch:(claude|codex):begin\s*-->")
DISPATCH_END = re.compile(r"<!--\s*dispatch:(claude|codex):end\s*-->")
MENTION_RE = re.compile(r"~/\.agents/docs/([A-Za-z0-9_./-]+\.md)(?![A-Za-z0-9_./<-])")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
INLINE_CODE_RE = re.compile(r"`[^`]*`")
SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
POINTER_RE = re.compile(
    r"`(?:(?P<org>[A-Za-z0-9_.-]+)/)?(?P<repo>[A-Za-z0-9_.-]+):(?P<path>[^`\s]*[/.][^`\s]*)`"
    r"(?:[^`\n]{0,30}`(?P<symbol>[A-Za-z_][A-Za-z0-9_]*)`)?"
)
ORIGIN_RE = re.compile(r"^Origin:\s*github\.com/([^/\s]+)/([^/\s]+?)\s*$")
TABLE_SEP_RE = re.compile(r"\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?")

LINE_POINTER_RE = re.compile(
    r"[\w.-]+\.[A-Za-z][A-Za-z0-9]*:\d+(?:-\d+)?(?!\w)"
    r"|\b[\w.-]+:(?!//)[\w./-]*[/.][\w./-]*:\d+(?:-\d+)?(?!\w)"
)

PROSE_LINT = [
    (re.compile(r"\bas of\b", re.I), "time-bound phrase 'as of'"),
    (re.compile(r"\bin progress\b", re.I), "status phrase 'in progress'"),
    (re.compile(r"\bWIP\b", re.I), "WIP marker"),
    (re.compile(r"\bTODO\b", re.I), "TODO marker"),
    (LINE_POINTER_RE, "line-number code pointer"),
]
SECRET_RE = re.compile(
    r"(?:password|token|passphrase|secret)(?P<sep>\s*:\s*|\s+=\s+|=)(?P<value>\S+)", re.I
)
SECRET_SOURCE_RE = re.compile(r"1password|\.env\b|vault|keychain", re.I)
BASE64_RUN_RE = re.compile(r"[A-Za-z0-9+/]{40,}={0,2}")
HEX_RE = re.compile(r"[0-9a-fA-F]+")


class Finding(NamedTuple):
    level: str
    kind: str
    path: str
    detail: str


def _norm(path: Path) -> Path:
    return Path(os.path.normpath(path))


def _rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _scan(text: str):
    """Yield (lineno, line, in_fence). Fence marker lines count as in_fence."""
    in_fence = False
    for lineno, line in enumerate(text.splitlines(), start=1):
        if line.strip().startswith(("```", "~~~")):
            yield lineno, line, True
            in_fence = not in_fence
            continue
        yield lineno, line, in_fence


def _relative_links(text: str):
    for lineno, line, in_fence in _scan(text):
        if in_fence:
            continue
        for match in LINK_RE.finditer(INLINE_CODE_RE.sub("", line)):
            target = match.group(1).split("#", 1)[0]
            if not target or target.startswith(("/", "~")) or SCHEME_RE.match(target):
                continue
            yield lineno, target


def _outside_dispatch(text: str) -> list[str]:
    kept: list[str] = []
    inside = False
    for line in text.splitlines():
        if not inside and DISPATCH_BEGIN.search(line):
            inside = True
            continue
        if inside:
            if DISPATCH_END.search(line):
                inside = False
            continue
        kept.append(line)
    return kept


def _size_findings(rel: str, line_count: int) -> list[Finding]:
    if line_count > HARD_LIMIT:
        return [Finding("error", "over-hard", rel, f"{line_count} lines (hard limit {HARD_LIMIT})")]
    if line_count > SOFT_LIMIT:
        return [Finding("warn", "over-soft", rel, f"{line_count} lines (soft limit {SOFT_LIMIT})")]
    return []


def _long_non_hex_runs(line: str):
    for match in BASE64_RUN_RE.finditer(line):
        run = match.group(0).rstrip("=")
        if "/" not in run and not HEX_RE.fullmatch(run):
            yield run


def _has_secret(line: str) -> bool:
    """True when a secret-like key is assigned a literal value."""
    for match in SECRET_RE.finditer(line):
        value = match.group("value").strip("\"'`")
        if not value or value.startswith(("$", "<")) or SECRET_SOURCE_RE.search(line):
            continue
        tail = line[match.end() :].strip(" \t.,;`'\"")
        if ":" in match.group("sep") and tail:
            continue  # prose after "key:", not a bare value
        return True
    return False


def _lint(rel: str, text: str) -> list[Finding]:
    findings: list[Finding] = []
    table: list[tuple[int, str]] = []

    def flush_table() -> None:
        if not table:
            return
        has_sep = len(table) > 1 and TABLE_SEP_RE.fullmatch(table[1][1]) is not None
        rows = len(table) - (2 if has_sep else 0)
        if rows > MAX_TABLE_ROWS:
            findings.append(
                Finding("warn", "lint", rel, f"line {table[0][0]}: table has {rows} rows (max {MAX_TABLE_ROWS})")
            )
        table.clear()

    for lineno, line, in_fence in _scan(text):
        stripped = line.strip()
        is_table_line = not in_fence and stripped.startswith("|")
        if not is_table_line:
            flush_table()
        if is_table_line:
            table.append((lineno, stripped))
        if not in_fence:
            for pattern, why in PROSE_LINT:
                if pattern.search(line):
                    findings.append(Finding("warn", "lint", rel, f"line {lineno}: {why}"))
        if _has_secret(line):
            findings.append(Finding("warn", "lint", rel, f"line {lineno}: secret assignment"))
        for _run in _long_non_hex_runs(line):
            findings.append(Finding("warn", "lint", rel, f"line {lineno}: long base64-like run"))
    flush_table()
    return findings


def _is_404(output: str) -> bool:
    return "HTTP 404" in output or "Not Found" in output


def run_gh(args: list[str]) -> tuple[int, str]:
    """Run `gh` with args. Return (returncode, stdout on success else stderr)."""
    try:
        proc = subprocess.run(["gh", *args], capture_output=True, text=True)
    except OSError as exc:
        return 127, str(exc)
    return proc.returncode, proc.stdout if proc.returncode == 0 else proc.stderr


def _origin(hub_text: str) -> tuple[str, str] | None:
    for line in hub_text.splitlines()[:10]:
        match = ORIGIN_RE.match(line.strip())
        if match:
            return match.group(1), match.group(2)
    return None


def _symbol_present(output: str, symbol: str) -> bool:
    """False only when the file text was readable and lacks the symbol."""
    try:
        data = json.loads(output)
        text = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
    except (ValueError, KeyError, TypeError):
        return True
    return not data["content"] or symbol in text


def _pointer_findings(root: Path, docs: list[Path], texts: dict[Path, str], nodes: set[Path]) -> list[Finding]:
    findings: list[Finding] = []
    fetched: dict[tuple[str, str], tuple[int, str]] = {}
    for doc in docs:
        rel = _rel(root, doc)
        for lineno, line, in_fence in _scan(texts[_norm(doc)]):
            if in_fence:
                continue
            for match in POINTER_RE.finditer(line):
                org, repo, symbol = match.group("org"), match.group("repo"), match.group("symbol")
                path = match.group("path").split(":", 1)[0]
                if org:
                    slug = f"{org}/{repo}"
                else:
                    hub = _norm(root / "repos" / f"{repo}.md")
                    if hub not in nodes:
                        continue
                    origin = _origin(texts[hub])
                    if origin is None:
                        findings.append(
                            Finding("warn", "broken-pointer", rel, f"line {lineno}: repos/{repo}.md has no Origin line")
                        )
                        continue
                    slug = f"{origin[0]}/{origin[1]}"
                if (slug, path) not in fetched:
                    fetched[slug, path] = run_gh(["api", f"repos/{slug}/contents/{quote(path)}"])
                rc, out = fetched[slug, path]
                if rc != 0:
                    level = "error" if _is_404(out) else "warn"
                    what = "not found on" if level == "error" else f"gh failed ({out.strip()}) for"
                    findings.append(Finding(level, "broken-pointer", rel, f"line {lineno}: {path} {what} {slug}"))
                elif symbol and not _symbol_present(out, symbol):
                    detail = f"line {lineno}: symbol {symbol} not found in {path}"
                    findings.append(Finding("error", "broken-pointer", rel, detail))
    return findings


def _doc_files(root: Path) -> list[Path]:
    docs = []
    for path in root.rglob("*.md"):
        first = path.relative_to(root).parts[0]
        if first in SKIP_DIRS or first.startswith("."):
            continue
        docs.append(path)
    return sorted(docs)


def check(root, agents_md, skip=frozenset(), pointers: bool = False) -> list[Finding]:
    root = Path(root).expanduser().absolute()
    agents = Path(agents_md).expanduser().absolute()
    docs = _doc_files(root)
    nodes = {_norm(p) for p in docs}
    texts = {_norm(p): p.read_text(encoding="utf-8") for p in docs}
    findings: list[Finding] = []
    edges: dict[Path, set[Path]] = {}

    for doc in docs:
        rel = _rel(root, doc)
        text = texts[_norm(doc)]
        findings += _size_findings(rel, len(text.splitlines()))
        findings += _lint(rel, text)
        if " " in doc.name:
            findings.append(Finding("warn", "space-in-name", rel, "file name contains a space"))
        targets: set[Path] = set()
        for lineno, target in _relative_links(text):
            resolved = _norm(doc.parent / target)
            if not resolved.exists():
                findings.append(Finding("error", "broken-link", rel, f"line {lineno}: {target} does not exist"))
            elif resolved in nodes:
                targets.add(resolved)
        edges[_norm(doc)] = targets

    for doc in docs:
        hub_dir = doc.parent / doc.stem
        if not hub_dir.is_dir():
            continue
        for child in sorted(hub_dir.glob("*.md")):
            if _norm(child) not in edges[_norm(doc)]:
                findings.append(
                    Finding("error", "hub-missing-child", _rel(root, doc), f"does not link to {_rel(root, child)}")
                )

    agents_text = agents.read_text(encoding="utf-8") if agents.is_file() else ""
    findings += _size_findings(str(agents), len(_outside_dispatch(agents_text)))

    frontier = [_norm(root / m) for m in MENTION_RE.findall(agents_text)]
    frontier = [p for p in frontier if p in nodes]
    reached: set[Path] = set()
    while frontier:
        node = frontier.pop()
        if node in reached:
            continue
        reached.add(node)
        frontier.extend(edges.get(node, ()))
    for doc in docs:
        if _norm(doc) not in reached:
            findings.append(
                Finding("error", "orphan", _rel(root, doc), "no relative link or AGENTS.md mention reaches this doc")
            )

    if pointers:
        findings += _pointer_findings(root, docs, texts, nodes)

    return [f for f in findings if f.kind not in skip]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Mechanical audit of the agent docs tree.")
    parser.add_argument("--root", type=Path, default=Path("~/.agents/docs"))
    parser.add_argument("--agents-md", type=Path, default=Path("~/.agents/AGENTS.md"))
    parser.add_argument("--skip", nargs="+", action="extend", default=[], metavar="KIND")
    parser.add_argument("--pointers", action="store_true", help="check code pointers with gh")
    args = parser.parse_args(argv)

    findings = check(args.root, args.agents_md, skip=set(args.skip), pointers=args.pointers)
    for finding in findings:
        path = finding.path
        print(f"{finding.level} {finding.kind} {path}: {finding.detail}")
    return 1 if any(f.level == "error" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
