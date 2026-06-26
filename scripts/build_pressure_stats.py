#!/usr/bin/env python3
"""
Step 2b — Build population pressure stats.

Reads data/kicks.json (shootout kicks only), writes
data/aggregations/pressure_stats.json.

Run: python scripts/build_pressure_stats.py
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from backend.services.aggregations import (
    build_pressure_stats, load_kicks, MIN_N,
    INTERNATIONAL_TOURNAMENTS, is_international,
)

AGG_DIR = Path(__file__).parent.parent / "data" / "aggregations"
AGG_DIR.mkdir(parents=True, exist_ok=True)


def main():
    kicks = load_kicks()

    all_shootout = [k for k in kicks if k.get("is_shootout")]
    # Pressure stats: INTERNATIONAL TOURNAMENTS ONLY
    # Club competitions (Champions League, Indian Super League, etc.) go to
    # the per-player placement pool only — never to the pressure stats bucket.
    shootout = [k for k in all_shootout if is_international(k)]
    excluded = [k for k in all_shootout if not is_international(k)]

    if not shootout:
        sys.exit("No international shootout kicks found. Run explore_data.py first.")

    print("Bucket split (shootout kicks only):")
    from collections import Counter
    by_comp = Counter(k["competition"] for k in all_shootout)
    for comp, n in sorted(by_comp.items(), key=lambda x: -x[1]):
        bucket = "INTL" if comp in INTERNATIONAL_TOURNAMENTS else "CLUB (excluded from pressure stats)"
        print(f"  {n:>4}  {comp:<35} [{bucket}]")
    print(f"  ----")
    print(f"  {len(shootout):>4}  INTERNATIONAL (used for pressure stats)")
    print(f"  {len(excluded):>4}  CLUB (excluded)")
    print()

    competitions = sorted(set(k["competition"] for k in shootout))
    print(f"Pressure stats computed from {len(shootout)} international-tournament shootout kicks.")
    print(f"Competitions: {', '.join(competitions)}\n")

    stats = build_pressure_stats(shootout)

    output = {
        "meta": {
            "computed_at": datetime.now(timezone.utc).isoformat(),
            "n_shootout_kicks": len(shootout),
            "n_excluded_club_shootout_kicks": len(excluded),
            "excluded_competitions": sorted(set(k["competition"] for k in excluded)),
            "competitions": competitions,
            "min_n_for_ci": MIN_N,
            "bucket_rule": (
                "International national-team tournaments only. "
                "Club competitions (Champions League, Indian Super League, etc.) "
                "are excluded from pressure stats — they feed the per-player "
                "placement pool only."
            ),
            "warning": (
                "Population-level historical base rates only. "
                "These do not predict individual kick outcomes "
                "and do not recommend any direction for either side."
            ),
        },
        **stats,
    }

    out_path = AGG_DIR / "pressure_stats.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    # ── Print ─────────────────────────────────────────────────────────────────
    ov = stats["overall"]
    print(f"Overall  {ov['goals']:>3}/{ov['n']:>3} = {ov['rate']:.1%}  "
          f"[{ov['wilson_lo']:.1%}, {ov['wilson_hi']:.1%}]")

    print("\nBy kick order:")
    for row in stats["by_kick_order"]:
        lo = f"{row['wilson_lo']:.1%}" if row["wilson_lo"] is not None else "—"
        hi = f"{row['wilson_hi']:.1%}" if row["wilson_hi"] is not None else "—"
        print(f"  Order {str(row['label']):>3}:  {row['goals']:>3}/{row['n']:>3} "
              f"= {row['rate']:.1%}  [{lo}, {hi}]")

    print("\nBy score state (kicking team's position before the kick):")
    for row in stats["by_score_state"]:
        lo = f"{row['wilson_lo']:.1%}" if row["wilson_lo"] is not None else "—"
        hi = f"{row['wilson_hi']:.1%}" if row["wilson_hi"] is not None else "—"
        print(f"  {row['label']:>7}:  {row['goals']:>3}/{row['n']:>3} "
              f"= {row['rate']:.1%}  [{lo}, {hi}]")

    print("\nSudden death vs regular rounds:")
    for row in stats["sudden_death_vs_regular"]:
        lo = f"{row['wilson_lo']:.1%}" if row["wilson_lo"] is not None else "—"
        hi = f"{row['wilson_hi']:.1%}" if row["wilson_hi"] is not None else "—"
        print(f"  {row['label']:>15}:  {row['goals']:>3}/{row['n']:>3} "
              f"= {row['rate']:.1%}  [{lo}, {hi}]")

    print(f"\nWritten → {out_path}")


if __name__ == "__main__":
    main()
