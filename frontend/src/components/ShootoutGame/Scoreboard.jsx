/**
 * Scoreboard — broadcast scoreline.
 * Styled to match the setup page's neutral-dark / condensed-type treatment.
 * No logic change — reads session.score, session.kicks_taken, session.phase.
 */
export default function Scoreboard({ session, teamColors = {} }) {
  if (!session) return null;

  const entries = Object.entries(session.score);   // [[teamA, goalsA], [teamB, goalsB]]
  const taken   = session.kicks_taken;
  const isSD    = session.phase === 'sudden_death';
  const total   = Object.values(taken).reduce((a, b) => a + b, 0);
  const round   = isSD ? null : Math.ceil((total + 1) / 2);

  const [nameA, goalsA] = entries[0] ?? ['—', 0];
  const [nameB, goalsB] = entries[1] ?? ['—', 0];
  const colorA = teamColors[nameA] ?? null;
  const colorB = teamColors[nameB] ?? null;
  const kicksA = taken[nameA] ?? 0;
  const kicksB = taken[nameB] ?? 0;

  return (
    <div className="scoreboard">

      {/* ── Left team ─────────────────────────────── */}
      <div className="sb-team sb-left"
           style={colorA ? { '--tc': colorA } : {}}>
        <span className="sb-name">{nameA}</span>
        <span className="sb-kicks">{kicksA} kick{kicksA !== 1 ? 's' : ''}</span>
      </div>

      {/* ── Score centre ──────────────────────────── */}
      <div className="sb-centre">
        <span className="sb-score" style={colorA ? { color: colorA } : {}}>{goalsA}</span>
        <div className="sb-mid">
          <span className="sb-dash">—</span>
          <span className="sb-phase">
            {isSD ? '⚡ SUDDEN DEATH' : `ROUND ${round}`}
          </span>
        </div>
        <span className="sb-score" style={colorB ? { color: colorB } : {}}>{goalsB}</span>
      </div>

      {/* ── Right team ────────────────────────────── */}
      <div className="sb-team sb-right"
           style={colorB ? { '--tc': colorB } : {}}>
        <span className="sb-kicks">{kicksB} kick{kicksB !== 1 ? 's' : ''}</span>
        <span className="sb-name">{nameB}</span>
      </div>

    </div>
  );
}
