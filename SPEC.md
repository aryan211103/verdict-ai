# Verdict AI — Specification
_Rewritten 2026-06-25. Previous direction deprecated (see bottom)._

---

## What This App Is

Two independent features in one app. **Feature 1 is built first, fully, before Feature 2 starts.**

---

## FEATURE 1 — Penalty Shootout Game

### Concept
An interactive penalty shootout. Two players on one device can replay or invent shootouts with recognisable team and player names. Team and player selection is **cosmetic only** — names are labels, not data sources.

### Honesty Rule (Feature 1)
The UI may say "relive and rewrite the moment." It must **never** claim predictive accuracy about real players or keepers. No per-player shooting stat appears anywhere. If player identity enters the resolution logic, stop and flag it.

---

### Team & Player Selection — COSMETIC ONLY

- User picks two national teams and a kick order of player names.
- Names, flags, and kit colours are shown for flavour.
- **Player choice has zero effect on game mechanics.** A player name is a button label, nothing more.
- No per-player data is loaded, stored, or faked.

**Presets (hardcoded):**

| Preset | Team A | Team B |
|---|---|---|
| 2022 World Cup Final | Argentina | France |
| 2021 Copa América Final | Argentina | Brazil |
| UEFA Euro 2020 Final | Italy | England |
| Custom | User types team names | User types player names |

Preset squads are a fixed hardcoded list of recognisable names. Free-play lets the user type whatever they like.

---

### Mode A — One v One (build first)

Two humans on one device, passing the screen between them.

**Turn structure:**
1. Shooter secretly picks a cell on the **3×3 goal grid**.
2. Keeper secretly picks a **dive direction**.
3. Choices are revealed simultaneously. Resolution rule applied. Outcome shown.
4. Full shootout: 5 kicks each (alternating), then sudden death under standard rules. Score tracked. Winner declared.

**Goal grid — shooter's perspective:**
```
[ TL ] [ TC ] [ TR ]
[ ML ] [ MC ] [ MR ]
[ BL ] [ BC ] [ BR ]
```
T = top, M = middle, B = bottom, L = left, C = centre, R = right.
All from the **shooter's viewpoint** looking at the goal.

