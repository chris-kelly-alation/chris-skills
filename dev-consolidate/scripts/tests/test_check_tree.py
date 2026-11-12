"""Tests for check_tree.py. Every tree is built in tmp_path."""

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import check_tree  # noqa: E402
from check_tree import check  # noqa: E402

SCRIPT = Path(__file__).resolve().parents[1] / "check_tree.py"


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def numbered(n: int) -> str:
    return "\n".join(f"line {i}" for i in range(n)) + "\n"


def triples(findings, kind=None):
    return {(f.level, f.kind, f.path) for f in findings if kind is None or f.kind == kind}


@pytest.fixture
def tree(tmp_path):
    root = tmp_path / "docs"
    root.mkdir()
    agents = tmp_path / "AGENTS.md"
    return root, agents


@pytest.mark.parametrize(
    "lines, expected",
    [
        (150, set()),
        (151, {("warn", "over-soft", "a.md")}),
        (301, {("error", "over-hard", "a.md")}),
    ],
)
def test_soft_and_hard_limits(tree, lines, expected):
    root, agents = tree
    write(root / "a.md", numbered(lines))
    findings = check(root, agents, skip={"orphan"})
    assert triples(findings, "over-soft") | triples(findings, "over-hard") == expected


def test_agents_md_excludes_dispatch_blocks(tree):
    root, agents = tree
    text = (
        numbered(140)
        + "<!-- dispatch:claude:begin -->\n"
        + numbered(100)
        + "<!-- dispatch:claude:end -->\n"
    )
    write(agents, text)
    findings = check(root, agents, skip={"orphan"})
    assert triples(findings, "over-soft") == set()
    assert triples(findings, "over-hard") == set()


def test_links_anchor_external_fence(tree):
    root, agents = tree
    write(root / "b.md", "target\n")
    write(
        root / "index.md",
        "[a](b.md#x)\n"
        "[e](https://x)\n"
        "```\n"
        "[f](nope.md)\n"
        "```\n"
        "[c](gone.md)\n",
    )
    findings = check(root, agents, skip={"orphan"})
    assert triples(findings, "broken-link") == {("error", "broken-link", "index.md")}
    broken = [f for f in findings if f.kind == "broken-link"]
    assert len(broken) == 1 and "gone.md" in broken[0].detail


def test_orphan_and_index_mention(tree):
    root, agents = tree
    write(root / "core.md", "core\n")
    write(root / "reach.md", "reached only by a mention in another doc\n")
    write(root / "other.md", "mentions `~/.agents/docs/reach.md` in prose\n")
    write(root / "lonely.md", "nothing points here\n")
    write(root / "inbox" / "a.md", "inbox entries are ignored\n")
    write(
        agents,
        "- Core: `~/.agents/docs/core.md`\n"
        "- Repo: `~/.agents/docs/repos/<name>.md`\n",
    )
    findings = check(root, agents)
    assert triples(findings, "orphan") == {
        ("error", "orphan", "other.md"),
        ("error", "orphan", "reach.md"),
        ("error", "orphan", "lonely.md"),
    }
    assert check(root, agents, skip={"orphan"}) == [
        f for f in findings if f.kind != "orphan"
    ]


def test_hub_missing_child(tree):
    root, agents = tree
    write(root / "hub.md", "[y](hub/y.md)\n")
    write(root / "hub" / "x.md", "x\n")
    write(root / "hub" / "y.md", "y\n")
    write(root / "full.md", "[x](full/x.md) and [y](full/y.md)\n")
    write(root / "full" / "x.md", "x\n")
    write(root / "full" / "y.md", "y\n")
    write(agents, "`~/.agents/docs/hub.md` `~/.agents/docs/full.md`\n")
    findings = check(root, agents)
    assert triples(findings, "hub-missing-child") == {
        ("error", "hub-missing-child", "hub.md")
    }


def test_lint_patterns(tree):
    root, agents = tree
    write(root / "ports.md", "Run `localhost:4200` locally.\n")
    write(root / "ts.md", "See `foo.ts:120` for the bug.\n")
    write(root / "secret.md", "```\nPASSPHRASE=abc\n```\n")
    write(root / "asof.md", "As of June we ship.\n")
    write(root / "sha.md", "Fixed in 0123456789abcdef0123456789abcdef01234567.\n")
    write(root / "table.md", "| a | b |\n|---|---|\n" + "| x | y |\n" * 16)
    write(root / "table_ok.md", "| a | b |\n|---|---|\n" + "| x | y |\n" * 15)
    write(
        agents,
        "`~/.agents/docs/ports.md` `~/.agents/docs/ts.md` `~/.agents/docs/secret.md` "
        "`~/.agents/docs/asof.md` `~/.agents/docs/sha.md` `~/.agents/docs/table.md` "
        "`~/.agents/docs/table_ok.md`\n",
    )
    findings = check(root, agents, skip={"orphan"})
    assert triples(findings, "lint") == {
        ("warn", "lint", "ts.md"),
        ("warn", "lint", "secret.md"),
        ("warn", "lint", "asof.md"),
        ("warn", "lint", "table.md"),
    }


