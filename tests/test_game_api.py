"""
API-level tests for the game endpoints.

Run: python -m pytest tests/test_game_api.py -v

Uses FastAPI's TestClient (no real server needed).
"""

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


# ── Helpers ───────────────────────────────────────────────────────────────────

def create_session(mode="1v1", seed=42, team_a_name="Team A", team_b_name="Team B",
                   a_players=None, b_players=None):
    resp = client.post("/game/session", json={
        "team_a": {"team_name": team_a_name, "players": a_players or ["P1","P2","P3","P4","P5"]},
        "team_b": {"team_name": team_b_name, "players": b_players or ["Q1","Q2","Q3","Q4","Q5"]},
        "mode": mode,
        "seed": seed,
    })
    assert resp.status_code == 201, resp.text
    return resp.json()["session_id"]


# ── Session creation ──────────────────────────────────────────────────────────

class TestCreateSession:
    def test_creates_session_returns_201(self):
        resp = client.post("/game/session", json={
            "team_a": {"team_name": "A", "players": ["X"]},
            "team_b": {"team_name": "B", "players": ["Y"]},
        })
        assert resp.status_code == 201
        assert "session_id" in resp.json()

    def test_mode_1v1_accepted(self):
        sid = create_session(mode="1v1")
        assert sid

    def test_mode_vs_ai_accepted(self):
        sid = create_session(mode="vs_ai")
        assert sid

    def test_invalid_mode_rejected(self):
        resp = client.post("/game/session", json={
            "team_a": {"team_name": "A", "players": ["X"]},
            "team_b": {"team_name": "B", "players": ["Y"]},
            "mode": "god_mode",
        })
        assert resp.status_code == 422

    def test_empty_players_rejected(self):
        resp = client.post("/game/session", json={
            "team_a": {"team_name": "A", "players": []},
            "team_b": {"team_name": "B", "players": ["Y"]},
        })
        assert resp.status_code == 422

    def test_unknown_session_returns_404(self):
        resp = client.get("/game/session/does-not-exist")
        assert resp.status_code == 404


# ── Mode enforcement ──────────────────────────────────────────────────────────

