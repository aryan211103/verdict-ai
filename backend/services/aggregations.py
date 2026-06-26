"""
Aggregation functions shared by the build scripts and the FastAPI app.

Honesty contract (enforced here, not left to callers):
  - wilson_ci() returns None bounds when n < MIN_N so callers cannot accidentally
    display a CI on an insufficient sample.
  - Every public function returns sample size (n) alongside any rate.
  - Nothing here recommends a direction for keeper or taker.
"""

import json
import math
from collections import defaultdict
from pathlib import Path

MIN_N = 5   # honesty floor: below this, no CI is returned

DATA_DIR = Path(__file__).parent.parent.parent / "data"

# ── Competition buckets ───────────────────────────────────────────────────────
#
# INTERNATIONAL_TOURNAMENTS: national-team knockout competitions.
#   Used for: shootout pressure stats, hero demos, shootout index.
#
# Everything else (Champions League, Indian Super League, domestic leagues)
#   feeds ONLY the per-player placement pool and the in-game penalty backdrop.
#
# An ISL or UCL shootout must never sit in the same pressure-stats bucket
# as a World Cup shootout. This set is the single definition — never inline it.

INTERNATIONAL_TOURNAMENTS: frozenset[str] = frozenset({
    "FIFA World Cup",
    "Women's World Cup",
    "FIFA U20 World Cup",
    "UEFA Euro",
    "UEFA Women's Euro",
    "Copa America",
    "African Cup of Nations",
})


def is_international(kick: dict) -> bool:
    """True if this kick belongs to a national-team international tournament."""
    return kick.get("competition") in INTERNATIONAL_TOURNAMENTS


# ── Interpretation rule (enforced here; re-stated in every Granite prompt) ────
#
# When two Wilson CIs overlap, the finding is "no statistically detectable
# difference." The point gap is never narrated.  A rate is "weakly suggestive"
# only when CIs do not overlap AND the sample is meaningful. These constants
# and the cis_overlap() function are the canonical implementation of that rule.

def cis_overlap(lo1, hi1, lo2, hi2) -> bool | None:
    """
    True  → CIs overlap  → report "no statistically detectable difference."
    False → CIs do not overlap → may say "weakly suggestive, not conclusive."
    None  → at least one CI is unavailable (n < MIN_N); report as indeterminate.
    """
    if any(v is None for v in (lo1, hi1, lo2, hi2)):
        return None
    return not (hi1 < lo2 or hi2 < lo1)


def overlap_label(overlaps: bool | None) -> str:
    if overlaps is None:
        return "indeterminate — one or both samples below honesty floor"
    if overlaps:
        return "no statistically detectable difference (CIs overlap)"
    return "weakly suggestive — CIs do not overlap, but treat with caution"


# ── Wilson score interval ─────────────────────────────────────────────────────

def wilson_ci(successes: int, n: int, z: float = 1.96):
    """
    95% Wilson score confidence interval for a proportion.

    Returns (rate, lo, hi).  Returns (rate, None, None) when n < MIN_N so the
    UI can show "insufficient data" instead of a misleading narrow interval.
    """
    if n == 0:
        return None, None, None
    p = successes / n
    if n < MIN_N:
        return round(p, 4), None, None   # rate known but CI withheld
    denom  = 1 + z ** 2 / n
    center = (p + z ** 2 / (2 * n)) / denom
    margin = (z * math.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2))) / denom
    return round(p, 4), round(max(0.0, center - margin), 4), round(min(1.0, center + margin), 4)


def _summary(kicks: list, label: str) -> dict:
    """Produce a single rate record for a list of kicks."""
    n       = len(kicks)
    goals   = sum(1 for k in kicks if k.get("outcome") == "Goal")
    rate, lo, hi = wilson_ci(goals, n)
    return {
        "label":     label,
        "n":         n,
        "goals":     goals,
        "rate":      rate,
        "wilson_lo": lo,
        "wilson_hi": hi,
        "ci_note":   (
            f"95% Wilson CI, n={n}"
            if n >= MIN_N and lo is not None
            else f"n={n} — below honesty floor ({MIN_N}); CI not shown"
        ),
    }


# ── Step 2b: population pressure stats ───────────────────────────────────────

# Sudden death starts after 5 kicks per team (kick_order > 10 in alternating seq)
_SD_THRESHOLD = 10


