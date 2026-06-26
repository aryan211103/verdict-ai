#!/usr/bin/env python3
"""
Step 1 — Data exploration.

Scans every free StatsBomb competition, extracts every penalty kick
(period-5 shootout + in-game), writes:
    data/kicks.json           one record per kick
    data/shootouts_index.json one record per shootout match

Prints per-competition counts so we can verify the data before building on it.

Usage:
    python scripts/explore_data.py               # all competitions
    python scripts/explore_data.py --resume      # skip already-cached matches
    python scripts/explore_data.py --intl-only   # international/cup comps only (fast)

Column notes (verified against statsbombpy 1.19, open data format):
    type, shot_type, shot_outcome, team, player  → already flat strings
    player_id, team_id                           → numeric
    shot_end_location                            → list [x, y] or [x, y, z]
    goalkeeper_end_location                      → NaN for penalty events in free data
    goalkeeper_body_part                         → best available proxy for dive direction
    related_events                               → list of UUID strings
    id                                           → UUID string
"""

import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

try:
    from statsbombpy import sb
except ImportError:
    sys.exit("statsbombpy not found. Install: pip install statsbombpy")

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT      = Path(__file__).parent.parent
DATA_DIR  = ROOT / "data"
CACHE_DIR = DATA_DIR / ".cache"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ── Goal geometry ─────────────────────────────────────────────────────────────
# StatsBomb pitch: 120 × 80, attacks always left → right.
# Goal: y ∈ [36, 44], height 0 – 2.44 m.
#
# ALL direction labels are from the GOALKEEPER's perspective (facing the taker):
#   GK's right = lower  y  (= attacker's left)
#   GK's left  = higher y  (= attacker's right)
#
# Horizontal split: goal width (8 m) into three equal thirds.
GOAL_Y_MIN    = 36.0
GOAL_Y_MAX    = 44.0
THIRD         = (GOAL_Y_MAX - GOAL_Y_MIN) / 3   # 2.6̄  (≈ 2.667)
GK_RIGHT_MAX  = GOAL_Y_MIN + THIRD               # ≈ 38.667
GK_LEFT_MIN   = GOAL_Y_MAX - THIRD              # ≈ 41.333
HEIGHT_MID    = 1.22                             # metres; low ≤ 1.22 < high

