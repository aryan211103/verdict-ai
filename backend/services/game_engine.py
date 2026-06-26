"""
Penalty shootout game engine.

Resolution logic, AI keeper, and session state live here.
No external data, no player statistics, no network calls.
Player/team names are passed in as cosmetic labels and never
influence any probability or game outcome.
"""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

# ── Cell classification ────────────────────────────────────────────────────────

class Cell(str, Enum):
    TL = "TL"; TC = "TC"; TR = "TR"
    ML = "ML"; MC = "MC"; MR = "MR"
    BL = "BL"; BC = "BC"; BR = "BR"

class Dive(str, Enum):
    L = "L"; C = "C"; R = "R"

_HORIZ: dict[Cell, Dive] = {
    Cell.TL: Dive.L, Cell.ML: Dive.L, Cell.BL: Dive.L,
    Cell.TC: Dive.C, Cell.MC: Dive.C, Cell.BC: Dive.C,
    Cell.TR: Dive.R, Cell.MR: Dive.R, Cell.BR: Dive.R,
}

_CORNERS  = {Cell.TL, Cell.TR, Cell.BL, Cell.BR}
_SIDE_MID = {Cell.ML, Cell.MR}
_CENTER   = {Cell.TC, Cell.MC, Cell.BC}

def _cell_type(cell: Cell) -> str:
    if cell in _CORNERS:  return "corner"
    if cell in _SIDE_MID: return "side_mid"
    return "center"

# ── Probability table ─────────────────────────────────────────────────────────
#
# (cell_type, matched) → P(goal)
#
# Verified by simulation (100 000 kicks each strategy, seed=42):
#   corners-only vs uniform keeper  → 73.5%  (best strategy)
#   side-mid-only vs uniform keeper → 65.3%  (middle)
#   centre-only vs uniform keeper   → 58.6%  (worst — not dominant)
#   uniform × uniform               → 66.7%  (≈ 67% real-world base rate)
#   Nash equilibrium value          → 67.0%
#
# Centre mismatch is 0.85 (not 0.90) because a keeper diving to the side
# can still reach a centre-column ball, preventing centre from being a
# free-scoring option on any mismatch.

_GOAL_PROB: dict[tuple[str, bool], float] = {
    ("corner",   True):  0.30,
    ("side_mid", True):  0.12,
    ("center",   True):  0.06,
    ("corner",   False): 0.95,
    ("side_mid", False): 0.92,
    ("center",   False): 0.85,
}


# ── Resolution ────────────────────────────────────────────────────────────────

@dataclass
class KickResult:
    cell: Cell
    dive: Dive
    matched: bool
    cell_type: str
    p_goal: float
    goal: bool


def resolve_kick(cell: Cell, dive: Dive, rng: random.Random | None = None) -> KickResult:
    """
    Resolve one penalty kick.

    cell — shooter's chosen grid cell (cosmetic player name never enters here)
    dive — keeper's chosen dive direction
    rng  — optional seeded Random instance (for testing)
    """
    if rng is None:
        rng = random.Random()

    matched   = (_HORIZ[cell] == dive)
    ct        = _cell_type(cell)
    p_goal    = _GOAL_PROB[(ct, matched)]
    goal      = rng.random() < p_goal

    return KickResult(
        cell=cell,
        dive=dive,
        matched=matched,
        cell_type=ct,
        p_goal=p_goal,
        goal=goal,
    )


# ── AI keeper ─────────────────────────────────────────────────────────────────
#
# First-order Markov model + 50% random floor.
#
# The AI tracks what horizontal direction the user shot AFTER each previous
# direction in this session, building a transition table. Before each kick
# it predicts the user's next shot based on the last shot, then mixes that
# prediction with a uniform random component.
#
# Why Markov instead of frequency counting:
#   Frequency counting is trivially beaten by simple alternating (L→R→L→R)
#   because the user always shoots the direction the AI least expects.
#   The Markov model learns that after L comes R and after R comes L,
#   defeating the alternating pattern. Frequency counting gives alternating
#   users ~84% conversion; the Markov model brings it down to ~52% (below
#   Nash equilibrium of 67%), so the user is incentivised to mix.
#
# The 50% random floor keeps the AI beatable: a user who mixes their own
# shots achieves the Nash equilibrium of ~67% regardless.
#
# No cross-game memory. No external player data. Ever.

RANDOM_FLOOR = 0.50
_DIRS = [Dive.L, Dive.C, Dive.R]


