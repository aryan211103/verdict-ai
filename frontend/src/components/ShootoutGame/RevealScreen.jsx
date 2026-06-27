import { useEffect, useState } from 'react';

const CELL_LABELS = {
  TL:'Top Left',  TC:'Top Centre',  TR:'Top Right',
  ML:'Mid Left',  MC:'Centre',      MR:'Mid Right',
  BL:'Bot Left',  BC:'Bot Centre',  BR:'Bot Right',
};
const DIVE_LABELS = { L:'Left', C:'Centre', R:'Right' };

export default function RevealScreen({ outcome, session, teamColors = {}, onNext, aiPanel = null }) {
  const goal    = outcome.goal;
  const matched = outcome.matched;
  // Keeper guessed wrong AND ball still didn't go in → shooter missed, not a save.
  const isMiss  = !goal && !matched;

  // Trigger entrance animation on mount
  const [visible, setVisible] = useState(false);
  useEffect(() => { requestAnimationFrame(() => setVisible(true)); }, []);

  const shooterLine = `${outcome.player} → ${CELL_LABELS[outcome.cell]}`;
  const keeperLine  = `Keeper dived ${DIVE_LABELS[outcome.dive]}`;
  const matchLine   = matched ? 'Keeper guessed correctly' : 'Keeper guessed wrong';

  const entries  = Object.entries(session.score);
  const scoreA   = entries[0];
  const scoreB   = entries[1];
  const nextTeam = session.current_team;

  const colorA = teamColors[scoreA?.[0]];
  const colorB = teamColors[scoreB?.[0]];

  const resultClass = goal
    ? `reveal-screen reveal-goal ${visible ? 'reveal-enter' : 'reveal-hidden'}`
    : `reveal-screen reveal-save ${visible ? 'reveal-enter' : 'reveal-hidden'}`;

  return (
    <div className={resultClass}>
      {/* Animated result badge */}
      <div className={`result-badge ${goal ? 'badge-goal-anim' : 'badge-save-anim'}`}>
        {goal ? '⚽' : isMiss ? '❌' : '🧤'}
        <span className="result-word">{goal ? ' GOAL!' : isMiss ? ' MISSED' : ' SAVED!'}</span>
      </div>

      <div className="reveal-detail">
        <div className="reveal-row">⚽ {shooterLine}</div>
        <div className="reveal-row">🧤 {keeperLine}</div>
        <div className="reveal-row dim">{matchLine}</div>
        <div className="reveal-row dim">
          {isMiss
            ? `${(outcome.p_goal * 100).toFixed(0)}% goal chance — but the ${(100 - outcome.p_goal * 100).toFixed(0)}% came up. No goal.`
            : `P(goal) was ${(outcome.p_goal * 100).toFixed(0)}% — resolved by a single random draw`
          }
        </div>
      </div>

      <div className="score-display">
        <span style={colorA ? { color: colorA } : {}}>
          {scoreA?.[0]} <strong>{scoreA?.[1]}</strong>
        </span>
        <span className="score-sep">–</span>
        <span style={colorB ? { color: colorB } : {}}>
          <strong>{scoreB?.[1]}</strong> {scoreB?.[0]}
        </span>
      </div>

      {session.phase === 'sudden_death' && (
        <div className="phase-badge">⚡ Sudden Death</div>
      )}

      {aiPanel}

      <button className="next-btn" onClick={onNext}>
        Next kick: {nextTeam} →
      </button>
    </div>
  );
}
