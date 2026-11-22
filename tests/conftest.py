from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


def load(skill: str, module: str):
    """Import a skill's script the way the agent runs it: its own folder first on the path."""
    folder = SKILLS / skill / "scripts"
    sys.path.insert(0, str(folder))
    try:
        spec = importlib.util.spec_from_file_location(f"{skill.replace('-', '_')}_{module}", folder / f"{module}.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        sys.path.remove(str(folder))


experiment = load("agent-spec-experiment", "experiment")
contract = load("agent-spec-pipeline", "contract")
route = load("agent-spec-router", "route")


def sh(root: Path, *args: str) -> str:
    return subprocess.run(list(args), cwd=root, check=True, capture_output=True, text=True).stdout


LAB = """# LAB

**Budget**: 1000000

## Metrics

| Metric | Pass at | Guardrail | Target |
| --- | --- | --- | --- |
| cited_recall | 0.8 | | |
| correctness | 1 | | |
| input_tokens | | | |

## Surface

| Item | Paths | Affects all |
| --- | --- | --- |
| skill:history | prompts/history.md | |
| tool:resolve_equipment | tools/resolve.py | |
| system_prompt | prompts/system.md | yes |

## Edit Scope

- prompts/
"""


def spec_text(cases: str = "", *, target: str = "+0.1", targets: str = "q01", scope: str = "- prompts/history.md",
              extra: str = "", approved: bool = True, metrics: str | None = None) -> str:
    rows = cases or "| q01 | Why did TOOL-1 fail? | names the cause |\n| q07 | History of TOOL-7? | lists events |"
    metrics_table = metrics if metrics is not None else (
        "| Metric | Pass at | Guardrail | Target |\n| --- | --- | --- | --- |\n"
        f"| cited_recall | | | {target} |")
    header = rows.splitlines()[0] if rows.startswith("| Case") else None
    table = rows if header else "| Case | Question | Rubric |\n| --- | --- | --- |\n" + rows
    return f"""# History citations

**Profile**: agent
**Lane**: research
{'**Approved**: 2026-11-22 - user: "go"' if approved else ''}
**Failure mode**: reads history, does not cite it
**Target cases**: {targets}
{extra}

## Problem

The agent reads the history records but cites a third of them.

## Diagnosis

A synthesis failure, not retrieval. Cause class: behavioral.

## Hypotheses

### H1 - cite-ids
- Idea: tell the history skill to cite the id of every record used
- Why: the records were read; only the citation was missing

## Cases

{table}

## Metrics

{metrics_table}

## Edit Scope

{scope}
"""


class Host:
    def __init__(self, root: Path, capsys):
        self.root = root
        self.capsys = capsys

    def write(self, rel: str, text: str) -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def commit(self, message: str = "change") -> None:
        sh(self.root, "git", "add", "-A")
        sh(self.root, "git", "commit", "-q", "-m", message, "--allow-empty")

    def _call(self, module, args) -> tuple[int, str]:
        self.capsys.readouterr()
        code = module.main(["--root", str(self.root), *args])
        return code, self.capsys.readouterr().out

    def exp(self, *args: str) -> tuple[int, str]:
        return self._call(experiment, args)

    def contract(self, *args: str) -> tuple[int, str]:
        return self._call(contract, args)

    def route(self, *args: str) -> tuple[int, str]:
        return self._call(route, args)

    def runs(self, slug: str, variant: str, name: str, runs: list[dict]) -> None:
        self.write(f".specs/features/{slug}/runs/{variant}/{name}.json", json.dumps({"runs": runs}))

    def spec(self, slug: str = "exp", text: str | None = None, **kwargs) -> None:
        self.write(f".specs/features/{slug}/plan.md", text if text is not None else spec_text(**kwargs))


@pytest.fixture
def host(tmp_path, capsys) -> Host:
    sh(tmp_path, "git", "init", "-q", "-b", "main")
    sh(tmp_path, "git", "config", "user.email", "test@example.com")
    sh(tmp_path, "git", "config", "user.name", "test")
    h = Host(tmp_path, capsys)
    h.write(".specs/LAB.md", LAB)
    h.write("prompts/history.md", "cite what you read\n")
    h.write("prompts/system.md", "you are a maintenance agent\n")
    h.write("tools/resolve.py", "def resolve(): ...\n")
    h.commit("initial")
    return h


def run(case: str, n: int = 1, recall: float = 1.0, correct: int = 1, tokens: int = 50_000,
        touched: list | None = None, **extra) -> dict:
    return {"case": case, "run": n, "metrics": {"cited_recall": recall, "correctness": correct,
                                                "input_tokens": tokens},
            "touched": touched or [], **extra}


def frozen(host: Host, baseline_runs: list[dict], slug: str = "exp", **spec_kwargs) -> None:
    """An approved spec, frozen at the current commit, with its Baseline recorded."""
    host.spec(slug, **spec_kwargs)
    host.write(f".specs/features/{slug}/base.json", json.dumps({"runs": baseline_runs}))
    host.commit("spec")
    code, out = host.exp("freeze", slug)
    assert code == 0, out
    code, out = host.exp("baseline", slug, "--from", f".specs/features/{slug}/base.json")
    assert code == 0, out


def verified(host: Host, slug: str = "exp", variant: str = "v1", verifier: str = "subagent", verdict: str = "PASS",
             findings: str = "None - the one change, the traces and two unnamed questions probed") -> None:
    """The Verifier's report on the variant (agent-spec-experiment references/verify.md)."""
    host.write(f".specs/features/{slug}/verification.md",
               f"# {slug} verification\n\n**Verdict**: {verdict}\n**Variant**: {variant}\n**HEAD**: abc1234\n"
               f"**Verifier**: {verifier}\n\n## Findings\n\n{findings}\n")
