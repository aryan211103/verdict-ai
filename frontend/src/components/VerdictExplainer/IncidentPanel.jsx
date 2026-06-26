import { useState } from 'react';

const CALL_TYPE_LABEL = {
  correct: { label: 'Correct call', cls: 'tag-correct' },
  error:   { label: 'Missed call / Referee error', cls: 'tag-error' },
};

function renderExplanation(text) {
  // Preserve paragraph breaks; bold **text**
  return text.split('\n\n').map((para, i) => {
    const html = para.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    return (
      <p key={i} dangerouslySetInnerHTML={{ __html: html }} />
    );
  });
}

function renderLawText(text) {
  // Law section headers (--- ... ---) get distinct styling
  return text.split('\n\n').map((block, i) => {
    if (block.startsWith('---')) {
      const header = block.split('\n')[0].replace(/---/g, '').trim();
      const body   = block.split('\n').slice(1).join('\n').trim();
      return (
        <div key={i} className="law-section">
          <div className="law-section-header">{header}</div>
          {body && <pre className="law-section-body">{body}</pre>}
        </div>
      );
    }
    return <pre key={i} className="law-section-body">{block}</pre>;
  });
}

export default function IncidentPanel({ incident }) {
  const [showLaw, setShowLaw] = useState(false);

  const { label, cls } = CALL_TYPE_LABEL[incident.call_type] ?? { label: '', cls: '' };

  return (
    <article className="incident-panel">
      {/* ── Header ─────────────────────────────────────────────────── */}
      <div className="panel-header">
        <h2 className="panel-title">{incident.title}</h2>
        <span className={`call-tag ${cls}`}>{label}</span>
      </div>

      <div className="panel-meta">
        <span>{incident.competition}</span>
        <span className="meta-sep">·</span>
        <span>{incident.match}</span>
      </div>

      {/* ── What happened ──────────────────────────────────────────── */}
      <section className="panel-section">
        <h3 className="section-heading">What happened</h3>
        <p className="what-happened">{incident.what_happened}</p>
        <div className="call-box">
          <span className="call-label">Call: </span>
          <span className="call-text">{incident.call}</span>
        </div>
      </section>

      {/* ── Explanation ────────────────────────────────────────────── */}
      <section className="panel-section">
        <h3 className="section-heading">Explanation</h3>
        <div className="explanation-body">
          {renderExplanation(incident.explanation)}
        </div>
        <div className="provenance">
          Grounded in IFAB Laws of the Game ·
          Model: {incident.model_id} ·{' '}
          <button
            className="law-toggle"
            onClick={() => setShowLaw(v => !v)}
          >
            {showLaw ? 'Hide law text ▲' : 'Show injected law text ▼'}
          </button>
        </div>
      </section>

      {/* ── Law text (toggleable) ───────────────────────────────────── */}
      {showLaw && (
        <section className="panel-section law-panel">
          <h3 className="section-heading">
            IFAB Laws injected into the prompt
            <span className="law-note">
              (the only source Verdict AI is permitted to cite)
            </span>
          </h3>
          <div className="law-text-body">
            {renderLawText(incident.law_context_used)}
          </div>
        </section>
      )}
    </article>
  );
}
