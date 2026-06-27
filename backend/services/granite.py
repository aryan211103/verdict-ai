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
# call_type / error_type branching:
#
# "correct"  — officials applied the Laws accurately.
#
# "error" with error_type "goal_affecting"  — the error wrongly allowed or
#              disallowed a goal. Explain what the Laws say, state the goal
#              should/should not have stood, and that it stood only because
#              officials missed it.
#
# "error" with error_type "disciplinary"    — the error was a missed or
#              insufficient card/sanction (e.g. yellow when red was required,
#              or nothing when a red was required). Explain the correct sanction
#              under the Laws. Do NOT claim any goal was disallowed or match
#              result affected unless the offence directly caused or prevented
#              a goal. The focus is on what card should have been shown and why.

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

_SYSTEM_ERROR_GOAL = (
    _SYSTEM_BASE + "\n\n"
    "5. IMPORTANT: The call described was a referee ERROR that wrongly allowed "
    "or disallowed a goal. You must:\n"
    "   a. Quote the specific clauses that apply to what physically happened.\n"
    "   b. State clearly that under those clauses this constituted an offence "
    "and the goal should have been disallowed (or vice versa).\n"
    "   c. State that the goal stood only because the offence was not seen "
    "or penalised by the officials.\n"
    "   d. Do NOT invent any legal justification for the incorrect outcome."
)

_SYSTEM_ERROR_DISCIPLINARY = (
    _SYSTEM_BASE + "\n\n"
    "5. IMPORTANT: The call described was a referee ERROR — either a missed card "
    "or an insufficient sanction (e.g. a yellow shown when the Laws required a "
    "red, or no action taken when a sending-off was required). You must:\n"
    "   a. Quote the specific clauses that apply to what physically happened.\n"
    "   b. State clearly what the correct sanction should have been under the "
    "Laws and that it was not applied.\n"
    "   c. State that the incorrect outcome was due to the officials not "
    "recognising or applying the correct sanction.\n"
    "   d. Do NOT claim that any goal was disallowed or that the match result "
    "was affected UNLESS the offence directly caused or prevented a goal — "
    "an off-ball sending-off offence does not disallow goals already scored."
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

_TASK_ERROR_GOAL = (
    "Using the law text above and quoting key clauses, explain what the Laws "
    "actually say applies to this incident, state that the goal should have "
    "been disallowed under those Laws, and explain that it stood only because "
    "the officials did not see or penalise the offence."
)

_TASK_ERROR_DISCIPLINARY = (
    "Using the law text above and quoting key clauses, explain what the correct "
    "sanction should have been under the Laws (stating which specific clause "
    "requires it), and state that the correct sanction was not applied. "
    "Do NOT assert that any goal was disallowed or that the match result was "
    "affected unless the offence directly caused or prevented a goal."
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

    call_type  = incident.get("call_type",  "correct")
    error_type = incident.get("error_type", "goal_affecting")   # default = old behaviour

    if call_type != "error":
        system = _SYSTEM_CORRECT
        task   = _TASK_CORRECT
    elif error_type == "disciplinary":
        system = _SYSTEM_ERROR_DISCIPLINARY
        task   = _TASK_ERROR_DISCIPLINARY
    else:
        system = _SYSTEM_ERROR_GOAL
        task   = _TASK_ERROR_GOAL

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
