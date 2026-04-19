"""
llm_model_config.py
-------------------
Central source of truth for which OpenAI model the app uses.

Controlled by env vars:
  OPENAI_PRIMARY_MODEL   (default: "gpt-5.2")
  OPENAI_FALLBACK_MODEL  (default: "gpt-4o")

Why this exists:
  In Feb 2026 OpenAI started returning 502 Bad Gateway for `gpt-5.2` on
  and off. We don't want to hard-code a model in 15+ call sites. Using
  env vars means when OpenAI stabilises we flip OPENAI_PRIMARY_MODEL
  back to "gpt-5.2" in backend/.env and restart — no code change.
"""
import os


def get_primary_model() -> str:
    """Returns the current primary OpenAI model name (env-driven)."""
    return os.environ.get("OPENAI_PRIMARY_MODEL", "gpt-5.2")


def get_fallback_model() -> str:
    """Returns the fallback OpenAI model used on 502/timeout."""
    return os.environ.get("OPENAI_FALLBACK_MODEL", "gpt-4o")
