import { useState } from 'react';
import GoalScene, { ZONE_LABELS } from './GoalScene';

export default function GoalGrid({ onSelect }) {
  const [selected, setSelected] = useState(null);

  return (
    <div className="goal-grid-wrap">
      <div className="goal-scene-card">
        <GoalScene mode="shoot" selected={selected} onZoneClick={setSelected}/>
      </div>

      {selected && (
        <div className="cell-confirm">
          <span className="cell-label">
            Selected: <strong>{ZONE_LABELS[selected]}</strong>
          </span>
          <button className="confirm-btn" onClick={() => onSelect(selected)}>
            Lock it in ✓
          </button>
        </div>
      )}
    </div>
  );
}
