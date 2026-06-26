import { useState } from 'react';

// 3×3 grid from shooter's perspective
// Rows: top → bottom.  Columns: left → right (shooter's left/right).
const CELLS = [
  ['TL','TC','TR'],
  ['ML','MC','MR'],
  ['BL','BC','BR'],
];

// Each cell carries a short display name, a strategic type, and a placement
// indicator so a first-time user can see which cells are corners vs centre.
// The corner/centre distinction matters: corners score ~30% even on a matched
// dive; centre scores only ~6% on a match. This is the core tradeoff.
const CELL_META = {
  TL: { short: 'Top Left',    type: 'corner',   icon: '↖' },
  TC: { short: 'Top Centre',  type: 'top-cent', icon: '↑'  },
  TR: { short: 'Top Right',   type: 'corner',   icon: '↗' },
  ML: { short: 'Mid Left',    type: 'side',     icon: '←'  },
  MC: { short: 'Centre',      type: 'center',   icon: '●'  },
  MR: { short: 'Mid Right',   type: 'side',     icon: '→'  },
  BL: { short: 'Bot Left',    type: 'corner',   icon: '↙' },
  BC: { short: 'Bot Centre',  type: 'bot-cent', icon: '↓'  },
  BR: { short: 'Bot Right',   type: 'corner',   icon: '↘' },
};

export default function GoalGrid({ onSelect }) {
  const [selected, setSelected] = useState(null);

  return (
    <div className="goal-grid-wrap">
      <div className="goal-frame">
        {CELLS.map((row, ri) => (
          <div key={ri} className="goal-row">
            {row.map(cell => {
              const meta = CELL_META[cell];
              return (
                <button
                  key={cell}
                  className={`cell-btn cell-${meta.type} ${selected === cell ? 'chosen' : ''}`}
                  onClick={() => setSelected(cell)}
                  aria-label={meta.short}
                >
                  <span className="cell-icon">{meta.icon}</span>
                  <span className="cell-name">{meta.short}</span>
                </button>
              );
            })}
          </div>
        ))}
      </div>

      {selected && (
        <div className="cell-confirm">
          <span className="cell-label">
            Selected: <strong>{CELL_META[selected].short}</strong>
          </span>
          <button className="confirm-btn" onClick={() => onSelect(selected)}>
            Lock it in ✓
          </button>
        </div>
      )}
    </div>
  );
}
