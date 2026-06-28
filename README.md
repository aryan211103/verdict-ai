# Verdict AI

**A football penalty simulator and VAR decision explainer — built on the principle that honest limitations make better software than confident fabrications.**

---

## The story

We started where most football AI projects start: penalty prediction. Could we use StatsBomb open data to build a model that tells you where a player tends to shoot?

We actually ran it. We scanned every free competition — 3,961 matches across 55 competition-seasons that contained at least one penalty kick — extracting 1,481 penalty kicks in total. Then we looked at the numbers honestly.

**The per-player data is non-representative by design.** StatsBomb's free tier follows club partnerships, not career coverage. Messi appears 83 times (15 La Liga seasons of Barcelona data). Ronaldo appears 23 times — mostly from one full season (2015/16) where La Liga happened to be fully released. A player's "tendency" in this dataset reflects which seasons StatsBomb happened to release, not how they actually kick. Building a per-player predictor on this would have been confident-sounding fiction.

**The base rate IS solid.** Across 328 international shootout kicks: 66.5% conversion overall. The pressure splits (kick order, ahead/behind, sudden death) all have overlapping confidence intervals — no detectable difference between them at this sample size. The honest finding is that the base rate is knowable and the fine-grained splits are not.

**Penalties are also a mixed-strategy game.** Both shooter and keeper benefit from varying their choices. A model that says "Messi shoots left 70% of the time" is exploitable by any keeper who reads it — which means any competent player already randomises against scouting. There is no prediction to make.

So we built two things that *are* truthful instead.

---

## Feature 1 — Penalty Shootout Simulator

A 1v1 or vs-AI penalty game grounded in the real distribution of penalty outcomes.

**The probability table** was derived from the observed 66.5% base rate:

| Keeper matched? | Shot placement | P(goal) |
|---|---|---|
| Matched | Corner (TL / TR / BL / BR) | **30%** |
| Matched | Side-mid (ML / MR) | 12% |
| Matched | Centre column | 6% |
| Mismatched | Corner | 95% |
| Mismatched | Side-mid | 92% |
| Mismatched | Centre | 85% |

Corners beat a correct dive ~30% of the time. Shooting centre and being matched is a 6% chance. Under uniform random play by both shooter and keeper, the probability table yields a 66.7% conversion rate — matching the observed real-world base rate. Centre is not the best strategy.

**Team and player selection is cosmetic by design.** Names populate the UI from a static squad list. They never enter the resolution function. There are automated tests that assert identical `p_goal` for the same shot placement regardless of which player name is attached. We built this constraint in deliberately because the alternative — faking per-player tendencies — would have been dishonest.

**The AI keeper** (vs-AI mode) uses a first-order Markov model + 50% random floor: it tracks what direction you tended to shoot *after* each of your previous shots this session, predicts your next shot from that, and mixes with uniform randomness. It learns your session habits, not fabricated data about a real player. It resists simple alternating patterns — the test suite asserts that alternating play (L→R→L→R) stays below ~78% conversion.

---

## Feature 2 — VAR / Decision Explainer

Ten landmark refereeing incidents — each explained using only the actual IFAB Laws of the Game.

The incidents include a mix of correct calls and refereeing errors (missed cards, incorrect sanctions). For errors, the explanation states what the law required and that the wrong outcome stood only because officials did not apply it — it never invents a legal justification for the incorrect outcome.

**The 10 incidents:**

| Incident | Call | Type |
|---|---|---|
| Suárez handball on goal line — WC 2010 QF | Red + penalty | Correct |
| Zidane headbutt — WC 2006 final | Red card | Correct |
| Keane serious foul play on Haaland — PL 2001 | Red card | Correct |
| Rooney stamp — WC 2006 QF | Red card | Correct |
| Di Canio pushes referee Alcock — PL 1998 | Red card | Correct |
| Henry handball (not penalised) — WC 2010 qualifier | Goal given | Error |
| Maradona "Hand of God" — WC 1986 QF | Goal given | Error |
| Tevez offside goal — WC 2010 R16 | Goal given | Error |
| Suárez bites Chiellini (not called) — WC 2014 | No action | Error — missed card |
| De Jong on Xabi Alonso (wrong card) — WC 2010 final | Yellow given | Error — insufficient sanction |

