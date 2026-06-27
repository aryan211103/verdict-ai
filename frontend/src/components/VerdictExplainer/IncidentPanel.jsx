import { useState } from 'react';

/* ── Derive a compact summary from existing cached fields ────────────────
 * No new claims. All fields come from the verified incident record.
 */

function firstSentence(text) {
  // Return the first sentence (up to first . or !)
  const m = text.match(/^[^.!?]+[.!?]/);
  return m ? m[0].trim() : text.substring(0, 140).trim() + '…';
}

function extractLawCitations(lawContext) {
  // Parse "--- Law 12 | Serious foul play [page 124, ..." headers
  const re = /Law (\d+)\s*\|\s*([^[]+?)\s*\[/g;
  const names = new Set();
  let m;
  while ((m = re.exec(lawContext)) !== null) {
    names.add(`Law ${m[1]} — ${m[2].trim()}`);
  }
  return [...names];
}

function renderExplanation(text) {
  return text.split('\n\n').map((para, i) => {
    const html = para
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/^>\s*/gm, '');   // strip blockquote markers
    return <p key={i} dangerouslySetInnerHTML={{ __html: html }}/>;
  });
}

function renderLawText(text) {
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

const CALL_TYPE_LABEL = {
  correct: { label: 'Correct call', cls: 'tag-correct' },
  error:   { label: 'Missed call / Referee error', cls: 'tag-error' },
};

export default function IncidentPanel({ incident }) {
  const [showFull, setShowFull] = useState(false);
  const [showLaw,  setShowLaw]  = useState(false);

  const { label, cls } = CALL_TYPE_LABEL[incident.call_type] ?? {};
  const lawCitations   = extractLawCitations(incident.law_context_used);
  const offenceSummary = firstSentence(incident.what_happened);

  return (
    <article className="incident-panel">

      {/* ── Header ─────────────────────────────────────────────────────── */}
      <div className="panel-header">
        <h2 className="panel-title">{incident.title}</h2>
        <span className={`call-tag ${cls}`}>{label}</span>
      </div>
      <p className="panel-meta">
        {incident.competition}
        <span className="meta-sep">·</span>
        {incident.match}
      </p>

      {/* ── Quick-read summary (derived from verified fields) ───────────── */}
      <section className="summary-card">
        <dl className="summary-dl">
          <div className="summary-row">
            <dt className="summary-key">Offence</dt>
            <dd className="summary-val">{offenceSummary}</dd>
          </div>
          <div className="summary-row">
            <dt className="summary-key">Decision</dt>
            <dd className="summary-val decision-val">{incident.call}</dd>
          </div>
          <div className="summary-row">
            <dt className="summary-key">Law cited</dt>
            <dd className="summary-val">
              {lawCitations.length > 0
                ? lawCitations.join(' · ')
                : 'See explanation below'}
            </dd>
          </div>
        </dl>
      </section>

      {/* ── Full explanation (expandable) ────────────────────────────────── */}
      <section className="panel-section">
        <button
          className="expand-toggle"
          onClick={() => setShowFull(v => !v)}
        >
          {showFull ? 'Hide full explanation ▲' : 'Read full explanation ▼'}
        </button>

        {showFull && (
          <div className="explanation-body">
            {renderExplanation(incident.explanation)}
          </div>
        )}
      </section>

      {/* ── Law text (expandable) ────────────────────────────────────────── */}
      <section className="panel-section">
        <div className="provenance">
          Grounded in IFAB Laws of the Game · Model: {incident.model_id} ·{' '}
          <button
            className="law-toggle"
            onClick={() => setShowLaw(v => !v)}
          >
            {showLaw ? 'Hide law text ▲' : 'Show injected law text ▼'}
          </button>
        </div>

        {showLaw && (
          <div className="law-panel">
            <h3 className="section-heading">
              IFAB Laws injected into the prompt
              <span className="law-note">(the only source Verdict AI is permitted to cite)</span>
            </h3>
            <div className="law-text-body">
              {renderLawText(incident.law_context_used)}
            </div>
          </div>
        )}
      </section>

    </article>
  );
}
