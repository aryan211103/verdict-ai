// AI panel for Mode B (vs_ai).
// Shows ONLY session shot counts and the half-guessing disclaimer.
// Never ties the AI's behaviour to a player name or real statistics.

export default function AIPanel({ counts, lastDive }) {
  const total = counts ? Object.values(counts).reduce((a, b) => a + b, 0) : 0;

  return (
    <div className="ai-panel">
      <div className="ai-header">
        <span className="ai-icon">🤖</span>
        <span className="ai-title">AI Keeper</span>
      </div>

      <div className="ai-counts">
        {['L', 'C', 'R'].map(dir => {
          const n   = counts?.[dir] ?? 0;
          const pct = total > 0 ? Math.round(100 * n / total) : 0;
          const label = dir === 'L' ? '← Left' : dir === 'R' ? 'Right →' : '● Centre';
          const isLast = lastDive === dir;
          return (
            <div key={dir} className={`ai-dir ${isLast ? 'ai-last-dive' : ''}`}>
              <span className="ai-dir-label">{label}</span>
              <span className="ai-dir-count">{n}</span>
              <div className="ai-bar-wrap">
                <div className="ai-bar" style={{ width: `${pct}%` }} />
              </div>
              {isLast && <span className="ai-dived-tag">dived here ↑</span>}
            </div>
          );
        })}
        <div className="ai-total">Your shots this game: {total}</div>
      </div>

      <div className="ai-disclaimer">
        Half guessing, half tracking where you've been shooting <em>this game</em>.
        No data about real players.
      </div>
    </div>
  );
}
