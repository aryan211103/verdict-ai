const CELL_LABELS = {
  TL:'Top Left',TC:'Top Centre',TR:'Top Right',
  ML:'Mid Left',MC:'Centre',   MR:'Mid Right',
  BL:'Bot Left',BC:'Bot Centre',BR:'Bot Right',
};

export default function WinnerScreen({ session, lastOutcome, onRestart }) {
  const winner  = session.winner;
  const entries = Object.entries(session.score);

  return (
    <div className="winner-screen">
      <div className="winner-badge">🏆</div>
      <h2 className="winner-name">{winner} win!</h2>

      <div className="final-score">
        {entries.map(([team, goals]) => (
          <span key={team} className={`final-item ${team === winner ? 'bold' : ''}`}>
            {team} {goals}
          </span>
        ))}
      </div>

      {lastOutcome && (
        <div className="clincher">
          <p>Clinched by:</p>
          <p className="clincher-detail">
            {lastOutcome.player} to <strong>{CELL_LABELS[lastOutcome.cell]}</strong>
            {' — '}{lastOutcome.goal ? '⚽ GOAL' : '✋ SAVED'}
          </p>
        </div>
      )}

      <button className="restart-btn" onClick={onRestart}>Play Again</button>
    </div>
  );
}
