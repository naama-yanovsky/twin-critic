"""Part C: the generate -> evaluate -> revise loop, with one log entry per question."""

import json
from datetime import datetime
from pathlib import Path

from actor import generate_answer
from config import MAX_ATTEMPTS, STATUS_PREFIX
from evaluator import evaluate

LOG_FILE = Path(__file__).parent / "logs" / "chat_log.jsonl"

# The three ways a question can end
APPROVED = "approved"
EXHAUSTED = "attempts_exhausted"
ERROR = "technical_error"

MSG_EXHAUSTED = f"{STATUS_PREFIX} לא התקבלה תשובה מאושרת במסגרת מגבלת שלושת הניסיונות. אפשר לנסח את השאלה אחרת."
MSG_ERROR = f"{STATUS_PREFIX} אירעה שגיאה טכנית, ולכן לא הוצגה תשובה. הסיבה נשמרה ביומן הבדיקה."


def text_of(content):
    """Gradio may store a message as plain text or as a list of text parts."""
    if isinstance(content, list):
        return " ".join(part.get("text", "") for part in content if isinstance(part, dict))
    return content or ""


def as_messages(history):
    """Gradio gives the history either as message dicts or (older versions) as [user, bot] pairs."""
    messages = []
    for m in history or []:
        if isinstance(m, dict):
            messages.append(m)
        elif isinstance(m, (list, tuple)) and len(m) == 2:
            if m[0]:
                messages.append({"role": "user", "content": m[0]})
            if m[1]:
                messages.append({"role": "assistant", "content": m[1]})
    return messages


def clean_history(history):
    """Keep only user messages and approved answers, as plain {role, content} pairs."""
    cleaned = []
    for m in as_messages(history):
        role, content = m.get("role"), text_of(m.get("content"))
        if role == "assistant" and content.startswith(STATUS_PREFIX):
            continue  # a status message is not an answer, so the models should not see it
        if role in ("user", "assistant"):
            cleaned.append({"role": role, "content": content})
    return cleaned


def answer_question(question, history, scenario_id="chat", evaluator=evaluate, first_draft=None, log_file=LOG_FILE):
    """Run the loop for one question. Returns (text to show the user, log record)."""
    history = clean_history(history)
    record = {
        "scenario_id": scenario_id,
        "time": datetime.now().isoformat(timespec="seconds"),
        "question": question,
        "attempts": [],
        "end_state": None,
        "shown_to_user": None,
        "error": None,
    }
    rejected_answer, feedback = None, None

    for attempt in range(1, MAX_ATTEMPTS + 1):  # a new question always starts again from 1
        step = {
            "attempt": attempt,
            "source": "actor",
            "candidate_answer": None,
            "evaluation_completed": False,
            "is_acceptable": None,
            "feedback": None,
        }
        record["attempts"].append(step)

        # 1. Generate: the Actor writes an answer (or we inject a flawed test draft, scenario 4)
        try:
            if attempt == 1 and first_draft is not None:
                answer = first_draft
                step["source"] = "injected_test_draft"
            else:
                answer = generate_answer(question, history, rejected_answer, feedback)
        except Exception as e:
            return finish(record, ERROR, MSG_ERROR, f"Actor call failed: {e}", log_file)
        step["candidate_answer"] = answer

        # 2. Evaluate: the Critic returns a validated Evaluation, or the evaluation is not completed
        try:
            result = evaluator(question, answer, history)
        except Exception as e:
            return finish(record, ERROR, MSG_ERROR, str(e), log_file)
        step["evaluation_completed"] = True
        step["is_acceptable"] = result.is_acceptable
        step["feedback"] = result.feedback

        # 3. Approved: show this answer and stop
        if result.is_acceptable:
            return finish(record, APPROVED, answer, None, log_file)

        # 4. Rejected: the next attempt receives the rejected answer and the feedback
        rejected_answer, feedback = answer, result.feedback

    # 5. All attempts were rejected: show a limit message, never a rejected answer
    return finish(record, EXHAUSTED, MSG_EXHAUSTED, None, log_file)


def finish(record, end_state, shown, error, log_file):
    record["end_state"] = end_state
    record["shown_to_user"] = shown
    record["error"] = error
    if log_file:
        log_file.parent.mkdir(exist_ok=True)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return shown, record
