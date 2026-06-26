import { useState } from 'react';
import { PRESETS }         from '../../data/presets';
import { TEAMS, teamColor } from '../../data/teams';
import TeamAutocomplete    from './TeamAutocomplete';

function defaultCustom() {
  return { team_name: '', color: null, players: ['', '', '', '', ''] };
}

export default function SetupScreen({ onDone, loading }) {
  const [presetId, setPresetId] = useState(PRESETS[0].id);
  const [customA,  setCustomA]  = useState(defaultCustom());
  const [customB,  setCustomB]  = useState(defaultCustom());
  const [mode,     setMode]     = useState('1v1');

  const preset   = PRESETS.find(p => p.id === presetId);
  const isCustom = presetId === 'custom';

  // Called when user types in a custom team-name field
  function setCustomName(side, name) {
    const setter = side === 'A' ? setCustomA : setCustomB;
    setter(prev => ({ ...prev, team_name: name, color: teamColor(name) }));
  }

  // Called when user picks a suggestion — fills name + players
  function handleTeamSelect(side, team) {
    const setter = side === 'A' ? setCustomA : setCustomB;
    setter({
      team_name: team.name,
      color:     team.color,
      players:   [...team.players],  // editable copy
    });
  }

  function updatePlayer(side, idx, val) {
    const setter = side === 'A' ? setCustomA : setCustomB;
    setter(prev => {
      const players = [...prev.players];
      players[idx] = val;
      return { ...prev, players };
    });
  }

  function handleStart() {
    let teamA, teamB, colorA, colorB;
    if (isCustom) {
      teamA  = { team_name: customA.team_name || 'Team A', players: customA.players.map((p,i) => p || `Player ${i+1}`) };
      teamB  = { team_name: customB.team_name || 'Team B', players: customB.players.map((p,i) => p || `Player ${i+1}`) };
      colorA = customA.color;
      colorB = customB.color;
    } else {
      teamA  = preset.teamA;
      teamB  = preset.teamB;
      colorA = TEAMS.find(t => t.name === preset.teamA.team_name)?.color ?? null;
      colorB = TEAMS.find(t => t.name === preset.teamB.team_name)?.color ?? null;
    }
    onDone(teamA, teamB, mode, colorA, colorB);
  }

  return (
    <div className="setup-screen">
      <div className="setup-hero">
        <h1 className="title">Verdict AI</h1>
        <p className="subtitle">Penalty Shootout — Relive and rewrite the moment</p>
      </div>

      <div className="preset-grid">
        {PRESETS.map(p => (
          <button
            key={p.id}
            className={`preset-btn ${presetId === p.id ? 'active' : ''}`}
            onClick={() => setPresetId(p.id)}
          >
            {p.label}
          </button>
        ))}
      </div>

      {!isCustom && preset && (
        <div className="preset-preview">
          <TeamPreview team={preset.teamA} />
          <span className="vs">vs</span>
          <TeamPreview team={preset.teamB} />
        </div>
      )}

      {isCustom && (
        <div className="custom-grid">
          <CustomTeamForm
            label="Team A"
            data={customA}
            onNameChange={v => setCustomName('A', v)}
            onTeamSelect={t => handleTeamSelect('A', t)}
            onPlayerChange={(i, v) => updatePlayer('A', i, v)}
          />
          <CustomTeamForm
            label="Team B"
            data={customB}
            onNameChange={v => setCustomName('B', v)}
            onTeamSelect={t => handleTeamSelect('B', t)}
            onPlayerChange={(i, v) => updatePlayer('B', i, v)}
          />
        </div>
      )}

      <div className="mode-toggle">
        <span className="mode-label">Mode:</span>
        <button className={`mode-btn ${mode === '1v1'   ? 'active' : ''}`} onClick={() => setMode('1v1')}>
          👥 1v1 — Pass the device
        </button>
        <button className={`mode-btn ${mode === 'vs_ai' ? 'active' : ''}`} onClick={() => setMode('vs_ai')}>
          🤖 vs AI Keeper
        </button>
      </div>

      {mode === 'vs_ai' && (
        <div className="ai-mode-note">
          AI keeper learns your pattern this game — half random, half tracking where you've been shooting.
        </div>
      )}

      <div className="honesty-note">
        Player names are cosmetic labels — they don't affect kick probabilities.
      </div>

      <button className="start-btn" onClick={handleStart} disabled={loading}>
        {loading ? 'Starting…' : '⚽  Start Shootout'}
      </button>
    </div>
  );
}

function TeamPreview({ team }) {
  const color = TEAMS.find(t => t.name === team.team_name)?.color;
  const flag  = TEAMS.find(t => t.name === team.team_name)?.flag ?? '';
  return (
    <div className="team-preview" style={color ? { borderLeftColor: color } : {}}>
      <div className="team-name">{flag && <span className="preview-flag">{flag} </span>}{team.team_name}</div>
      <ol className="player-list">
        {team.players.map((p, i) => <li key={i}>{p}</li>)}
      </ol>
    </div>
  );
}

function CustomTeamForm({ label, data, onNameChange, onTeamSelect, onPlayerChange }) {
  return (
    <div className="custom-team">
      <div className="custom-team-label">{label}</div>

      {/* Team name with autocomplete */}
      <TeamAutocomplete
        value={data.team_name}
        onChange={onNameChange}
        onTeamSelect={onTeamSelect}
        placeholder="Type a country name…"
      />

      {/* Player slots — auto-filled when a team is selected, remain editable */}
      <div className="player-slots">
        {data.players.map((p, i) => (
          <input
            key={i}
            className="player-input"
            placeholder={`Player ${i + 1}`}
            value={p}
            onChange={e => onPlayerChange(i, e.target.value)}
          />
        ))}
      </div>
    </div>
  );
}
