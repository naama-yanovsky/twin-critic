"""Settings shared by every part of the app."""

from dotenv import load_dotenv

load_dotenv(override=True)  # reads OPENAI_API_KEY from the .env file

ACTOR_MODEL = "gpt-5.4-mini"      # writes the answers
EVALUATOR_MODEL = "gpt-5.4-mini"  # checks the answers
MAX_ATTEMPTS = 3                  # generation attempts per question, including the first
STATUS_PREFIX = "⚠️"              # marks system messages that are not real answers