Every explanation is shown alongside the exact law text it was grounded in, so anyone can read both and audit the claim.

---

## IBM technology

### IBM Granite via watsonx.ai
Model: `ibm/granite-4-h-small`

Generates the VAR explanations. The model receives a system prompt that constrains it to cite only the injected IFAB law text — it is explicitly instructed not to state any rule not present in that text. The prompt branches on incident type: "correct call" explanations cite why the law required the decision; "error" explanations cite what the law actually requires and state that the wrong outcome stood only because officials did not apply it. Disciplinary error explanations are further constrained not to claim any goal was affected unless the offence directly caused or prevented one.

### IBM Docling
Used to parse the **IFAB Laws of the Game 2026/27** (the current edition, in force from 1 July 2026) from its published PDF into structured law chunks. Docling's `HybridChunker` was used to split the document into 383 section-level chunks with heading context. Each chunk is stored in `data/ifab/law_chunks.json` with its law number, heading, page number, and authoritative/appendix status. The PDF itself is not committed (it is copyrighted); only the parsed output is.

### IBM Context Forge (MCP gateway)
Exposes the penalty game backend as MCP tools:
- `create_shootout_session` — creates a game session (1v1 or vs-AI)
- `submit_kick` — resolves a kick given shot placement and dive direction
- `get_session_state` — returns current score and session state
- `delete_session` — cleans up

Tool schemas are defined in `backend/mcp/tools.py`. In vs-AI mode, `submit_kick` distinguishes two sub-cases by the presence of the `dive` field: absent → human is shooting, AI keeper picks dive automatically; present → AI is shooting (random target chosen by the frontend), human keeper supplies dive. The AI's own shots are not fed into the pattern model, so only human shot history informs the keeper's learning.

---

## How the grounding works

**Tag-based retrieval.** Each incident in `data/incidents.json` carries a `law_tags` field — a list of specific chunk IDs from `law_chunks.json`. At explanation time, `backend/services/rulebook.py` fetches those exact chunks and concatenates them into the law context injected into the Granite prompt. There is no fuzzy matching, no embeddings, no vector search. The retrieval is auditable: you can read the chunk IDs, look up the chunks, and confirm what law text Granite received.

**The sentinel guard.** If all chunk IDs in a `law_tags` list are missing from the parsed law file, `build_law_context()` returns the sentinel string `INSUFFICIENT_LAW_TEXT` rather than an empty string. `explain_incident()` catches this before making any API call and returns the refusal message: *"The law text for this incident could not be retrieved. No explanation is possible without the authoritative IFAB Laws."* The explanation service never falls back to Granite's own training knowledge about football rules.

**Cached and hand-verified.** The 10 explanations in `data/explanations.json` were generated, then read against the full injected law text in the session, incident by incident, before being written to the cache. The VAR explainer UI serves these cached explanations and shows the injected law text in the UI for every incident. No live Granite call is made in the normal demo flow.

---

## Setup

**Requirements:** Python 3.12+, Node 18+

**Environment variables** (copy `.env.example` to `.env`):
```
WATSONX_API_KEY=...
WATSONX_PROJECT_ID=...
WATSONX_URL=https://us-south.ml.cloud.ibm.com
```

**Backend**
```bash
pip install -r backend/requirements.txt   # or: pip install fastapi uvicorn python-dotenv ibm-watsonx-ai docling statsbombpy
python -m uvicorn backend.main:app --port 8000
```

**Frontend**
```bash
cd frontend && npm install && npm run dev
# Opens on http://localhost:5173
```

**Note:** The VAR explainer serves from the pre-built cache in `frontend/src/data/explanations.json` and works without the backend. The penalty game requires the backend for session management and kick resolution.

**Tests** (engine + API, no backend required):
```bash
python -m pytest tests/ -v
# 63 tests, all passing — covers probability table, AI keeper Markov logic,
# cosmetic guarantee (player names never affect p_goal), session lifecycle.
```

---

## What we didn't build (and why)

- **Per-player tendency analysis.** The data doesn't support it honestly.
- **Live 2026 scouting.** The IFAB Laws 2026/27 are used for legal grounding; the StatsBomb data used for the probability model ends before 2026.
- **A prediction tool.** Penalties are a mixed-strategy equilibrium. A model that outputs a recommended direction for either side is exploitable and misleading. The simulator never does this.
