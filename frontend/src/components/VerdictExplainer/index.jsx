import { useState } from 'react';
import AskBox         from './AskBox';
import IncidentPicker from './IncidentPicker';
import IncidentPanel  from './IncidentPanel';
import { searchIncidents } from './search';
import explanations    from '../../data/explanations.json';
import './verdict.css';

export default function VerdictExplainer() {
  // Auto-select the first incident on load — no empty void on arrival
  const [selected, setSelected]   = useState(explanations[0]?.incident_id ?? null);
  const [query,    setQuery]       = useState('');
  const [noMatch,  setNoMatch]     = useState(false);

  const incident = selected
    ? explanations.find(e => e.incident_id === selected)
    : null;

  function handleSearch(q) {
    setQuery(q);
    if (!q.trim()) {
      // Clear search — restore first incident
      setNoMatch(false);
      setSelected(explanations[0]?.incident_id ?? null);
      return;
    }
    const match = searchIncidents(q, explanations);
    if (match) {
      setSelected(match.incident_id);
      setNoMatch(false);
    } else {
      setSelected(null);
      setNoMatch(true);
    }
  }

  function selectIncident(id) {
    setSelected(id);
    setQuery('');
    setNoMatch(false);
  }

  return (
    <div className="verdict-root">

      {/* ── Header ─────────────────────────────────────────────────────── */}
      <header className="verdict-header">
        <div className="verdict-header-top">
          <h1 className="verdict-title">Verdict AI</h1>
          <p className="verdict-sub">
            10 landmark incidents · each explained through the IFAB Laws of the Game
          </p>
        </div>
        <AskBox query={query} onChange={handleSearch} />
      </header>

      {/* ── No-match message ───────────────────────────────────────────── */}
      {noMatch && (
        <div className="no-match-banner">
          <span className="no-match-text">
            No verified incident matches <strong>"{query}"</strong> — browse below or try another search.
          </span>
        </div>
      )}

      {/* ── Body ───────────────────────────────────────────────────────── */}
      <div className="verdict-body">

        {/* Incident list — primary browse + search-matched highlight */}
        <nav className="incident-nav">
          <h2 className="nav-heading">
            {noMatch ? 'All incidents' : 'Incidents'}
          </h2>
          <IncidentPicker
            incidents={explanations}
            selected={selected}
            onSelect={selectIncident}
          />
        </nav>

        {/* Panel — explanation or empty-state */}
        <main className="verdict-panel-area">
          {incident ? (
            <IncidentPanel incident={incident} />
          ) : (
            <div className="verdict-placeholder">
              <p>Select an incident from the list, or type a question above.</p>
            </div>
          )}
        </main>

      </div>
    </div>
  );
}
