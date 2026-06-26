const BADGE = { correct: 'Correct call', error: 'Missed call / Error' };
const BADGE_CLASS = { correct: 'badge-correct', error: 'badge-error' };

export default function IncidentPicker({ incidents, selected, onSelect }) {
  return (
    <nav className="incident-nav">
      <h2 className="nav-heading">Incidents</h2>
      <ul className="incident-list">
        {incidents.map(inc => (
          <li key={inc.incident_id}>
            <button
              className={`incident-btn ${selected === inc.incident_id ? 'active' : ''}`}
              onClick={() => onSelect(inc.incident_id)}
            >
              <span className="incident-name">{inc.title}</span>
              <span className={`call-badge ${BADGE_CLASS[inc.call_type]}`}>
                {BADGE[inc.call_type]}
              </span>
            </button>
          </li>
        ))}
      </ul>
    </nav>
  );
}
