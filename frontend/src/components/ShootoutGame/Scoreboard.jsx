export default function Scoreboard({ session, teamColors = {} }) {
  if (!session) return null;
  const entries = Object.entries(session.score);
  const taken   = session.kicks_taken;
  const phase   = session.phase === 'sudden_death'
    ? '⚡ SD'
    : `Round ${Math.ceil((Object.values(taken).reduce((a, b) => a + b, 0) + 1) / 2)}`;

  return (
    <div className="scoreboard">
      {entries.map(([team, goals]) => {
        const color = teamColors[team];
        return (
          <span
            key={team}
            className="score-item"
            style={color ? { borderBottom: `2px solid ${color}`, paddingBottom: '2px' } : {}}
          >
            <span className="team-tag" style={color ? { color } : {}}>{team}</span>
            <span className="score-num">{goals}</span>
            <span className="kicks-tag">({taken[team]} kicks)</span>
          </span>
        );
      })}
      <span className="phase-tag">{phase}</span>
    </div>
  );
}