def test_secret_lint_needs_literal_value(tree):
    root, agents = tree
    write(root / "literal.md", "```\nTOKEN=abc123\n```\n")
    write(root / "cmdsub.md", '```\nGITHUB_TOKEN="$(gh auth token)"\n```\n')
    write(root / "empty.md", "```\nGITHUB_TOKEN= gh auth refresh\n```\n")
    write(root / "var.md", "```\nPASSWORD=$DB_PASS\nTOKEN=\n```\n")
    write(
        agents,
        "`~/.agents/docs/literal.md` `~/.agents/docs/cmdsub.md` "
        "`~/.agents/docs/empty.md` `~/.agents/docs/var.md`\n",
    )
    findings = check(root, agents)
    assert triples(findings, "lint") == {("warn", "lint", "literal.md")}


def test_links_in_inline_code_are_ignored(tree):
    root, agents = tree
    write(root / "code.md", 'Use `template.blocks["name"](template.new_context(ctx))` here.\n')
    write(root / "real.md", "See [x](gone.md) and `[y](also-gone.md)`.\n")
    write(agents, "`~/.agents/docs/code.md` `~/.agents/docs/real.md`\n")
    findings = check(root, agents)
    assert triples(findings, "broken-link") == {("error", "broken-link", "real.md")}
    assert [f.detail for f in findings if f.kind == "broken-link"] == ["line 1: gone.md does not exist"]


class FakeGh:
    """Stands in for check_tree.run_gh. Records every call."""

    def __init__(self, branch_reply, contents_reply):
        self.branch_reply = branch_reply
        self.contents_reply = contents_reply
        self.calls = []

    def __call__(self, args):
        self.calls.append(args)
        if "--jq" in args:
            return self.branch_reply
        return self.contents_reply


def test_pointer_only_for_known_repos(tree, monkeypatch):
    root, agents = tree
    write(
        root / "repos" / "alation-ui.md",
        "Origin: github.com/Alation/alation-ui\n"
        "Stack: nx-frontend\n\n"
        "See `alation-ui:libs/x.ts` and `localhost:4200`.\n",
    )
    write(agents, "`~/.agents/docs/repos/alation-ui.md`\n")

    fake = FakeGh((0, "master\n"), (1, "gh: Not Found (HTTP 404)"))
    monkeypatch.setattr(check_tree, "run_gh", fake)
    findings = check(root, agents, skip={"orphan"}, pointers=True)
    assert triples(findings, "broken-pointer") == {
        ("error", "broken-pointer", "repos/alation-ui.md")
    }
    contents_calls = [c for c in fake.calls if "contents" in c[1]]
    assert len(contents_calls) == 1
    assert contents_calls[0][1].endswith("/contents/libs/x.ts?ref=master")
    assert all("localhost" not in " ".join(c) for c in fake.calls)

    fake = FakeGh((0, "master\n"), (1, "gh: Forbidden (HTTP 403)"))
    monkeypatch.setattr(check_tree, "run_gh", fake)
    findings = check(root, agents, skip={"orphan"}, pointers=True)
    assert triples(findings, "broken-pointer") == {
        ("warn", "broken-pointer", "repos/alation-ui.md")
    }

    # Without --pointers the gh seam is never called.
    fake = FakeGh((0, "master\n"), (1, "gh: Not Found (HTTP 404)"))
    monkeypatch.setattr(check_tree, "run_gh", fake)
    check(root, agents, skip={"orphan"})
    assert fake.calls == []


def test_exit_codes(tmp_path):
    root = tmp_path / "docs"
    agents = tmp_path / "AGENTS.md"

    # Warnings only: a reachable 151-line doc.
    write(root / "big.md", numbered(151))
    write(agents, "`~/.agents/docs/big.md`\n")
    warn_run = subprocess.run(
        [sys.executable, "-I", str(SCRIPT), "--root", str(root), "--agents-md", str(agents)],
        capture_output=True,
        text=True,
    )
    assert warn_run.returncode == 0
    assert warn_run.stdout.startswith("warn over-soft big.md:")

    # An error: an orphan doc.
    write(root / "lonely.md", "nothing points here\n")
    err_run = subprocess.run(
        [sys.executable, "-I", str(SCRIPT), "--root", str(root), "--agents-md", str(agents)],
        capture_output=True,
        text=True,
    )
    assert err_run.returncode == 1
    assert "error orphan lonely.md:" in err_run.stdout
