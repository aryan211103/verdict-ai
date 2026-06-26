import { useState } from 'react';
import SetupScreen   from './SetupScreen';
import HandoffScreen from './HandoffScreen';
import GoalGrid      from './GoalGrid';
import KeeperPicker  from './KeeperPicker';
import RevealScreen  from './RevealScreen';
import Scoreboard    from './Scoreboard';
import WinnerScreen  from './WinnerScreen';
import AIPanel       from './AIPanel';
import ErrorScreen   from './ErrorScreen';
import { api, ApiError } from '../../api/client';
import './game.css';

const PHASE = {
  SETUP:         'setup',
  HANDOFF_SHOOT: 'handoff_shoot',
  SHOOTING:      'shooting',
  HANDOFF_KEEP:  'handoff_keep',   // 1v1 only
  KEEPING:       'keeping',        // 1v1 only
  REVEAL:        'reveal',
  WINNER:        'winner',
  EXPIRED:       'expired',        // session evicted or backend returned 404
  HARD_ERROR:    'hard_error',     // backend down or unrecoverable
};

export default function ShootoutGame() {
  const [uiPhase,     setUiPhase]    = useState(PHASE.SETUP);
  const [mode,        setMode]       = useState('1v1');
  const [sessionId,   setSessionId]  = useState(null);
  const [session,     setSession]    = useState(null);
  const [teamColors,  setTeamColors] = useState({});   // { teamName: cssColor } — cosmetic only
  const [pendingCell, setCell]       = useState(null);
  const [lastOutcome, setOutcome]    = useState(null);
  const [aiCounts,    setAiCounts]   = useState(null);
  const [error,       setError]      = useState(null);
  const [loading,     setLoading]    = useState(false);

  // ── Setup ─────────────────────────────────────────────────────────────────
  async function handleSetupDone(teamA, teamB, chosenMode, colorA, colorB) {
    setLoading(true); setError(null); setMode(chosenMode);
    // Store team colors for cosmetic accents — never enters game logic
    if (colorA || colorB) {
      setTeamColors({
        [teamA.team_name]: colorA,
        [teamB.team_name]: colorB,
      });
    }
    try {
      const data  = await api.createSession({ team_a: teamA, team_b: teamB, mode: chosenMode });
      const state = await api.getSession(data.session_id);
      setSessionId(data.session_id);
      setSession(state.session);
      setAiCounts(state.ai_session_counts);
      setUiPhase(PHASE.HANDOFF_SHOOT);
    } catch (e) {
      if (e instanceof ApiError && e.status === 0) {
        setUiPhase(PHASE.HARD_ERROR);
      } else {
        setError(e.message);
      }
    }
    finally { setLoading(false); }
  }

  // ── Shooter picks a cell ──────────────────────────────────────────────────
  function handleCellChosen(cell) {
    setCell(cell);
    if (mode === 'vs_ai') {
      // AI mode: submit immediately without keeper handoff
      submitKick(cell, null);
    } else {
      setUiPhase(PHASE.HANDOFF_KEEP);
    }
  }

  // ── 1v1: keeper picks dive → resolve ──────────────────────────────────────
  function handleDiveChosen(dive) { submitKick(pendingCell, dive); }

  // ── Common kick submission ─────────────────────────────────────────────────
  async function submitKick(cell, dive) {
    setLoading(true); setError(null);
    try {
      const payload = mode === 'vs_ai' ? { cell } : { cell, dive };
      const data    = await api.submitKick(sessionId, payload);
      setOutcome(data.outcome);
      setSession(data.session);
      if (data.ai_session_counts) setAiCounts(data.ai_session_counts);
      setUiPhase(data.session.finished ? PHASE.WINNER : PHASE.REVEAL);
    } catch (e) {
      setLoading(false);
      if (e instanceof ApiError && e.status === 404) {
        // Session was evicted (LRU cap) or otherwise gone — not a user error.
        setUiPhase(PHASE.EXPIRED);
      } else if (e instanceof ApiError && e.status === 0) {
        // Backend is completely unreachable.
        setUiPhase(PHASE.HARD_ERROR);
      } else {
        // All other errors: show inline banner, stay on current phase.
        setError(e.message);
        setUiPhase(prev => prev === PHASE.KEEPING ? PHASE.KEEPING : PHASE.SHOOTING);
      }
      return;
    }
    setLoading(false);
  }

  // ── After reveal ──────────────────────────────────────────────────────────
  function handleNextKick() {
    setCell(null); setOutcome(null);
    setUiPhase(PHASE.HANDOFF_SHOOT);
  }

  // ── Restart ───────────────────────────────────────────────────────────────
  function handleRestart() {
    if (sessionId) api.deleteSession(sessionId).catch(() => {});
    setSessionId(null); setSession(null); setCell(null);
    setOutcome(null); setAiCounts(null); setError(null);
    setTeamColors({});
    setUiPhase(PHASE.SETUP);
  }

  const shooter   = session?.current_team ?? '';
  const keeperTeam = session?.score
    ? Object.keys(session.score).find(t => t !== shooter)
    : 'Keeper';

  return (
    <div className="game-root">
      {error && <div className="error-banner">{error}</div>}

      {uiPhase === PHASE.SETUP && (
        <SetupScreen onDone={handleSetupDone} loading={loading} />
      )}

      {uiPhase === PHASE.HANDOFF_SHOOT && (
        <HandoffScreen
          message="Pass the device to"
          name={shooter}
          subtext={mode === 'vs_ai'
            ? 'Pick your spot — the AI keeper will react.'
            : "Don't let the keeper see your pick!"}
          buttonLabel="I'm ready — show the goal"
          onContinue={() => setUiPhase(PHASE.SHOOTING)}
        />
      )}

      {uiPhase === PHASE.SHOOTING && (
        <div className="kick-screen">
          <Scoreboard session={session} teamColors={teamColors} />
          <p className="role-label">🎯 {shooter} — pick your spot</p>
          <GoalGrid onSelect={handleCellChosen} />
          {mode === 'vs_ai' && aiCounts && (
            <AIPanel counts={aiCounts} lastDive={null} />
          )}
          {loading && <p className="loading-note">Resolving…</p>}
        </div>
      )}

      {/* 1v1 only phases */}
      {uiPhase === PHASE.HANDOFF_KEEP && (
        <HandoffScreen
          message="Pass the device to"
          name={keeperTeam}
          subtext="Shooter has locked in. Now choose your dive."
          buttonLabel="I'm ready — show dive options"
          onContinue={() => setUiPhase(PHASE.KEEPING)}
        />
      )}

      {uiPhase === PHASE.KEEPING && (
        <div className="kick-screen">
          <Scoreboard session={session} teamColors={teamColors} />
          <p className="role-label">🧤 Keeper — choose your dive</p>
          <KeeperPicker onSelect={handleDiveChosen} loading={loading} />
        </div>
      )}

      {uiPhase === PHASE.REVEAL && lastOutcome && (
        <RevealScreen
          outcome={lastOutcome}
          session={session}
          teamColors={teamColors}
          onNext={handleNextKick}
          aiPanel={mode === 'vs_ai' && aiCounts
            ? <AIPanel counts={aiCounts} lastDive={lastOutcome.dive} />
            : null}
        />
      )}

      {uiPhase === PHASE.WINNER && session && (
        <WinnerScreen
          session={session}
          lastOutcome={lastOutcome}
          onRestart={handleRestart}
        />
      )}

      {uiPhase === PHASE.EXPIRED && (
        <ErrorScreen
          title="Game Expired"
          message="This session was cleared to make room for new games. Start a fresh one — it only takes a second."
          actionLabel="Start New Game"
          onAction={handleRestart}
        />
      )}

      {uiPhase === PHASE.HARD_ERROR && (
        <ErrorScreen
          title="Server Unreachable"
          message="Cannot connect to the backend. Check that the server is running, then try again."
          actionLabel="Back to Setup"
          onAction={handleRestart}
        />
      )}
    </div>
  );
}
