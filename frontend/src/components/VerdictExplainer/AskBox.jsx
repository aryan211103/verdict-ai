export default function AskBox({ query, onChange }) {
  return (
    <div className="ask-wrap">
      <div className="ask-icon">⚖️</div>
      <input
        className="ask-input"
        type="text"
        value={query}
        onChange={e => onChange(e.target.value)}
        placeholder="Ask: 'Maradona handball' · 'Why did Suárez get a red card?' · 'Zidane headbutt'…"
        aria-label="Search verified incidents"
      />
      {query && (
        <button className="ask-clear" onClick={() => onChange('')} aria-label="Clear">✕</button>
      )}
    </div>
  );
}
