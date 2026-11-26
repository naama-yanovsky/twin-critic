"""Part D: run the five required scenarios and save the logs.
Results from the language model and results from mock (control-flow) tests are saved separately."""

import json
from pathlib import Path

from pydantic import ValidationError

from evaluator import Evaluation, EvaluationError, always_reject
from pipeline import answer_question

RESULTS = Path(__file__).parent / "results"

# ---------- The test questions (matched to data/linkedin.txt and data/summary.txt) ----------
Q_EXISTING = "איפה את לומדת ובאיזה מסלול?"          # 1: the answer IS in the sources
Q_FOLLOW_1 = "מה עשית בשירות הצבאי?"                # 2: first question
Q_FOLLOW_2 = "ובאילו טכנולוגיות השתמשת שם?"         # 2: follow-up that only makes sense after question 1
Q_MISSING = "איזה ציון קיבלת בקורס למידת מכונה?"     # 3: NOT in the sources
Q_FLAWED = "אילו פרסים קיבלת?"                      # 4: the question for the flawed draft
FLAWED_DRAFT = "זכיתי בפרס נובל לפיזיקה בשנת 2020, ובנוסף קיבלתי את פרס ישראל על פרויקט הגמר שלי."  # 4: invented on purpose
Q_LIMIT = "מה התחביבים שלך?"                        # 5: any question; the mock rejects everything
# ---------------------------------------------------------------


def broken_evaluator(question, answer, history):
    """MOCK evaluator (no model call): returns invalid structured output, to test the error exit."""
    try:
        return Evaluation.model_validate_json('{"is_acceptable": "maybe"}')
    except ValidationError as e:
        raise EvaluationError(f"[MOCK] Evaluator output is not a valid Evaluation: {e.errors()[0]['msg']}") from e


def run(scenario_id, question, expected_end_state, history=None, min_attempts=1, **options):
    shown, record = answer_question(question, history or [], scenario_id=scenario_id, log_file=None, **options)
    record["expected_end_state"] = expected_end_state
    record["matches_expectation"] = (
        record["end_state"] == expected_end_state and len(record["attempts"]) >= min_attempts
    )
    mark = "OK" if record["matches_expectation"] else "CHECK THIS"
    print(f"{scenario_id}: {record['end_state']} after {len(record['attempts'])} attempt(s) "
          f"(expected {expected_end_state}) -> {mark}", flush=True)
    return record


print("=== Language-model scenarios ===")
llm = [run("1-existing-info", Q_EXISTING, "approved")]
first = run("2a-follow-up-first", Q_FOLLOW_1, "approved")
llm.append(first)
conversation = [{"role": "user", "content": Q_FOLLOW_1}, {"role": "assistant", "content": first["shown_to_user"]}]
llm.append(run("2b-follow-up-second", Q_FOLLOW_2, "approved", history=conversation))
llm.append(run("3-missing-info", Q_MISSING, "approved"))
llm.append(run("4-reject-and-improve", Q_FLAWED, "approved", min_attempts=2, first_draft=FLAWED_DRAFT))

print("\n=== Mock control-flow tests (no model decides) ===")
mock = [
    run("5-attempts-exhausted [MOCK]", Q_LIMIT, "attempts_exhausted", min_attempts=3, evaluator=always_reject),
    run("extra-technical-error [MOCK]", Q_LIMIT, "technical_error", evaluator=broken_evaluator),
]

RESULTS.mkdir(exist_ok=True)
(RESULTS / "llm_scenarios.json").write_text(json.dumps(llm, ensure_ascii=False, indent=2), encoding="utf-8")
(RESULTS / "mock_scenarios.json").write_text(json.dumps(mock, ensure_ascii=False, indent=2), encoding="utf-8")

lines = ["| Scenario | Mode | Attempts | End state | Expected | Matches |", "| --- | --- | --- | --- | --- | --- |"]
for mode, records in (("language model", llm), ("mock", mock)):
    for r in records:
        lines.append(f"| {r['scenario_id']} | {mode} | {len(r['attempts'])} | {r['end_state']} | "
                     f"{r['expected_end_state']} | {'yes' if r['matches_expectation'] else 'NO'} |")
(RESULTS / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\nSaved: results/llm_scenarios.json, results/mock_scenarios.json, results/summary.md")