def build_pressure_stats(shootout_kicks: list) -> dict:
    """
    Compute population-level pressure stats for shootout kicks.

    Input:  list of kick dicts (is_shootout == True, from kicks.json).
    Output: dict ready to serialise as pressure_stats.json.

    These stats describe base rates across all historical shootouts.
    They do NOT predict outcomes or recommend directions.
    """
    # ── By kick order (1–10 individually, then SD bucket) ────────────────────
    order_buckets: dict = defaultdict(list)
    for k in shootout_kicks:
        ko = k.get("kick_order")
        if ko is None:
            continue
        key = int(ko) if int(ko) <= _SD_THRESHOLD else "SD"
        order_buckets[key].append(k)

    by_kick_order = []
    for key in sorted(order_buckets, key=lambda x: (x == "SD", x)):
        by_kick_order.append(_summary(order_buckets[key], str(key)))

    # ── By score state (ahead / level / behind) ───────────────────────────────
    state_buckets: dict = defaultdict(list)
    for k in shootout_kicks:
        state = k.get("shootout_score_state")
        if state:
            state_buckets[state].append(k)

    by_score_state = [
        _summary(state_buckets.get(s, []), s)
        for s in ("ahead", "level", "behind")
    ]

    # ── Sudden death vs regular ───────────────────────────────────────────────
    sd_kicks  = [k for k in shootout_kicks if (k.get("kick_order") or 0) > _SD_THRESHOLD]
    reg_kicks = [k for k in shootout_kicks
                 if k.get("kick_order") and int(k["kick_order"]) <= _SD_THRESHOLD]

    sd_vs_regular = [
        _summary(reg_kicks, "regular_rounds"),
        _summary(sd_kicks,  "sudden_death"),
    ]

    # ── Pairwise overlap flags (the canonical signal for Granite) ────────────
    # Granite receives these booleans, not raw rates, as the primary signal
    # about whether a difference exists between groups.
    def _row(rows, label):
        return next((r for r in rows if r["label"] == label), None)

    def _overlap_pair(a, b):
        if a is None or b is None:
            return None
        return cis_overlap(a["wilson_lo"], a["wilson_hi"], b["wilson_lo"], b["wilson_hi"])

    ahead  = _row(by_score_state, "ahead")
    level  = _row(by_score_state, "level")
    behind = _row(by_score_state, "behind")
    reg    = sd_vs_regular[0]
    sd     = sd_vs_regular[1]

    pairwise_overlap = {
        "ahead_vs_level":    {
            "overlaps": _overlap_pair(ahead, level),
            "interpretation": overlap_label(_overlap_pair(ahead, level)),
        },
        "ahead_vs_behind":   {
            "overlaps": _overlap_pair(ahead, behind),
            "interpretation": overlap_label(_overlap_pair(ahead, behind)),
        },
        "level_vs_behind":   {
            "overlaps": _overlap_pair(level, behind),
            "interpretation": overlap_label(_overlap_pair(level, behind)),
        },
        "sd_vs_regular":     {
            "overlaps": _overlap_pair(sd, reg),
            "interpretation": overlap_label(_overlap_pair(sd, reg)),
        },
    }

    return {
        "overall":                 _summary(shootout_kicks, "all_shootout_kicks"),
        "by_kick_order":           by_kick_order,
        "by_score_state":          by_score_state,
        "sudden_death_vs_regular": sd_vs_regular,
        "pairwise_overlap":        pairwise_overlap,
        "_sd_threshold":           _SD_THRESHOLD,
    }


# ── Step 2a stub (not built yet — awaiting taker count approval) ──────────────

def build_taker_tendency(taker_id: int, all_kicks: list) -> dict:
    """
    Placeholder — not implemented.
    Will pool ALL competitions for the given taker, return placement
    distribution with Wilson CIs (or insufficient-data message below MIN_N).
    """
    raise NotImplementedError("Step 2a not yet approved — awaiting taker count review.")


# ── Loader ────────────────────────────────────────────────────────────────────

def load_kicks() -> list:
    path = DATA_DIR / "kicks.json"
    if not path.exists():
        raise FileNotFoundError(f"kicks.json not found at {path}")
    with open(path) as f:
        return json.load(f)
