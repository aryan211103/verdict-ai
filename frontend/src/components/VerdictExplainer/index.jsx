import { useState } from 'react';
import IncidentPicker  from './IncidentPicker';
import IncidentPanel   from './IncidentPanel';
import explanations    from '../../data/explanations.json';
import './verdict.css';

export default function VerdictExplainer() {
  const [selected, setSelected] = useState(null);

  const incident = selected
    ? explanations.find(e => e.incident_id === selected)
    : null;

  return (
    <div className="verdict-root">
      <header className="verdict-header">
        <h1 className="verdict-title">Verdict AI</h1>
        <p className="verdict-sub">
          Real incidents explained through the IFAB Laws of the Game
        </p>
      </header>

      <div className="verdict-body">
        <IncidentPicker
          incidents={explanations}
          selected={selected}
          onSelect={setSelected}
        />

        {incident ? (
          <IncidentPanel incident={incident} />
        ) : (
          <div className="verdict-placeholder">
            <p>Select an incident to read the explanation and the law text it is grounded in.</p>
          </div>
        )}
      </div>
    </div>
  );
}
