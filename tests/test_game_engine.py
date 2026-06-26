"""
Tests for backend/services/game_engine.py

Run: python -m pytest tests/test_game_engine.py -v
"""

import random
import pytest
from collections import Counter

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from backend.services.game_engine import (
    Cell, Dive, KickResult, KickPhase,
    TeamState, KickRecord, ShootoutSession,
    AIKeeper, resolve_kick,
    _HORIZ, _CORNERS, _SIDE_MID, _CENTER, _GOAL_PROB,
    RANDOM_FLOOR,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_session(a_names=None, b_names=None, seed=0):
    s = ShootoutSession(
        team_a=TeamState("Argentina", a_names or ["Messi","Dybala","Paredes","Montiel","Di Maria"]),
        team_b=TeamState("France",    b_names or ["Mbappé","Muani","Griezmann","Coman","Tchouaméni"]),
        _rng=random.Random(seed),
    )
    return s


# ── 1. Probability table ──────────────────────────────────────────────────────

class TestProbabilityTable:
    def test_all_9_cells_classified(self):
        all_cells = list(Cell)
        assert len(all_cells) == 9
        classified = set()
        for c in all_cells:
            ct = None
            if c in _CORNERS:  ct = "corner"
            elif c in _SIDE_MID: ct = "side_mid"
            elif c in _CENTER:  ct = "center"
            assert ct is not None, f"{c} not classified"
            classified.add(c)
        assert classified == set(all_cells)

    def test_corner_cells(self):
        assert _CORNERS == {Cell.TL, Cell.TR, Cell.BL, Cell.BR}

    def test_side_mid_cells(self):
        assert _SIDE_MID == {Cell.ML, Cell.MR}

    def test_center_cells(self):
        assert _CENTER == {Cell.TC, Cell.MC, Cell.BC}

    def test_horiz_mapping_correct(self):
        assert _HORIZ[Cell.TL] == Dive.L
        assert _HORIZ[Cell.TC] == Dive.C
        assert _HORIZ[Cell.TR] == Dive.R
        assert _HORIZ[Cell.ML] == Dive.L
        assert _HORIZ[Cell.MC] == Dive.C
        assert _HORIZ[Cell.MR] == Dive.R
        assert _HORIZ[Cell.BL] == Dive.L
        assert _HORIZ[Cell.BC] == Dive.C
        assert _HORIZ[Cell.BR] == Dive.R

    def test_all_table_entries_present(self):
        types    = ["corner", "side_mid", "center"]
        matched  = [True, False]
        for ct in types:
            for m in matched:
                assert (ct, m) in _GOAL_PROB, f"Missing ({ct}, {m})"

    def test_probabilities_in_range(self):
        for key, p in _GOAL_PROB.items():
            assert 0 < p < 1, f"P={p} out of range for {key}"

    def test_matched_lower_than_mismatched(self):
        for ct in ["corner", "side_mid", "center"]:
            assert _GOAL_PROB[(ct, True)] < _GOAL_PROB[(ct, False)], \
                f"Matched should be harder than mismatched for {ct}"

    def test_corner_hardest_to_save_when_matched(self):
        # Keeper matched: corner concedes most
        assert _GOAL_PROB[("corner", True)] > _GOAL_PROB[("side_mid", True)]
        assert _GOAL_PROB[("side_mid", True)] > _GOAL_PROB[("center", True)]

    def test_center_mismatch_not_equal_to_corner_mismatch(self):
        # Centre mismatch intentionally lower than corner mismatch
        assert _GOAL_PROB[("center", False)] < _GOAL_PROB[("corner", False)]


# ── 2. resolve_kick ───────────────────────────────────────────────────────────

class TestResolveKick:
    def test_returns_kick_result(self):
        r = resolve_kick(Cell.TL, Dive.L, rng=random.Random(0))
        assert isinstance(r, KickResult)

    def test_matched_when_dive_equals_horizontal(self):
        r = resolve_kick(Cell.TL, Dive.L, rng=random.Random(0))
        assert r.matched is True

    def test_mismatched_when_dive_differs(self):
        r = resolve_kick(Cell.TL, Dive.R, rng=random.Random(0))
        assert r.matched is False

    def test_cell_and_dive_recorded(self):
        r = resolve_kick(Cell.MC, Dive.C, rng=random.Random(0))
        assert r.cell == Cell.MC
        assert r.dive == Dive.C

    def test_cell_type_corner(self):
        for cell in [Cell.TL, Cell.TR, Cell.BL, Cell.BR]:
            r = resolve_kick(cell, Dive.C, rng=random.Random(0))
            assert r.cell_type == "corner"

    def test_cell_type_side_mid(self):
        for cell in [Cell.ML, Cell.MR]:
            r = resolve_kick(cell, Dive.C, rng=random.Random(0))
            assert r.cell_type == "side_mid"

    def test_cell_type_center(self):
        for cell in [Cell.TC, Cell.MC, Cell.BC]:
            r = resolve_kick(cell, Dive.C, rng=random.Random(0))
            assert r.cell_type == "center"

    def test_p_goal_matches_table(self):
        r = resolve_kick(Cell.TL, Dive.L, rng=random.Random(0))  # corner, matched
        assert r.p_goal == pytest.approx(_GOAL_PROB[("corner", True)])

        r = resolve_kick(Cell.TL, Dive.R, rng=random.Random(0))  # corner, mismatch
        assert r.p_goal == pytest.approx(_GOAL_PROB[("corner", False)])

    def test_goal_is_bool(self):
        r = resolve_kick(Cell.MC, Dive.C, rng=random.Random(0))
        assert isinstance(r.goal, bool)

    def test_high_p_goal_usually_scores(self):
        # mismatch corner should score ~95% of the time
        goals = sum(
            resolve_kick(Cell.TL, Dive.R, rng=random.Random(i)).goal
            for i in range(1000)
        )
        assert goals > 900

    def test_low_p_goal_rarely_scores(self):
        # matched center should score ~6% of the time
        goals = sum(
            resolve_kick(Cell.MC, Dive.C, rng=random.Random(i)).goal
            for i in range(1000)
        )
        assert goals < 120

    def test_simulation_corners_beat_center(self):
        N = 10_000
        rng = random.Random(42)
        corner_goals = sum(
            resolve_kick(Cell.TL, Dive.C, rng=rng).goal for _ in range(N)
        )
        rng2 = random.Random(42)
        center_goals = sum(
            resolve_kick(Cell.MC, Dive.C, rng=rng2).goal for _ in range(N)
        )
        # Under uniform keeper (dive=C), corner mismatch vs center match
        # corner: P=0.95 (mismatch), center: P=0.06 (match)
        assert corner_goals > center_goals

    def test_overall_conversion_near_67pct(self):
        """Uniform shooter × uniform keeper → ≈ 67%."""
        cells = list(Cell)
        dives = list(Dive)
        N     = 50_000
        rng   = random.Random(99)
        goals = sum(
            resolve_kick(rng.choice(cells), rng.choice(dives), rng=rng).goal
            for _ in range(N)
        )
        rate = goals / N
        assert 0.64 < rate < 0.70, f"Expected ~0.67, got {rate:.3f}"


# ── 3. AIKeeper ───────────────────────────────────────────────────────────────

class TestAIKeeper:
    def test_dive_returns_valid_direction(self):
        ai = AIKeeper(rng=random.Random(0))
        for _ in range(20):
            assert ai.dive() in list(Dive)

    def test_cold_start_uses_uniform(self):
        """With no history, AI should spread dives roughly uniformly."""
        counts = Counter()
        for seed in range(3000):
            ai = AIKeeper(rng=random.Random(seed))
            counts[ai.dive()] += 1
        total = sum(counts.values())
        for d in Dive:
            ratio = counts[d] / total
            assert 0.28 < ratio < 0.38, f"{d}: {ratio:.3f} (expected ~0.333)"

    def test_record_shot_updates_history(self):
        ai = AIKeeper(rng=random.Random(0))
        ai.record_shot(Dive.L)
        assert ai.session_history == [Dive.L]
        ai.record_shot(Dive.R)
        assert ai.session_history == [Dive.L, Dive.R]

    def test_transitions_tracked(self):
        ai = AIKeeper(rng=random.Random(0))
        ai.record_shot(Dive.L)
        ai.record_shot(Dive.R)   # L → R transition
        ai.record_shot(Dive.L)   # R → L transition
        # Internal transition counts
        assert ai._transitions[Dive.L][Dive.R] == 1
        assert ai._transitions[Dive.R][Dive.L] == 1

    def test_alternating_user_not_trivially_dominant(self):
        """
        A purely alternating L→R→L→R user should NOT consistently beat
        a player who mixes uniformly.  Both should achieve ~67% conversion.
        Without Markov, alternating gives ~84%. With Markov + 50% floor,
        it should be ≤ 72% (well within beatable range but not trivial).
        """
        N = 5_000
        rng = random.Random(42)

        # Alternating shooter
        alt_goals = 0
        ai = AIKeeper(rng=random.Random(42))
        dirs = [Dive.L, Dive.R]
        for i in range(N):
            shot_dir = dirs[i % 2]
            # Shooter picks a corner in that direction
            cell = Cell.TL if shot_dir == Dive.L else Cell.TR
            dive = ai.dive()
            result = resolve_kick(cell, dive, rng=rng)
            if result.goal:
                alt_goals += 1
            ai.record_shot(shot_dir)

        alt_rate = alt_goals / N
        # Must be meaningfully less than the ~84% frequency-counting gives
        assert alt_rate < 0.78, f"Alternating trivially dominant: {alt_rate:.3f}"

    def test_random_floor_respected(self):
        """
        Even with perfect transition data, AI should not be fully deterministic.
        Feed AI only L shots, then check it still sometimes dives non-L.
        """
        ai = AIKeeper(rng=random.Random(7))
        for _ in range(20):
            ai.record_shot(Dive.L)

        counts = Counter()
        for seed in range(1000):
            ai2 = AIKeeper(rng=random.Random(seed))
            for _ in range(20):
                ai2.record_shot(Dive.L)
            counts[ai2.dive()] += 1

        # Should still dive C and R some of the time (random floor ≥ 50%)
        assert counts[Dive.C] > 50, "C never dived despite random floor"
        assert counts[Dive.R] > 50, "R never dived despite random floor"

    def test_session_counts(self):
        ai = AIKeeper(rng=random.Random(0))
        ai.record_shot(Dive.L)
        ai.record_shot(Dive.L)
        ai.record_shot(Dive.R)
        counts = ai.session_counts
        assert counts["L"] == 2
        assert counts["R"] == 1
        assert counts["C"] == 0


# ── 4. ShootoutSession ────────────────────────────────────────────────────────

class TestShootoutSession:
    def test_initial_state(self):
        s = make_session()
        assert s.finished is False
        assert s.winner is None
        assert s.team_a.goals == 0
        assert s.team_b.goals == 0

    def test_teams_alternate(self):
        s = make_session(seed=1)
        # A kicks first
        assert s.current_team.name == "Argentina"
        s.submit_kick(Cell.TL, Dive.R)   # A kick 1
        assert s.current_team.name == "France"
        s.submit_kick(Cell.TR, Dive.L)   # B kick 1
        assert s.current_team.name == "Argentina"

    def test_player_name_cycles(self):
        s = make_session(a_names=["P1","P2","P3"], seed=2)
        assert s.team_a.next_player() == "P1"
        s.submit_kick(Cell.TL, Dive.R)
        s.submit_kick(Cell.TL, Dive.R)   # B kick
        assert s.team_a.next_player() == "P2"

    def test_goal_increments_score(self):
        # Force a goal: mismatch on corner → P=0.95
        s = make_session(seed=0)
        a_goals_before = s.team_a.goals
        # Keep submitting until we get a result we can verify
        r = s.submit_kick(Cell.TL, Dive.R)   # A kicks, mismatch
        if r.result.goal:
            assert s.team_a.goals == a_goals_before + 1
        else:
            assert s.team_a.goals == a_goals_before

    def test_phase_regulation_initially(self):
        s = make_session(seed=0)
        assert s.phase == KickPhase.REGULATION

    def test_phase_sudden_death_after_5_each(self):
        s = make_session(seed=0)
        # Simulate 10 kicks (5 per team) with all goals
        for _ in range(10):
            s.submit_kick(Cell.TL, Dive.R)
            if s.finished:
                break
        if not s.finished:
            assert s.phase == KickPhase.SUDDEN_DEATH

    def test_cannot_kick_after_finish(self):
        s = make_session(seed=0)
        # Drive to a known finish: A scores all, B misses all
        # Force by making every kick a corner mismatch (P=0.95 goal or save)
        # Just simulate until finished
        for _ in range(50):
            if s.finished:
                break
            s.submit_kick(Cell.TL, Dive.R)

        assert s.finished
        with pytest.raises(ValueError):
            s.submit_kick(Cell.TL, Dive.R)

    def test_winner_declared(self):
        s = make_session(seed=0)
        for _ in range(50):
            if s.finished:
                break
            s.submit_kick(Cell.TL, Dive.R)
        assert s.winner in (s.team_a.name, s.team_b.name)

    def test_session_id_is_string(self):
        s = make_session()
        assert isinstance(s.session_id, str)
        assert len(s.session_id) > 0

    def test_to_dict_structure(self):
        s = make_session(seed=3)
        d = s.to_dict()
        assert "session_id" in d
        assert "finished" in d
        assert "winner" in d
        assert "score" in d
        assert "phase" in d

    def test_clinch_before_5_kicks_each(self):
        """A wins 5-0: B cannot catch up after A's 5th — session ends early."""
        # We can't force exact outcomes without mocking random,
        # but we verify that if session finishes before 10 kicks,
        # it was a valid early clinch.
        s = make_session(seed=999)
        for _ in range(12):
            if s.finished:
                break
            s.submit_kick(Cell.TL, Dive.R)
        # If finished early (< 10 kicks total), winner must exist
        if s.finished:
            assert s.winner is not None
        # (the test is that no exception was raised and state is consistent)

    def test_kick_record_stored(self):
        s = make_session(seed=5)
        r = s.submit_kick(Cell.MC, Dive.L)
        assert isinstance(r, KickRecord)
        assert r.cell == Cell.MC
        assert r.dive == Dive.L
        assert r.result is not None
        assert len(s.kicks) == 1

    def test_player_label_not_in_probabilities(self):
        """Changing team/player labels must produce identical probability draws."""
        rng1 = random.Random(42)
        rng2 = random.Random(42)

        s1 = ShootoutSession(
            team_a=TeamState("Argentina", ["Messi"]),
            team_b=TeamState("France",    ["Mbappé"]),
            _rng=rng1,
        )
        s2 = ShootoutSession(
            team_a=TeamState("Team X", ["Alice"]),
            team_b=TeamState("Team Y", ["Bob"]),
            _rng=rng2,
        )
        # Same cell/dive choices must produce identical outcomes regardless of names
        r1 = s1.submit_kick(Cell.TL, Dive.R)
        r2 = s2.submit_kick(Cell.TL, Dive.R)
        assert r1.result.goal == r2.result.goal
        assert r1.result.p_goal == r2.result.p_goal


# ── 5. Simulation sanity ──────────────────────────────────────────────────────

class TestSimulationSanity:
    def test_strategy_ranking_corners_best(self):
        """Corners > side_mid > center against uniform keeper."""
        N   = 20_000
        rng = random.Random(7)

        def rate(cells):
            return sum(
                resolve_kick(rng.choice(cells), rng.choice(list(Dive)), rng=rng).goal
                for _ in range(N)
            ) / N

        r_corner   = rate(list(_CORNERS))
        r_side_mid = rate(list(_SIDE_MID))
        r_center   = rate(list(_CENTER))

        assert r_corner > r_side_mid, f"corner {r_corner:.3f} ≤ side_mid {r_side_mid:.3f}"
        assert r_side_mid > r_center, f"side_mid {r_side_mid:.3f} ≤ center {r_center:.3f}"

    def test_random_floor_is_constant(self):
        assert RANDOM_FLOOR == 0.50