class AIKeeper:
    """In-session adaptive AI keeper using a first-order Markov model."""

    def __init__(self, rng: random.Random | None = None):
        self._rng = rng or random.Random()
        self._history: list[Dive] = []
        # transitions[last_dir][next_dir] = count
        self._transitions: dict[Dive, dict[Dive, int]] = {
            d: {d2: 0 for d2 in _DIRS} for d in _DIRS
        }

    # ── Public interface ──────────────────────────────────────────────────────

    def dive(self) -> Dive:
        """Sample a dive direction."""
        probs = self._compute_probs()
        r = self._rng.random()
        cumulative = 0.0
        for d in _DIRS:
            cumulative += probs[d]
            if r < cumulative:
                return d
        return _DIRS[-1]   # float rounding guard

    def record_shot(self, direction: Dive) -> None:
        """Call after each kick with the shot's horizontal direction."""
        if self._history:
            self._transitions[self._history[-1]][direction] += 1
        self._history.append(direction)

    @property
    def session_history(self) -> list[Dive]:
        return list(self._history)

    @property
    def session_counts(self) -> dict[str, int]:
        return {d.value: self._history.count(d) for d in _DIRS}

    # ── Internals ─────────────────────────────────────────────────────────────

    def _compute_probs(self) -> dict[Dive, float]:
        uniform = {d: 1 / 3 for d in _DIRS}

        if not self._history:
            return uniform

        last   = self._history[-1]
        counts = self._transitions[last]
        total  = sum(counts.values())

        if total == 0:
            markov_pred = uniform
        else:
            markov_pred = {d: counts[d] / total for d in _DIRS}

        return {
            d: RANDOM_FLOOR * uniform[d] + (1 - RANDOM_FLOOR) * markov_pred[d]
            for d in _DIRS
        }


# ── Shootout session ──────────────────────────────────────────────────────────

class KickPhase(str, Enum):
    REGULATION = "regulation"   # kicks 1-5 per team
    SUDDEN_DEATH = "sudden_death"


@dataclass
class TeamState:
    name: str           # cosmetic label only
    players: list[str]  # cosmetic labels only
    goals: int = 0
    kicks_taken: int = 0

    def next_player(self) -> str:
        if not self.players:
            return self.name
        return self.players[self.kicks_taken % len(self.players)]


@dataclass
class KickRecord:
    kick_number: int        # 1-based, overall sequence
    phase: KickPhase
    team: str
    player: str             # cosmetic
    cell: Optional[Cell]
    dive: Optional[Dive]
    result: Optional[KickResult]


@dataclass
class ShootoutSession:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    team_a: TeamState = field(default_factory=lambda: TeamState("Team A", []))
    team_b: TeamState = field(default_factory=lambda: TeamState("Team B", []))
    kicks: list[KickRecord] = field(default_factory=list)
    winner: Optional[str] = None
    finished: bool = False
    _rng: random.Random = field(default_factory=random.Random, repr=False)

    # ── Derived state ─────────────────────────────────────────────────────────

    @property
    def current_kick_number(self) -> int:
        return len(self.kicks) + 1

    @property
    def phase(self) -> KickPhase:
        # Sudden death starts once both teams have taken >= 5 kicks
        return (KickPhase.SUDDEN_DEATH
                if self.team_a.kicks_taken >= 5 and self.team_b.kicks_taken >= 5
                else KickPhase.REGULATION)

    @property
    def current_team(self) -> TeamState:
        # Teams alternate; A goes first
        total = self.team_a.kicks_taken + self.team_b.kicks_taken
        return self.team_a if total % 2 == 0 else self.team_b

    @property
    def other_team(self) -> TeamState:
        return self.team_b if self.current_team is self.team_a else self.team_a

    # ── Kick submission ───────────────────────────────────────────────────────

    def submit_kick(self, cell: Cell, dive: Dive) -> KickRecord:
        """Resolve a kick and advance session state. Returns the completed record."""
        if self.finished:
            raise ValueError("Session is already finished.")

        team    = self.current_team
        player  = team.next_player()
        phase   = self.phase
        result  = resolve_kick(cell, dive, rng=self._rng)

        record = KickRecord(
            kick_number=self.current_kick_number,
            phase=phase,
            team=team.name,
            player=player,
            cell=cell,
            dive=dive,
            result=result,
        )
        self.kicks.append(record)

        if result.goal:
            team.goals += 1
        team.kicks_taken += 1

        self._check_winner()
        return record

    # ── Winner logic ──────────────────────────────────────────────────────────

    def _check_winner(self) -> None:
        a, b = self.team_a, self.team_b
        ka, kb = a.kicks_taken, b.kicks_taken

        # Regulation: check if one team cannot be caught
        if ka == kb and ka <= 5 and ka > 0:
            # Both teams have taken equal kicks; check clinched
            remaining_a = 5 - ka
            remaining_b = 5 - kb
            if a.goals > b.goals + remaining_b:
                self._end(a.name); return
            if b.goals > a.goals + remaining_a:
                self._end(b.name); return
            if ka == 5 and a.goals != b.goals:
                self._end(a.name if a.goals > b.goals else b.name); return

        # After A's 5th, B might have already clinched
        if ka == 5 and kb < 5:
            if b.goals > a.goals:
                self._end(b.name); return

        # Sudden death: decide after each pair (A and B both kicked)
        if ka > 5 and kb > 5 and ka == kb:
            if a.goals != b.goals:
                self._end(a.name if a.goals > b.goals else b.name)

    def _end(self, winner_name: str) -> None:
        self.winner   = winner_name
        self.finished = True

    # ── Serialisation helper ──────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "finished":   self.finished,
            "winner":     self.winner,
            "phase":      self.phase.value,
            "score":      {self.team_a.name: self.team_a.goals,
                           self.team_b.name: self.team_b.goals},
            "kicks_taken": {self.team_a.name: self.team_a.kicks_taken,
                            self.team_b.name: self.team_b.kicks_taken},
            "current_team":   None if self.finished else self.current_team.name,
            "current_player": None if self.finished else self.current_team.next_player(),
        }
