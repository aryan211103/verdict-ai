"""
Granite explanation service — Feature 2 (VAR/Decision Explainer).

Calls IBM Granite via watsonx.ai using the chat API (text_chat function).
Credentials loaded exclusively from environment variables — never hardcoded.

Model: ibm/granite-4-h-small — the active Granite 4 model on this instance,
confirmed to have text_chat + text_generation + retrieval_augmented_generation.

Free-tier concurrency limit: 10 simultaneous requests. Calls within the same
process that fire rapidly will hit 429. The retry-with-backoff in _chat_with_retry
handles this automatically — space calls at least 5 s apart for best results.

Grounding contract (enforced in Python + prompt):
- Granite must cite ONLY clauses from the injected IFAB law text.
- If build_law_context returns INSUFFICIENT_LAW_TEXT, explain_incident returns
  a refusal before making any API call.
- No directional recommendations for either side.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

MODEL_ID     = "ibm/granite-4-h-small"
INSUFFICIENT = "INSUFFICIENT_LAW_TEXT"
_MAX_RETRIES = 4
_BASE_WAIT   = 12   # seconds; each retry doubles: 12, 24, 48, 96

# ── Prompts (branched by call_type) ──────────────────────────────────────────
#
# "correct": the officials applied the Laws accurately — explain why each part
#            of the call was required by the provided law text.
#
# "error":   the officials missed or misapplied the Laws — explain what the
#            Laws actually say, state that the outcome should have been
#            different, and make clear it stood ONLY because it was not seen
#            or penalised. Do NOT invent any legal justification for the result.

_SYSTEM_BASE = """\
You are a football referee decision explainer. Your ONLY source of law is the \
IFAB Laws of the Game text that the user provides. Do not recall, paraphrase, \
or add any rule that is not explicitly stated in that text.

Rules you must follow without exception:
1. Cite the specific clauses from the provided law text by quoting key phrases.
2. Do not recommend what any player, keeper, or referee should do differently.
3. Do not state any rule that is not in the provided law text.
4. Write 200–280 words in plain English for a general audience.\
"""

_SYSTEM_CORRECT = (
    _SYSTEM_BASE + "\n\n"
    "5. The call described was legally correct. Explain why every part of the "
    "call — each sanction, each award — was required or permitted by the "
    "specific clauses in the provided law text. Address each component of the "
    "call in turn."
)

_SYSTEM_ERROR = (
    _SYSTEM_BASE + "\n\n"
    "5. IMPORTANT: The call described was a referee ERROR. The outcome only "
    "stood because the officials did not see or penalise the offence — NOT "
    "because the Laws permitted it. You must:\n"
    "   a. Quote the specific clauses that apply to what physically happened.\n"
    "   b. State clearly that under those clauses this constituted an offence "
    "and the goal should have been disallowed (or the correct sanction applied).\n"
    "   c. State that the goal stood only because the offence was not seen by "
    "the officials.\n"
    "   d. Do NOT invent any legal justification for the goal standing. "
    "There is none in the Laws."
)

_USER = """\
IFAB LAWS OF THE GAME (relevant sections):
{law_context}

INCIDENT:
{what_happened}
Call made: {call}

{task}\
"""

_TASK_CORRECT = (
    "Explain, using the law text above and quoting key clauses, why the Laws "
    "required or permitted every part of this call."
)

_TASK_ERROR = (
    "Using the law text above and quoting key clauses, explain what the Laws "
    "actually say applies to this incident, state that the goal should have "
    "been disallowed under those Laws, and explain that it stood only because "
    "the officials did not see or penalise the offence."
)


# ── Watsonx.ai client + retry ─────────────────────────────────────────────────

def _get_model():
    from ibm_watsonx_ai import Credentials
    from ibm_watsonx_ai.foundation_models import ModelInference

    credentials = Credentials(
        url     = os.environ["WATSONX_URL"],
        api_key = os.environ["WATSONX_API_KEY"],
    )
    return ModelInference(
        model_id   = MODEL_ID,
        credentials= credentials,
        project_id = os.environ["WATSONX_PROJECT_ID"],
    )


def _chat_with_retry(messages: list[dict], params: dict) -> dict:
    """Call model.chat with exponential backoff on 429."""
    import warnings
    model = _get_model()
    wait  = _BASE_WAIT

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                return model.chat(messages=messages, params=params)
        except Exception as exc:
            is_429 = "429" in str(exc) or "consumption_limit" in str(exc)
            if is_429 and attempt < _MAX_RETRIES:
                print(f"  [429] concurrency limit — waiting {wait}s (attempt {attempt}/{_MAX_RETRIES})")
                time.sleep(wait)
                wait *= 2
                model = _get_model()   # fresh client after wait
            else:
                raise

    raise RuntimeError("Max retries exceeded")   # unreachable but satisfies type checkers


# ── Public interface ──────────────────────────────────────────────────────────

def explain_incident(incident: dict, law_context: str) -> dict:
    """
    Explain a refereeing incident grounded in the provided IFAB law text.

    Returns:
        {
          "explanation":      str,   # Granite's response text
          "law_context_used": str,   # exact text injected into the prompt
          "model_id":         str,
          "refused":          bool,
        }
    """
    # Guard: return refusal before any API call when law text is missing.
    if law_context == INSUFFICIENT:
        return {
            "explanation": (
                "The law text for this incident could not be retrieved. "
                "No explanation is possible without the authoritative IFAB Laws."
            ),
            "law_context_used": law_context,
            "model_id":         MODEL_ID,
            "refused":          True,
        }

    call_type = incident.get("call_type", "correct")
    system    = _SYSTEM_ERROR   if call_type == "error" else _SYSTEM_CORRECT
    task      = _TASK_ERROR     if call_type == "error" else _TASK_CORRECT

    user_msg = _USER.format(
        law_context  = law_context,
        what_happened= incident["what_happened"],
        call         = incident["call"],
        task         = task,
    )

    messages = [
        {"role": "system", "content": system},
        {"role": "user",   "content": user_msg},
    ]

    result = _chat_with_retry(
        messages,
        params={
            "max_new_tokens":     600,
            "temperature":        0.2,
            "repetition_penalty": 1.05,
        },
    )

    if isinstance(result, dict):
        explanation = result["choices"][0]["message"]["content"].strip()
    else:
        explanation = str(result).strip()

    return {
        "explanation":      explanation,
        "law_context_used": law_context,
        "model_id":         MODEL_ID,
        "refused":          False,
    }
