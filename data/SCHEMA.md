# kicks.json — Field Schema

## Direction Convention (fixed, never changes)

**All direction labels are from the GOALKEEPER's perspective** — the person
standing on the goal line, facing the taker.

| Label | Attacker's view | StatsBomb y-coordinate |
|---|---|---|
| `gk_right` | Attacker's left | lower y |
| `center` | Center | mid y |
| `gk_left` | Attacker's right | higher y |

This applies to **both** shot placement and keeper dive direction.
The UI must never relabel these as the attacker's left/right.

---

## Placement Derivation

### Horizontal — from `shot.end_location[1]` (the y-coordinate)

StatsBomb goal spans **y = 36.0 to y = 44.0** (goal width = 8 m equivalent).
Divided into three equal thirds (2.667 each):

```
y < 38.667              → gk_right   (GK's right; attacker's left)
38.667 ≤ y ≤ 41.333    → center
y > 41.333              → gk_left    (GK's left; attacker's right)
```

Boundary values (exact): `GK_RIGHT_MAX = 36 + 8/3 ≈ 38.667`,
`GK_LEFT_MIN = 44 − 8/3 ≈ 41.333`.

### Vertical — from `shot.end_location[2]` (z, metres above ground)

Goal height = 2.44 m. Split at the midpoint:

```
end_z ≤ 1.22    → low
end_z >  1.22   → high
end_z missing   → null  (shot off target or data gap)
```

---

## Keeper Dive — Not Available in Free Data

`goalkeeper_end_location` is absent for 100% of penalty events in StatsBomb
free open data (verified against raw JSON for every World Cup 2018 and 2022
shootout match). There is no keeper dive direction field in this dataset.

**The keeper dive mechanic is cut from the UI (decision: 2026-06-25).**

`gk_body_part` is retained in `kicks.json` as an audit field only. It is never
used as a direction signal because it is populated only on saves (when the keeper
makes contact), making it a survivorship-biased proxy, not a representative
record of dive direction.

---

## kicks.json Fields

| Field | Type | Description |
|---|---|---|
| `kick_id` | string | `{match_id}_{event_index}` — unique per kick |
| `competition` | string | StatsBomb competition name |
| `season` | string | StatsBomb season label |
| `match_id` | integer | StatsBomb match ID |
| `match_label` | string | Human-readable "Home vs Away" |
| `is_shootout` | boolean | `true` if period == 5; `false` for in-game penalty |
| `kick_order` | integer or null | 1-based position within the shootout; null for in-game |
| `taker_id` | integer | StatsBomb player ID of the taker |
| `taker_name` | string | Taker's full name |
| `keeper_id` | integer or null | StatsBomb player ID of the goalkeeper |
| `keeper_name` | string or null | Goalkeeper's full name |
| `team_name` | string | Taker's team name |
| `placement_horiz` | string or null | `gk_right` / `center` / `gk_left` (GK's perspective) |
| `placement_vert` | string or null | `high` / `low` / `null` |
| `gk_body_part` | string or null | **Audit field only — never shown in UI.** StatsBomb `goalkeeper_body_part` value (e.g. `Left Hand`, `Right Hand`, `Both Hands`). Present only when keeper made contact (saved kicks). Absent for all conceded and off-target kicks. |
| `outcome` | string | StatsBomb shot outcome name (e.g. `Goal`, `Saved`, `Off T`, `Post`) |
| `shootout_score_state` | string or null | `ahead` / `behind` / `level` at moment of kick; null for in-game |
| `period` | integer | 1–5 |

---

## shootouts_index.json Fields

One record per match that contained a period-5 shootout.

| Field | Type | Description |
|---|---|---|
| `match_id` | integer | StatsBomb match ID |
| `competition` | string | Competition name |
| `season` | string | Season label |
| `match_label` | string | "Home vs Away" |
| `kicks` | integer | Total kicks in this shootout |
| `goals` | integer | Goals scored in this shootout |

---

## Honesty Floor

Individual taker tendencies are only shown when `n >= 5` for that taker.
Below that threshold, the UI shows "Insufficient data (n=X)" and explains
why sample sizes this small cannot support inference.
Wilson confidence intervals are computed only above this floor.
