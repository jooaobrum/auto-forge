from fractions import Fraction

from conftest import experiment, frozen, run, spec_text

lab = experiment.lab


def load(host, **kwargs):
    host.spec("exp", **kwargs)
    return lab.load_spec(lab.Work(host.root, "exp"))


def test_spec_metrics_override_lab(host):
    spec = load(host, metrics="")
    assert spec.metrics["cited_recall"].pass_at == "0.8"
    assert spec.metrics["correctness"].pass_at == "1"
    spec = load(host, metrics="| Metric | Pass at | Guardrail | Target |\n| --- | --- | --- | --- |\n"
                              "| cited_recall | 0.9 | | +0.2 |")
    assert spec.metrics["cited_recall"].pass_at == "0.9"
    assert spec.metrics["cited_recall"].target == "+0.2"
    assert spec.metrics["correctness"].pass_at == "1"  # untouched LAB row
    spec = load(host, metrics="| Metric | Pass at | Guardrail | Target |\n| --- | --- | --- | --- |\n"
                              "| cited_recall | | | +0.2 |")
    assert spec.metrics["cited_recall"].pass_at == "0.8"  # an empty spec cell keeps the LAB value


def test_defaults(host):
    spec = load(host)
    assert spec.variants == 3
    assert spec.k == {"target": 3, "affected": 1, "stable": 1}
    assert spec.guardrails() == {"input_tokens": Fraction(15)}
    host.write(".specs/LAB.md", (host.root / ".specs/LAB.md").read_text().replace(
        "| input_tokens | | | |", "| input_tokens | | | |\n| latency_ms | | | |"))
    assert load(host).guardrails() == {"input_tokens": Fraction(15), "latency_ms": Fraction(20)}
    spec = load(host, extra="**Variants**: 5\n**k**: target 5, stable 2",
                metrics="| Metric | Pass at | Guardrail | Target |\n| --- | --- | --- | --- |\n"
                        "| cited_recall | | | +0.1 |\n| input_tokens | | +30% | |")
    assert spec.variants == 5
    assert spec.k == {"target": 5, "affected": 1, "stable": 2}
    assert spec.guardrails()["input_tokens"] == Fraction(30)


def test_freeze_refuses_incomplete_spec(host):
    host.spec("exp", approved=False)
    host.commit()
    code, out = host.exp("freeze", "exp")
    assert code == 2
    assert "no **Approved**: line" in out
    host.spec("exp", metrics="| Metric | Pass at | Guardrail | Target |\n| --- | --- | --- | --- |\n"
                             "| bleu | | | |")
    code, out = host.exp("freeze", "exp")
    assert code == 2
    assert "no Target Metric" in out
    host.spec("exp")
    code, out = host.exp("freeze", "exp")
    assert code == 0, out


def test_cases_columns_adapt(host):
    cases = ("| Case | Question | Rubric | Cite |\n| --- | --- | --- | --- |\n"
             "| q01 | Why did TOOL-1 fail? | names the cause | PD-1, PD-2 |\n"
             "| q07 | History of TOOL-7? | lists events | |")
    base = [run("q01", n, recall=0, cited=["PD-1"], touched=["skill:history"]) for n in (1, 2, 3)]
    base += [run("q07", recall=0, touched=["skill:history"])]
    frozen(host, base, cases=cases, target="+0.5")
    spec = lab.load_spec(lab.Work(host.root, "exp"))
    assert spec.cases["q07"]["Cite"] == ""
    host.exp("select", "exp", "--variant", "v1")
    host.runs("exp", "v1", "q01", [run("q01", n, recall=0, cited=["PD-1", "PD-2"]) for n in (1, 2, 3)])
    host.runs("exp", "v1", "q07", [run("q07", recall=0)])
    code, out = host.exp("gate", "exp", "--variant", "v1")
    # q01: cited recall is computed from `cited` (1/2 -> 2/2), not the run's own metric; q07 is not graded on it
    assert code == 0, out
    results = (host.root / ".specs/features/exp/results.md").read_text()
    assert "| q01 | target, capability | fail | pass | 0.5 → 1 |" in results
    assert "| q07 | affected, capability | pass | pass |" in results
    only_required = ("| Case | Question | Rubric |\n| --- | --- | --- |\n| q01 | Why? | names the cause |")
    host.spec("other", text=spec_text(cases=only_required))
    host.commit()
    code, out = host.exp("freeze", "other")
    assert code == 0, out


def test_route_column_is_graded_when_present(host):
    cases = ("| Case | Question | Rubric | Route |\n| --- | --- | --- | --- |\n"
             "| q01 | Why? | cause | history |\n| q07 | History? | events | history |")
    frozen(host, [run("q01", n, recall=0.5, route="history") for n in (1, 2, 3)]
           + [run("q07", route="history", touched=["skill:history"])], cases=cases)
    host.exp("select", "exp", "--variant", "v1")
    host.runs("exp", "v1", "q01", [run("q01", n, route="history") for n in (1, 2, 3)])
    host.runs("exp", "v1", "q07", [run("q07", route="direct")])
    code, out = host.exp("gate", "exp", "--variant", "v1")
    assert code == 1
    assert "FAIL q07: regressed" in out


def test_cases_or_dataset(host):
    text = spec_text().split("## Cases")[0] + "## Metrics\n\n| Metric | Pass at | Guardrail | Target |\n" \
        "| --- | --- | --- | --- |\n| cited_recall | | | +0.1 |\n"
    host.spec("exp", text=text)
    host.commit()
    code, out = host.exp("freeze", "exp")
    assert code == 2
    assert "no Cases" in out
    host.spec("exp", text=text.replace("**Lane**: research", "**Lane**: research\n**Dataset**: mlflow:minds-40"))
    code, out = host.exp("freeze", "exp")
    assert code == 0, out