**Keeper dive:** L / C / R, also from the **shooter's viewpoint**
(keeper dives to shooter's left, centre, or right).

**Grid and dive design — confirmed deliberate:**
- Shooter picks 1 of 9 cells (3×3).
- Keeper picks one of 3 horizontal directions (L / C / R) only.
- Only horizontal thirds are compared for match/mismatch. Keeper has no fine-grained vertical control in the fraction of a second available — this matches how real penalty saves work.
- Height influences the outcome through the shot's cell classification (corner vs side-mid vs centre) — captured in the probability table, not in a separate keeper vertical choice.

**Resolution logic (exact, documented):**

Step 1 — Classify the shot's horizontal zone:
- L if cell is TL, ML, or BL.
- C if cell is TC, MC, or BC.
- R if cell is TR, MR, or BR.

Step 2 — Determine match: keeper's dive direction equals shot's horizontal zone.

Step 3 — Classify the cell type (affects probability):
- **Corner**: TL, TR, BL, BR (horizontal side + extreme vertical).
- **Side-mid**: ML, MR (horizontal side + middle height).
- **Centre col**: TC, MC, BC (any height, centre horizontal).

Step 4 — Apply probability table:

| Dive match? | Cell type | P(Goal) | P(Save) |
|---|---|---|---|
| **Matched** | Corner (TL, TR, BL, BR) | **0.30** | 0.70 |
| **Matched** | Side-mid (ML, MR) | **0.12** | 0.88 |
| **Matched** | Centre col (TC, MC, BC) | **0.06** | 0.94 |
| **Mismatched** | Corner | **0.95** | 0.05 |
| **Mismatched** | Side-mid | **0.92** | 0.08 |
| **Mismatched** | Centre col | **0.85** | 0.15 |

Step 5 — Draw a single weighted random number. Resolve. No other data enters.

_Rationale and simulation results (100 000 kicks each):_
- _Corners vs uniform keeper: 73.5% — best strategy._
- _Side-mid vs uniform keeper: 65.3% — middle._
- _Centre-only vs uniform keeper: 58.6% — worst strategy, not dominant._
- _Both players mixing uniformly: 66.7% ≈ 67%._
- _Nash equilibrium value (both mixing optimally): 67.0%._
- _Centre mismatch is 0.85 (not 0.90) because a keeper who dives to the side can sometimes reach a centre-column ball even from the wrong direction. This prevents centre from becoming a free-scoring shot when the keeper guesses wrong, which would otherwise make centre weakly dominant._

---

### Mode B — vs AI Keeper (build after Mode A is complete)

User shoots; AI plays keeper.

**What the AI uses:**
1. A **mixed-strategy baseline** so it cannot be trivially exploited.
2. **In-session adaptation**: it tracks where _this user_ has shot _during this game_ and shifts probabilities toward the user's observed habit. It has no memory between games.

**What the AI never uses:** any real player's shooting data, external statistics, or anything other than the current session's shot history.

**Why first-order Markov, not frequency counting:**
Pure frequency counting is trivially beaten by simple alternating (L→R→L→R). After many alternating kicks, frequency = {L:50%, R:50%}, so the AI spreads evenly across L and R. The shooter always picks the direction the AI least recently weighted, getting ~84% conversion — far above Nash equilibrium.

The Markov approach tracks *what direction followed each previous shot*. After L→R→L→R, the AI learns that after L comes R and after R comes L. It predicts the next shot based on the last shot and dives accordingly. Simple alternating then yields ~52% conversion (below Nash equilibrium of 67%) — the user is genuinely incentivised to mix.

**AI dive algorithm — exact:**

```
# State per game session (reset on new game):
transitions = {
  'L': {'L': 0, 'C': 0, 'R': 0},
  'C': {'L': 0, 'C': 0, 'R': 0},
  'R': {'L': 0, 'C': 0, 'R': 0},
}
history = []          # horizontal directions this session
RANDOM_FLOOR = 0.50
uniform = {L: 1/3, C: 1/3, R: 1/3}

Before each kick:
  if history is empty:
    p_dive = uniform

  else:
    last = history[-1]
    counts = transitions[last]        # what user shot AFTER 'last', historically
    total  = sum(counts.values())

    if total == 0:                    # no data yet after this direction
      markov_pred = uniform
    else:
      markov_pred = {d: counts[d] / total for d in L, C, R}

    p_dive = 0.5 × uniform + 0.5 × markov_pred

  Sample dive direction from p_dive.

After kick resolves (shot direction known):
  if history is not empty:
    transitions[history[-1]][shot_direction] += 1
  history.append(shot_direction)
```

**Beatable by design:** The 50% random floor means the AI is never deterministic. A user who randomises their own shots achieves the Nash equilibrium of ~67%. A user who uses a fixed pattern (repeat, alternate, always-corner) achieves less. The AI text in the UI: _"I watch where you shot and what you did next — but I'm still half-guessing."_

---

### Feature 1 Build Order

| Step | Deliverable | Pause? |
|---|---|---|
| 1a | Game engine (resolution + AI logic), pure Python, tested | — |
| 1b | FastAPI session endpoints + Context Forge MCP tools | — |
| 1c | Frontend: Mode A (grid, keeper picker, reveal, scoreboard) | **Review** |
| 1d | Frontend: Mode B (AI keeper mode) | **Review** |

---

## FEATURE 2 — VAR / Decision Explainer

_Build only after Feature 1 is complete and approved._

### Concept
A library of real, well-known refereeing incidents (hardcoded text descriptions). The user picks an incident and asks why the call was what it was. Granite explains in plain language, **grounded in the actual IFAB Laws of the Game**.

### What It Does
- User selects a named incident from a curated list (e.g. "Suárez handball, WC 2010 quarter-final").
- User asks a question about the call (e.g. "Why wasn't that a red card straight away?").
- Granite answers, citing specific IFAB Law clauses by number and text.

### What It Does NOT Do
- It does not watch video or analyse footage.
- It does not rule on incidents the user submits; it only explains pre-curated ones.
- This limit is stated explicitly in the UI: _"This tool explains selected incidents using the Laws of the Game. It does not adjudicate new incidents or watch video."_

### IBM Docling Integration (required, not placeholder)
- The IFAB Laws of the Game PDF is parsed using **Docling** into structured text.
- Granite receives the relevant law sections as context when generating an explanation.
- This is a real integration: Docling extracts text → stored locally → retrieved at query time → injected into the Granite prompt.
- Do NOT use Docling for any other document. Do NOT skip it and paste law text manually.

### Incident Library (hardcoded)
A minimum of 8 curated incidents covering a range of Laws (handball, DOGSO, offside, simulation, VAR procedure, etc.). Each entry has: incident name, match context, what the call was, brief factual description of what happened. Granite does the explaining; the app provides the facts.

### Feature 2 Build Order

| Step | Deliverable | Pause? |
|---|---|---|
| 2a | Docling parse of IFAB PDF → structured local text | **Review** |
| 2b | Incident library (hardcoded JSON) | — |
| 2c | Granite explanation service with law retrieval | **Review** |
| 2d | Frontend: incident picker + question input + explanation panel | **Review** |

---

## Tech Stack

| Layer | Choice |
|---|---|
| Backend | Python, FastAPI |
| Frontend | React + Vite |
| AI explanations | IBM Granite via watsonx.ai (env vars, never hardcoded) |
| Rulebook parsing | Docling (Feature 2 only) |
| MCP gateway | IBM Context Forge |

Secrets via `.env` only. Never hardcoded.

---

## How to Work

- Targeted edits, not rewrites. Ask before changing architecture.
- Never fabricate data, stats, or player tendencies.
- Never connect player identity to resolution logic or AI behaviour.
- After each pause point, wait for explicit approval before continuing.

---

## DEPRECATED — Previous Direction (2026-06-25)

The original project was a StatsBomb data explainer with per-player placement tendencies and population pressure stats. That work is kept on disk but is **no longer the product direction**.

**Deprecated files (do not delete, do not build on):**
- `data/kicks.json` — StatsBomb penalty kick extraction
- `data/shootouts_index.json` — shootout match index
- `data/aggregations/pressure_stats.json` — population pressure statistics
- `data/SCHEMA.md` — StatsBomb field schema
- `backend/services/aggregations.py` — Wilson CI and pressure stat functions
- `scripts/explore_data.py` — StatsBomb scan script
- `scripts/build_pressure_stats.py` — pressure stat builder

**Why deprecated:** Per-player tendency data was non-representative (shaped by StatsBomb's release choices, not players' careers). The pressure stats (67% base rate, all pairwise CIs overlapping) were honest findings but not a compelling product for a general audience. The project pivoted to a game + rules explainer format.

**What remains valid from the old work:**
- The direction convention (GK perspective), the honesty principles, and the Wilson CI overlap test are good engineering; carry them forward if they become relevant in Feature 2's explanation layer.
- The StatsBomb data and scripts are complete and correct; they simply aren't the product anymore.
