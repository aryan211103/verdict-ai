const DIVES = [
  { value: 'L', label: '← Dive Left',  emoji: '🧤' },
  { value: 'C', label: '⬆ Stay Centre', emoji: '🧤' },
  { value: 'R', label: 'Dive Right →',  emoji: '🧤' },
];

export default function KeeperPicker({ onSelect, loading }) {
  return (
    <div className="keeper-picker">
      {DIVES.map(d => (
        <button
          key={d.value}
          className="dive-btn"
          onClick={() => onSelect(d.value)}
          disabled={loading}
        >
          {d.emoji} {d.label}
        </button>
      ))}
    </div>
  );
}