# International / cup competition names (for --intl-only mode)
INTL_COMPS = {
    "FIFA World Cup", "Women's World Cup", "FIFA U20 World Cup",
    "UEFA Euro", "UEFA Women's Euro",
    "Copa America", "African Cup of Nations",
    "Champions League", "UEFA Europa League",
    "Copa del Rey",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _nan(v):
    try:
        return isinstance(v, float) and math.isnan(v)
    except TypeError:
        return False

def _ok(v):
    """True if v is not None and not NaN."""
    return v is not None and not _nan(v)

def _at(lst, idx, default=None):
    """Safely index a list/tuple."""
    if isinstance(lst, (list, tuple)) and len(lst) > idx:
        v = lst[idx]
        return v if _ok(v) else default
    return default

def horiz(y):
    """Horizontal zone from GK's perspective."""
    if not _ok(y):
        return None
    if y < GK_RIGHT_MAX:
        return "gk_right"
    if y > GK_LEFT_MIN:
        return "gk_left"
    return "center"

def vert(z):
    """Vertical zone."""
    if not _ok(z):
        return None
    return "high" if z > HEIGHT_MID else "low"

def _str(v):
    """Return v if it's a non-empty string, else None."""
    if isinstance(v, str) and v:
        return v
    return None

def _int(v):
    """Return int(v) if possible, else None."""
    try:
        return int(v) if _ok(v) else None
    except (TypeError, ValueError):
        return None

def _body_to_dive(body_part):
    """
    Convert goalkeeper_body_part to a rough dive direction proxy (GK's perspective).
    This is only available when the keeper makes contact (saved kicks).
    For conceded kicks (No Touch), body_part is NaN → dive = null.
    NOT a reliable direction indicator — used for coverage reporting only.
    """
    if not _ok(body_part) or not isinstance(body_part, str):
        return None
    b = body_part.strip()
    if "Left" in b:
        return "gk_left"
    if "Right" in b:
        return "gk_right"
    if "Both" in b or "Chest" in b or "Head" in b:
        return "center"
    return None


# ── Per-match extraction ──────────────────────────────────────────────────────

def extract_match(match_id, meta):
    """
    Load events for one match, return (list_of_kick_dicts, is_shootout_match).
    """
    try:
        events = sb.events(match_id=match_id)
    except Exception as exc:
        print(f"      [WARN] match {match_id}: {exc}", flush=True)
        return [], False

    if "type" not in events.columns:
        return [], False

    has_shootout = bool((events["period"] == 5).any())

    shots   = events[events["type"] == "Shot"].copy()
    gk_evts = events[events["type"] == "Goal Keeper"].copy()

    # Build id → row lookup for goalkeeper events (matched via shot's related_events)
    gk_by_id = {}
    if "id" in gk_evts.columns:
        for _, row in gk_evts.iterrows():
            eid = row.get("id")
            if _ok(eid):
                gk_by_id[str(eid)] = row

    # ── Collect raw kicks in event order ─────────────────────────────────────
    raw = []
    for _, ev in shots.sort_values("index").iterrows():

        shot_type_name = _str(ev.get("shot_type"))
        period         = _int(ev.get("period")) or 0
        is_p5          = period == 5

        # Period-5 shots are all penalty kicks; otherwise require explicit "Penalty" type
        if not is_p5 and shot_type_name != "Penalty":
            continue

        # ── Taker ────────────────────────────────────────────────────────────
        taker_name = _str(ev.get("player"))
        taker_id   = _int(ev.get("player_id"))
        team_name  = _str(ev.get("team"))

        # ── Shot placement ────────────────────────────────────────────────────
        end_loc = ev.get("shot_end_location")
        y_val   = _at(end_loc, 1)
        z_val   = _at(end_loc, 2)   # absent when shot only recorded as [x, y]

        # ── Outcome ───────────────────────────────────────────────────────────
        outcome = _str(ev.get("shot_outcome"))

        # ── Goalkeeper (matched via shot's related_events → GK event id) ──────
        # Note: goalkeeper_end_location is NOT populated for penalty events
        # in StatsBomb free open data. We use goalkeeper_body_part as the
        # only available proxy (covers saves only, not conceded kicks).
        keeper_name  = None
        keeper_id    = None
        keeper_dive  = None    # null means not determinable from this data
        gk_body_part = None

        related = ev.get("related_events")
        if isinstance(related, list):
            for rel_id in related:
                gk_row = gk_by_id.get(str(rel_id))
                if gk_row is not None:
                    keeper_name  = _str(gk_row.get("player"))
                    keeper_id    = _int(gk_row.get("player_id"))
                    gk_body_part = _str(gk_row.get("goalkeeper_body_part"))
                    # Dive from body_part proxy (see _body_to_dive docstring)
                    keeper_dive  = _body_to_dive(gk_body_part)
                    break

        raw.append({
            "_idx":     ev.get("index", 0),
            "_period":  period,
            "_is_p5":   is_p5,
            "_team":    team_name,
            "_outcome": outcome,
            "taker_name":       taker_name,
            "taker_id":         taker_id,
            "keeper_name":      keeper_name,
            "keeper_id":        keeper_id,
            "team_name":        team_name,
            "placement_horiz":  horiz(y_val),
            "placement_vert":   vert(z_val),
            "keeper_dive":      keeper_dive,  # body_part proxy; null for most kicks
            "gk_body_part":     gk_body_part, # raw field for audit
            "outcome":          outcome,
            "period":           period,
        })

    # ── Pass 2: shootout score state ──────────────────────────────────────────
    p5_kicks = [k for k in raw if k["_is_p5"]]
    team_goals: dict = defaultdict(int)
    for i, k in enumerate(p5_kicks):
        team  = k["_team"] or ""
        my_g  = team_goals.get(team, 0)
        opp_g = sum(v for t, v in team_goals.items() if t != team)
        k["shootout_score_state"] = (
            "level" if my_g == opp_g else ("ahead" if my_g > opp_g else "behind")
        )
        k["kick_order"] = i + 1
        if k["_outcome"] == "Goal":
            team_goals[team] += 1

    for k in raw:
        if not k["_is_p5"]:
            k["shootout_score_state"] = None
            k["kick_order"]           = None

    # ── Assemble final records ────────────────────────────────────────────────
    kicks = []
    for k in raw:
        kicks.append({
            "kick_id":              f"{match_id}_{k['_idx']}",
            "competition":          meta["competition"],
            "season":               meta["season"],
            "match_id":             match_id,
            "match_label":          meta["match_label"],
            "is_shootout":          k["_is_p5"],
            "kick_order":           k.get("kick_order"),
            "taker_id":             k["taker_id"],
            "taker_name":           k["taker_name"],
            "keeper_id":            k["keeper_id"],
            "keeper_name":          k["keeper_name"],
            "team_name":            k["team_name"],
            "placement_horiz":      k["placement_horiz"],
            "placement_vert":       k["placement_vert"],
            # keeper_dive intentionally omitted: field does not exist in StatsBomb
            # free open data for penalty events. See SCHEMA.md.
            "gk_body_part":         k["gk_body_part"],  # audit only, never in UI
            "outcome":              k["outcome"],
            "shootout_score_state": k.get("shootout_score_state"),
            "period":               k["period"],
        })

    return kicks, has_shootout


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    resume     = "--resume" in sys.argv
    intl_only  = "--intl-only" in sys.argv
    cache_path = CACHE_DIR / "processed_matches.json"

    match_cache: dict = {}
    if resume and cache_path.exists():
        with open(cache_path) as f:
            match_cache = json.load(f)
        print(f"Resume mode: {len(match_cache)} matches already cached.", flush=True)

    print("Loading free competitions from StatsBomb...", flush=True)
    comps = sb.competitions()
    if intl_only:
        comps = comps[comps["competition_name"].isin(INTL_COMPS)]
        print(f"  --intl-only: {len(comps)} competition-seasons (international/cup).")
    else:
        print(f"  {len(comps)} competition-seasons found.")
    print()

    all_kicks      = []
    shootout_index = []
    comp_stats     = defaultdict(lambda: {"shootouts": 0, "s_kicks": 0, "ig_kicks": 0})
    dive_total     = 0   # total kicks (denominator for coverage report)
    body_total     = 0   # kicks where gk_body_part is non-null

    for _, comp_row in comps.sort_values(["competition_name", "season_name"]).iterrows():
        comp_id   = comp_row.get("competition_id")
        season_id = comp_row.get("season_id")
        comp_name = comp_row.get("competition_name", str(comp_id))
        season_nm = comp_row.get("season_name", str(season_id))
        label     = f"{comp_name} — {season_nm}"

        try:
            matches = sb.matches(competition_id=comp_id, season_id=season_id)
        except Exception as exc:
            print(f"  [WARN] {label}: {exc}", flush=True)
            continue

        print(f"  {label}: {len(matches)} matches", flush=True)

        for _, match_row in matches.iterrows():
            match_id = match_row.get("match_id")
            mid_str  = str(match_id)

            home_val = match_row.get("home_team", "")
            away_val = match_row.get("away_team", "")
            home = home_val if isinstance(home_val, str) else home_val.get("name", str(home_val))
            away = away_val if isinstance(away_val, str) else away_val.get("name", str(away_val))
            match_label = f"{home} vs {away}"

            meta = {
                "competition": comp_name,
                "season":      season_nm,
                "match_label": match_label,
            }

            if mid_str in match_cache:
                entry       = match_cache[mid_str]
                kicks       = entry["kicks"]
                is_shootout = entry["is_shootout"]
            else:
                kicks, is_shootout = extract_match(match_id, meta)
                match_cache[mid_str] = {"kicks": kicks, "is_shootout": is_shootout}
                with open(cache_path, "w") as f:
                    json.dump(match_cache, f)

            for k in kicks:
                dive_total += 1
                if k.get("gk_body_part") is not None:
                    body_total += 1

            s_kicks  = [k for k in kicks if k["is_shootout"]]
            ig_kicks = [k for k in kicks if not k["is_shootout"]]

            comp_stats[label]["ig_kicks"] += len(ig_kicks)

            if is_shootout and s_kicks:
                comp_stats[label]["shootouts"] += 1
                comp_stats[label]["s_kicks"]   += len(s_kicks)
                shootout_index.append({
                    "match_id":    match_id,
                    "competition": comp_name,
                    "season":      season_nm,
                    "match_label": match_label,
                    "kicks":       len(s_kicks),
                    "goals":       sum(1 for k in s_kicks if k["outcome"] == "Goal"),
                })

            all_kicks.extend(kicks)

    # ── Write output files ────────────────────────────────────────────────────
    kicks_path = DATA_DIR / "kicks.json"
    index_path = DATA_DIR / "shootouts_index.json"

    with open(kicks_path, "w") as f:
        json.dump(all_kicks, f, indent=2, default=str)
    with open(index_path, "w") as f:
        json.dump(shootout_index, f, indent=2, default=str)

    # ── Print summary ─────────────────────────────────────────────────────────
    LINE = "═" * 74
    print(f"\n{LINE}")
    print("COMPETITION SUMMARY")
    print(LINE)
    print(f"  {'Competition — Season':<48} {'SO-matches':>10} {'SO-kicks':>8} {'IG-pens':>7}")
    print(f"  {'-'*48} {'-'*10} {'-'*8} {'-'*7}")

    total_s = total_sk = total_ig = 0
    for lbl in sorted(comp_stats):
        d = comp_stats[lbl]
        if d["shootouts"] > 0 or d["ig_kicks"] > 0:
            print(f"  {lbl:<48} {d['shootouts']:>10} {d['s_kicks']:>8} {d['ig_kicks']:>7}")
        total_s  += d["shootouts"]
        total_sk += d["s_kicks"]
        total_ig += d["ig_kicks"]

    print(f"  {'-'*48} {'-'*10} {'-'*8} {'-'*7}")
    print(f"  {'TOTAL':<48} {total_s:>10} {total_sk:>8} {total_ig:>7}")

    # ── Taker sample sizes ────────────────────────────────────────────────────
    taker_counts = Counter(k["taker_name"] for k in all_kicks if k["taker_name"])
    eligible     = sum(1 for v in taker_counts.values() if v >= 5)
    top_takers   = taker_counts.most_common(10)

    print(f"\n{'─'*74}")
    print("TAKER SAMPLE SIZES")
    print(f"  Unique takers          : {len(taker_counts)}")
    print(f"  Takers with n >= 5     : {eligible}  (minimum for showing tendency)")
    print(f"  Top 10 by penalty count:")
    for name, count in top_takers:
        print(f"    {count:>3}  {name}")

    # ── Keeper dive coverage ──────────────────────────────────────────────────
    s_kicks  = [k for k in all_kicks if k["is_shootout"]]
    bp_total = sum(1 for k in all_kicks if k["gk_body_part"] is not None)
    bp_so    = sum(1 for k in s_kicks if k["gk_body_part"] is not None)

    print(f"\n{'─'*74}")
    print("KEEPER DATA COVERAGE (audit info, not used in UI)")
    print(f"  goalkeeper_end_location : 0/{dive_total} (0.0%) — absent for all penalty events")
    print(f"  gk_body_part (audit)    : {bp_total}/{dive_total} all kicks, {bp_so}/{len(s_kicks)} shootout kicks")
    print(f"    → Populated only when keeper made contact. Never shown in UI.")

    print(f"\n{'─'*74}")
    print(f"Shootout matches found: {len(shootout_index)}")
    print(f"Output written to:")
    print(f"  {kicks_path}")
    print(f"  {index_path}")
    print(f"\nDone. Review the counts above, then OK me to proceed to Step 2.")


if __name__ == "__main__":
    main()
