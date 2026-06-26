"""
FastAPI router — penalty shootout game.

Player/team names are accepted as cosmetic labels and stored for display.
They never enter resolve_kick(), AIKeeper, or any probability calculation.
"""

from __future__ import annotations

import random
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from backend.services.game_engine import (
    AIKeeper, Cell, Dive, ShootoutSession, TeamState,
)

router = APIRouter(prefix="/game", tags=["game"])

# ── In-memory session store ────────────────────────────────────────────────────
# Cap: 200 sessions max. When the cap is hit, the oldest session is evicted
# (LRU by creation order via OrderedDict). This prevents unbounded growth during
# a long demo without needing background threads or a scheduled job.
# For multi-worker production, replace with Redis + TTL.
from collections import OrderedDict

_SESSION_CAP = 200
_sessions: OrderedDict[str, ShootoutSession] = OrderedDict()
_ai_keepers: dict[str, AIKeeper] = {}


def _evict_if_full() -> None:
    while len(_sessions) >= _SESSION_CAP:
        evicted_id, _ = _sessions.popitem(last=False)   # oldest first
        _ai_keepers.pop(evicted_id, None)


# ── Request / response models ──────────────────────────────────────────────────

class PlayerList(BaseModel):
    """Cosmetic player names for one team. Never used in game logic."""
    team_name: str
    players: list[str]

    @field_validator("players")
    @classmethod
    def at_least_one_player(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("players list must not be empty")
        return v


class CreateSessionRequest(BaseModel):
    team_a: PlayerList
    team_b: PlayerList
    mode: str = "1v1"      # "1v1" | "vs_ai"
    seed: Optional[int] = None   # optional reproducibility seed (testing)

    @field_validator("mode")
    @classmethod
    def valid_mode(cls, v: str) -> str:
        if v not in ("1v1", "vs_ai"):
            raise ValueError("mode must be '1v1' or 'vs_ai'")
        return v


class CreateSessionResponse(BaseModel):
    session_id: str
    mode: str
    team_a: str
    team_b: str
    message: str


class SubmitKickRequest(BaseModel):
    cell: str                  # TL | TC | TR | ML | MC | MR | BL | BC | BR  (always required)
    dive: Optional[str] = None # L | C | R — REQUIRED in 1v1, MUST BE ABSENT in vs_ai

    @field_validator("cell")
    @classmethod
    def valid_cell(cls, v: str) -> str:
        try:
            Cell(v.upper())
        except ValueError:
            raise ValueError(f"cell must be one of {[c.value for c in Cell]}")
        return v.upper()

    @field_validator("dive")
    @classmethod
    def valid_dive(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        try:
            Dive(v.upper())
        except ValueError:
            raise ValueError(f"dive must be one of {[d.value for d in Dive]}")
        return v.upper()


class KickOutcome(BaseModel):
    kick_number: int
    phase: str
    team: str
    player: str                   # cosmetic label only
    cell: str
    dive: str
    matched: bool
    cell_type: str
    p_goal: float
    goal: bool


class SubmitKickResponse(BaseModel):
    outcome: KickOutcome
    session: dict                 # full session state snapshot
    ai_session_counts: Optional[dict] = None   # Mode B: L/C/R counts for UI


class SessionStateResponse(BaseModel):
    session: dict
    ai_session_counts: Optional[dict] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/session", response_model=CreateSessionResponse, status_code=201)
def create_session(req: CreateSessionRequest) -> CreateSessionResponse:
    """
    Create a new shootout session.

    team_a / team_b carry cosmetic name and player labels.
    mode "1v1": both humans submit cell + dive each kick.
    mode "vs_ai": human submits cell; AI chooses dive.
    """
    _evict_if_full()

    rng = random.Random(req.seed) if req.seed is not None else random.Random()

    session = ShootoutSession(
        team_a=TeamState(req.team_a.team_name, req.team_a.players),
        team_b=TeamState(req.team_b.team_name, req.team_b.players),
        _rng=rng,
    )
    _sessions[session.session_id] = session

    if req.mode == "vs_ai":
        _ai_keepers[session.session_id] = AIKeeper(rng=random.Random())

    return CreateSessionResponse(
        session_id=session.session_id,
        mode=req.mode,
        team_a=req.team_a.team_name,
        team_b=req.team_b.team_name,
        message=(
            "Session created. Submit kicks via POST /game/session/{id}/kick."
        ),
    )


@router.post("/session/{session_id}/kick", response_model=SubmitKickResponse)
def submit_kick(session_id: str, req: SubmitKickRequest) -> SubmitKickResponse:
    """
    Submit one penalty kick.

    In 1v1 mode: both cell (shooter's choice) and dive (keeper's choice) required.
    In vs_ai mode: cell required; dive field is accepted but ignored — AI chooses.

    Player identity never enters the resolution logic.
    """
    session = _get_session(session_id)

    cell      = Cell(req.cell)
    ai        = _ai_keepers.get(session_id)
    is_ai     = ai is not None

    # Enforce the mode contract hard — don't silently swallow wrong inputs.
    if is_ai and req.dive is not None:
        raise HTTPException(
            status_code=422,
            detail=(
                "In vs_ai mode the keeper's dive is chosen by the AI. "
                "Do not supply 'dive' in the request body."
            ),
        )
    if not is_ai and req.dive is None:
        raise HTTPException(
            status_code=422,
            detail="In 1v1 mode 'dive' is required (L, C, or R).",
        )

    if is_ai:
        dive = ai.dive()
    else:
        dive = Dive(req.dive)   # type: ignore[arg-type]  # validated above

    try:
        record = session.submit_kick(cell, dive)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    # Record the horizontal direction of this shot in the AI's memory (Mode B)
    if ai is not None:
        from backend.services.game_engine import _HORIZ
        ai.record_shot(_HORIZ[cell])

    outcome = KickOutcome(
        kick_number=record.kick_number,
        phase=record.phase.value,
        team=record.team,
        player=record.player,       # cosmetic label
        cell=record.cell.value,
        dive=record.dive.value,
        matched=record.result.matched,
        cell_type=record.result.cell_type,
        p_goal=record.result.p_goal,
        goal=record.result.goal,
    )

    return SubmitKickResponse(
        outcome=outcome,
        session=session.to_dict(),
        ai_session_counts=ai.session_counts if ai else None,
    )


@router.get("/session/{session_id}", response_model=SessionStateResponse)
def get_session(session_id: str) -> SessionStateResponse:
    """Return current session state without advancing it."""
    session = _get_session(session_id)
    ai = _ai_keepers.get(session_id)
    return SessionStateResponse(
        session=session.to_dict(),
        ai_session_counts=ai.session_counts if ai else None,
    )


@router.delete("/session/{session_id}", status_code=204)
def delete_session(session_id: str) -> None:
    """Remove a session (clean up after game ends)."""
    _get_session(session_id)  # raises 404 if absent
    _sessions.pop(session_id, None)
    _ai_keepers.pop(session_id, None)


# ── Internal helper ───────────────────────────────────────────────────────────

def _get_session(session_id: str) -> ShootoutSession:
    session = _sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    return session
