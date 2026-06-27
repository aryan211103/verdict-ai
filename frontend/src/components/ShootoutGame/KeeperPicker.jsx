import GoalScene from './GoalScene';

const DIVE_LABELS = { L: '← Dive Left', C: '⬆ Stay Centre', R: 'Dive Right →' };

export default function KeeperPicker({ onSelect, loading }) {
  return (
    <div className="goal-grid-wrap">
      <div className="goal-scene-card">
        <GoalScene
          mode="dive"
          selected={null}
          onZoneClick={onSelect}   // direct — no confirmation step for keeper
          loading={loading}
        />
      </div>
      <p className="dive-hint">Tap a third of the goal to cover it — same orientation as the shooter sees</p>
    </div>
  );
}