class TestModeEnforcement:
    def test_1v1_requires_dive(self):
        """1v1 mode must reject requests without a dive field."""
        sid = create_session(mode="1v1")
        resp = client.post(f"/game/session/{sid}/kick", json={"cell": "TL"})
        assert resp.status_code == 422
        assert "dive" in resp.json()["detail"].lower()

    def test_1v1_accepts_cell_and_dive(self):
        """1v1 mode should accept a valid cell + dive."""
        sid = create_session(mode="1v1", seed=1)
        resp = client.post(f"/game/session/{sid}/kick", json={"cell": "TL", "dive": "R"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["outcome"]["cell"] == "TL"
        assert data["outcome"]["dive"] in ("L", "C", "R")

    def test_vs_ai_accepts_dive_field_for_ai_shot(self):
        """
        vs_ai mode must ACCEPT a request that includes 'dive' — this signals
        that the AI is shooting and the human is keeping. The backend uses
        the supplied dive as the keeper's choice and resolves the kick normally.
        dive absent  → human shoots, AI keeper picks dive (200 OK)
        dive present → AI shoots, human keeper supplied dive (200 OK)
        """
        sid = create_session(mode="vs_ai")
        resp = client.post(f"/game/session/{sid}/kick",
                           json={"cell": "TL", "dive": "R"})
        assert resp.status_code == 200
        data = resp.json()
        # dive should be echoed back as the supplied value
        assert data["outcome"]["dive"] == "R"
        # AI session counts must be present but NOT updated (AI's own shot)
        assert data["ai_session_counts"] is not None

    def test_vs_ai_accepts_cell_only(self):
        """vs_ai mode should accept a request with only 'cell'."""
        sid = create_session(mode="vs_ai", seed=5)
        resp = client.post(f"/game/session/{sid}/kick", json={"cell": "TR"})
        assert resp.status_code == 200
        data = resp.json()
        # dive was chosen by AI, not by caller
        assert data["outcome"]["dive"] in ("L", "C", "R")
        # AI session counts must be present
        assert data["ai_session_counts"] is not None
        assert set(data["ai_session_counts"].keys()) == {"L", "C", "R"}

    def test_invalid_cell_rejected(self):
        sid = create_session(mode="1v1")
        resp = client.post(f"/game/session/{sid}/kick",
                           json={"cell": "XX", "dive": "L"})
        assert resp.status_code == 422

    def test_invalid_dive_rejected(self):
        sid = create_session(mode="1v1")
        resp = client.post(f"/game/session/{sid}/kick",
                           json={"cell": "TL", "dive": "Q"})
        assert resp.status_code == 422


# ── API-level cosmetic guarantee ─────────────────────────────────────────────

class TestCosmeticGuarantee:
    def test_different_names_same_seed_identical_p_goal(self):
        """
        Two sessions with the SAME seed but DIFFERENT team and player names
        must produce identical p_goal for the same cell+dive input.

        This enforces at the API boundary that player/team identity is cosmetic:
        names travel through the response as labels but never influence the
        probability calculation.
        """
        # Session 1: named teams
        sid1 = create_session(
            mode="1v1", seed=42,
            team_a_name="Argentina", team_b_name="France",
            a_players=["Messi", "Dybala", "Paredes", "Montiel", "Di Maria"],
            b_players=["Mbappé", "Muani", "Griezmann", "Coman", "Tchouaméni"],
        )
        # Session 2: identical seed, anonymous teams
        sid2 = create_session(
            mode="1v1", seed=42,
            team_a_name="Team X", team_b_name="Team Y",
            a_players=["A1", "A2", "A3", "A4", "A5"],
            b_players=["B1", "B2", "B3", "B4", "B5"],
        )

        # Same kick submitted to both sessions
        r1 = client.post(f"/game/session/{sid1}/kick",
                         json={"cell": "TL", "dive": "R"}).json()
        r2 = client.post(f"/game/session/{sid2}/kick",
                         json={"cell": "TL", "dive": "R"}).json()

        # p_goal must be identical — it comes from the probability table,
        # not from team or player identity
        assert r1["outcome"]["p_goal"] == r2["outcome"]["p_goal"], (
            f"p_goal differed: {r1['outcome']['p_goal']} vs {r2['outcome']['p_goal']}"
        )

        # goal outcome must be identical (same RNG seed, same probability draw)
        assert r1["outcome"]["goal"] == r2["outcome"]["goal"], (
            f"goal outcome differed despite same seed and same kick"
        )

        # cell_type and matched must be identical
        assert r1["outcome"]["cell_type"] == r2["outcome"]["cell_type"]
        assert r1["outcome"]["matched"]   == r2["outcome"]["matched"]

        # Players shown are different labels (cosmetic) — confirm names differ
        assert r1["outcome"]["player"] != r2["outcome"]["player"]

    def test_p_goal_matches_table_values(self):
        """
        p_goal in the response must be one of the 6 documented table values.
        Uses a fresh single-kick session for each (cell, dive) pair so a
        finished session can never contaminate the next check.
        """
        documented = {0.30, 0.12, 0.06, 0.95, 0.92, 0.85}
        for cell in ["TL", "ML", "TC", "TR", "MR", "BC"]:
            for dive in ["L", "C", "R"]:
                sid = create_session(mode="1v1", seed=1)
                resp = client.post(f"/game/session/{sid}/kick",
                                   json={"cell": cell, "dive": dive})
                assert resp.status_code == 200, f"Unexpected {resp.status_code} for {cell}/{dive}"
                p = resp.json()["outcome"]["p_goal"]
                assert p in documented, f"Undocumented p_goal {p} for {cell}/{dive}"


# ── Session lifecycle ─────────────────────────────────────────────────────────

class TestSessionLifecycle:
    def test_get_session_returns_state(self):
        sid = create_session(mode="1v1", seed=3)
        resp = client.get(f"/game/session/{sid}")
        assert resp.status_code == 200
        data = resp.json()["session"]
        assert data["finished"] is False
        assert data["winner"] is None

    def test_delete_session(self):
        sid = create_session(mode="1v1")
        resp = client.delete(f"/game/session/{sid}")
        assert resp.status_code == 204
        # Gone after delete
        assert client.get(f"/game/session/{sid}").status_code == 404

    def test_kick_after_session_ends_returns_error(self):
        sid = create_session(mode="1v1", seed=0)
        # Drive to completion
        for _ in range(50):
            resp = client.post(f"/game/session/{sid}/kick",
                               json={"cell": "TL", "dive": "R"})
            if resp.status_code != 200:
                break
            if resp.json()["session"]["finished"]:
                break
        # Next kick must fail with 409 Conflict (not 500)
        resp = client.post(f"/game/session/{sid}/kick",
                           json={"cell": "TL", "dive": "R"})
        assert resp.status_code == 409, f"Expected 409, got {resp.status_code}"

    def test_session_cap_evicts_oldest(self):
        """Creating more than _SESSION_CAP sessions evicts the oldest, not an error."""
        from backend.routers.game import _SESSION_CAP
        first_sid = create_session(mode="1v1")

        # Create enough sessions to exceed the cap
        for _ in range(_SESSION_CAP):
            create_session(mode="1v1")

        # The first session should have been evicted
        resp = client.get(f"/game/session/{first_sid}")
        assert resp.status_code == 404, "Oldest session should have been evicted at cap"
