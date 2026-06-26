import { useState } from 'react';
import ShootoutGame     from './components/ShootoutGame/index';
import VerdictExplainer from './components/VerdictExplainer/index';
import './app-nav.css';

const FEATURES = [
  { id: 'game',    label: '⚽ Penalty Shootout' },
  { id: 'verdict', label: '⚖️ VAR Explainer'    },
];

export default function App() {
  const [feature, setFeature] = useState('game');

  return (
    <>
      <nav className="feature-nav">
        {FEATURES.map(f => (
          <button
            key={f.id}
            className={`feature-btn ${feature === f.id ? 'active' : ''}`}
            onClick={() => setFeature(f.id)}
          >
            {f.label}
          </button>
        ))}
      </nav>
      {feature === 'game'    && <ShootoutGame />}
      {feature === 'verdict' && <VerdictExplainer />}
    </>
  );
}
