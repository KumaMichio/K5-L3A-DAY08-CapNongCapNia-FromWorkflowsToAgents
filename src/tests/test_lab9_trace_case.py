"""Regression test from docs/trace_case.md: seeded_regression C-002@11 (FM-03, ticket over DB).

The first wrong step is event 3 `model_override {"delay_days": 5}`: the DB says O-202 was 2 days
late, the ticket says 5. Every later step (quote 20000, refund, reply) follows from it."""
import pytest

pytestmark = pytest.mark.student


@pytest.fixture(scope="module")
def graders():
    from lab9 import graders

    return graders


def _ctx(case):
    from pydantic_evals.evaluators import EvaluatorContext

    return EvaluatorContext(name="trace_case", inputs={}, metadata=None, expected_output=case["label"],
                            output=case["trial"], duration=0.0, _span_tree=None, attributes={}, metrics={})


@pytest.fixture(scope="module")
def cases():
    from lab9.trace_case import investigate

    return {shape: investigate(shape, "C-002", 11) for shape in ("seeded_regression", "fixed")}


def test_lab9_trace_case_first_wrong_step_is_override(cases):
    events = cases["seeded_regression"]["trial"]["events"]
    kinds = [e.get("kind") for e in events]
    assert kinds.index("model_override") == 2          # event 3, right after the investigator
    assert events[2]["payload"] == {"delay_days": 5}
    db_delay = events[1]["payload"]["lookup_order"]["order"]["delay_days"]
    assert db_delay == 2


def test_lab9_trace_case_graders_catch_regression(cases, graders):
    bad = _ctx(cases["seeded_regression"])
    assert graders.DbFactKept().evaluate(bad).value is False
    assert graders.RefundAmountCorrect().evaluate(bad).value is False
    assert graders.TrialPass().evaluate(bad).value is False


def test_lab9_trace_case_fixed_passes(cases, graders):
    good = _ctx(cases["fixed"])
    assert "model_override" not in [e.get("kind") for e in cases["fixed"]["trial"]["events"]]
    for g in (graders.DbFactKept, graders.RefundAmountCorrect, graders.TrialPass, graders.ReplyMatchesLedger,
              graders.ProposalCorrect):
        assert g().evaluate(good).value is True
    assert graders.ApprovalBypass().evaluate(good).value is False
