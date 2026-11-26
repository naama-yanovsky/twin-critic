"""Part B: the Evaluator (Critic) checks a candidate answer and returns structured output."""

from openai import OpenAI
from pydantic import BaseModel, ValidationError

from config import EVALUATOR_MODEL
from prompts import BACKGROUND, EVALUATOR_SYSTEM_PROMPT

client = OpenAI()


class Evaluation(BaseModel):
    is_acceptable: bool  # the decision
    feedback: str        # the reason; when rejecting, what to fix and how


class EvaluationError(Exception):
    """The evaluation was not completed: the call failed or the output was not a valid Evaluation."""


def format_history(history):
    if not history:
        return "(no earlier messages)"
    return "\n".join(f"{m['role']}: {m['content']}" for m in history)


def build_evaluator_message(question, answer, history):
    """The User Evaluator message: everything the Evaluator needs in order to judge."""
    return f"""# Background sources
{BACKGROUND}

# Conversation so far
{format_history(history)}

# Visitor's question
{question}

# Candidate answer to evaluate
{answer}

Evaluate the candidate answer against criteria A-D."""


def evaluate(question, answer, history):
    """Return a validated Evaluation, or raise EvaluationError."""
    messages = [
        {"role": "system", "content": EVALUATOR_SYSTEM_PROMPT},
        {"role": "user", "content": build_evaluator_message(question, answer, history)},
    ]
    try:
        # client.chat.completions.parse in new openai versions, client.beta.chat... in older ones
        completions = client.chat.completions if hasattr(client.chat.completions, "parse") else client.beta.chat.completions
        response = completions.parse(model=EVALUATOR_MODEL, messages=messages, response_format=Evaluation)
        raw = response.choices[0].message.content  # the JSON text the model wrote
        return Evaluation.model_validate_json(raw)  # our own check against the schema
    except ValidationError as e:
        raise EvaluationError(f"Evaluator output is not a valid Evaluation: {e.errors()[0]['msg']}") from e
    except Exception as e:
        raise EvaluationError(f"Evaluator call failed: {e}") from e


def always_reject(question, answer, history):
    """MOCK evaluator (no model call): rejects every answer. Used only to test the attempt limit."""
    return Evaluation(is_acceptable=False, feedback="[MOCK] Rejected on purpose to test the attempt limit.")
