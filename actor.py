"""Part A: the Actor writes a candidate answer (and fixes it when the Evaluator rejects it)."""

from openai import OpenAI

from config import ACTOR_MODEL
from prompts import ACTOR_SYSTEM_PROMPT

client = OpenAI()


def generate_answer(question, history, rejected_answer=None, feedback=None):
    """Return a candidate answer.

    history: earlier messages as [{"role": "user" or "assistant", "content": "..."}].
    rejected_answer, feedback: given only when a previous attempt was rejected.
    """
    messages = [{"role": "system", "content": ACTOR_SYSTEM_PROMPT}] + history

    if rejected_answer is None:
        # First attempt: just the visitor's question
        messages.append({"role": "user", "content": question})
    else:
        # Revision: the same question, plus the rejected draft and the Evaluator's feedback
        messages.append({"role": "user", "content": f"""{question}

[Quality-check note, not written by the visitor]
Your previous draft answer to this question was rejected.
Rejected draft:
{rejected_answer}

Evaluator feedback:
{feedback}

Write a corrected answer to the visitor's question that fixes these problems.
Reply with the answer only."""})

    response = client.chat.completions.create(model=ACTOR_MODEL, messages=messages)
    answer = response.choices[0].message.content
    if not answer:
        raise RuntimeError("The Actor returned an empty answer")
    return answer
