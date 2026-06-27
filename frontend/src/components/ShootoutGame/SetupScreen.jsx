import { useState } from 'react';
import { PRESETS }         from '../../data/presets';
import { TEAMS, teamColor } from '../../data/teams';
import TeamAutocomplete    from './TeamAutocomplete';

function defaultCustom() {
  return { team_name: '', color: null, players: ['', '', '', '', ''] };
}

/* ── Faint goal-net watermark — decorative only ──────────────────────── */
function GoalWatermark() {
  const vLines = [60,90,120,150,180,210,240,270,300,330];
  const hLines = [30,56,82,108,134];
  return (
    <svg className="hero-watermark-svg" viewBox="0 0 380 160"
         xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      {/* Posts */}
      <line x1="24"  y1="4"  x2="24"  y2="156" stroke="white" strokeWidth="5" strokeLinecap="round"/>
      <line x1="356" y1="4"  x2="356" y2="156" stroke="white" strokeWidth="5" strokeLinecap="round"/>
      {/* Crossbar */}
      <line x1="21"  y1="6"  x2="359" y2="6"   stroke="white" strokeWidth="5" strokeLinecap="round"/>
      {/* Net horizontal */}
      {hLines.map(y => (
        <line key={y} x1="24" y1={y} x2="356" y2={y}
              stroke="white" strokeWidth="0.8" opacity="0.55"/>
      ))}
      {/* Net vertical */}
      {vLines.map(x => (
        <line key={x} x1={x} y1="6" x2={x} y2="156"
              stroke="white" strokeWidth="0.8" opacity="0.55"/>
      ))}
    </svg>
  );
}

/* ── Broadcast stat cell ─────────────────────────────────────────────── */
function Stat({ label, value }) {
  return (
    <div className="hero-stat">
      <span className="hero-stat-value">{value}</span>
      <span className="hero-stat-label">{label}</span>
    </div>
  );
}

/* ── Matchup team card ───────────────────────────────────────────────── */
function MatchupCard({ team, side }) {
  const color = TEAMS.find(t => t.name === team.team_name)?.color ?? null;
  const flag  = TEAMS.find(t => t.name === team.team_name)?.flag  ?? '';
  return (
    <div className={`matchup-card matchup-${side}`}
         style={color ? { '--mc-accent': color } : {}}>
      {flag && <span className="matchup-flag">{flag}</span>}
      <div className="matchup-name">{team.team_name}</div>
      <div className="matchup-rule"/>
      <ol className="matchup-players">
        {team.players.map((p, i) => <li key={i}>{p}</li>)}
      </ol>
    </div>
  );
}

/* ── Main setup screen ───────────────────────────────────────────────── */
export default function SetupScreen({ onDone, loading }) {
  const [presetId, setPresetId] = useState(PRESETS[0].id);
  const [customA,  setCustomA]  = useState(defaultCustom());
  const [customB,  setCustomB]  = useState(defaultCustom());
  const [mode,     setMode]     = useState('1v1');

  const preset   = PRESETS.find(p => p.id === presetId);
  const isCustom = presetId === 'custom';

  /* Derived names for the hero matchup title */
  const nameA = isCustom
    ? (customA.team_name?.toUpperCase() || 'TEAM A')
    : preset.teamA.team_name.toUpperCase();
  const nameB = isCustom
    ? (customB.team_name?.toUpperCase() || 'TEAM B')
    : preset.teamB.team_name.toUpperCase();

  function setCustomName(side, name) {
    const setter = side === 'A' ? setCustomA : setCustomB;
    setter(prev => ({ ...prev, team_name: name, color: teamColor(name) }));
  }

  function handleTeamSelect(side, team) {
    const setter = side === 'A' ? setCustomA : setCustomB;
    setter({ team_name: team.name, color: team.color, players: [...team.players] });
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

      {/* ── HERO BANNER ──────────────────────────────────────────────── */}
      <div className="setup-hero-banner">
        <GoalWatermark />
        <div className="hero-body">
          <div className="hero-left">
            <p className="hero-eyebrow">PENALTY SHOOTOUT · RELIVE &amp; REWRITE THE MOMENT</p>
            <h1 className="hero-matchup">
              <span className="hero-team-a">{nameA}</span>
              <span className="hero-vs">vs</span>
              <span className="hero-team-b">{nameB}</span>
            </h1>
          </div>
          <div className="hero-stats">
            <Stat label="ROUNDS"  value="5" />
            <Stat label="FORMAT"  value="Best of 5" />
            <Stat label="MODE"    value={mode === '1v1' ? '1v1' : 'vs AI'} />
            <Stat label="KICKS"   value="5 / side" />
          </div>
        </div>
      </div>

      {/* ── PRESET CHIPS ─────────────────────────────────────────────── */}
      <div className="setup-section">
        <div className="section-eyebrow">SELECT MATCH</div>
        <div className="preset-chips" role="tablist">
          {PRESETS.map(p => (
            <button
              key={p.id}
              role="tab"
              aria-selected={presetId === p.id}
              className={`preset-chip ${presetId === p.id ? 'active' : ''}`}
              onClick={() => setPresetId(p.id)}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── MATCHUP CARDS ────────────────────────────────────────────── */}
      {!isCustom && preset && (
        <div className="matchup-row">
          <MatchupCard team={preset.teamA} side="home" />
          <div className="matchup-vs-center">
            <span className="matchup-vs-text">VS</span>
          </div>
          <MatchupCard team={preset.teamB} side="away" />
        </div>
      )}

      {/* ── CUSTOM TEAM FORM ──────────────────────────────────────────── */}
      {isCustom && (
        <div className="custom-matchup">
          <CustomTeamForm
            label="HOME"
            data={customA}
            onNameChange={v => setCustomName('A', v)}
            onTeamSelect={t => handleTeamSelect('A', t)}
            onPlayerChange={(i, v) => updatePlayer('A', i, v)}
          />
          <div className="matchup-vs-center">
            <span className="matchup-vs-text">VS</span>
          </div>
          <CustomTeamForm
            label="AWAY"
            data={customB}
            onNameChange={v => setCustomName('B', v)}
            onTeamSelect={t => handleTeamSelect('B', t)}
            onPlayerChange={(i, v) => updatePlayer('B', i, v)}
          />
        </div>
      )}

      {/* ── MODE SEGMENT ──────────────────────────────────────────────── */}
      <div className="setup-section">
        <div className="section-eyebrow">GAME MODE</div>
        <div className="mode-segment" role="group">
          <button
            className={`mode-seg-btn ${mode === '1v1' ? 'active' : ''}`}
            onClick={() => setMode('1v1')}
          >
            👥&nbsp;&nbsp;1v1 — Pass the device
          </button>
          <button
            className={`mode-seg-btn ${mode === 'vs_ai' ? 'active' : ''}`}
            onClick={() => setMode('vs_ai')}
          >
            🤖&nbsp;&nbsp;vs AI Keeper
          </button>
        </div>
        {mode === 'vs_ai' && (
          <p className="ai-mode-note">
            AI keeper learns where you've been shooting this game — half random, half pattern.
          </p>
        )}
      </div>

      {/* ── FOOTER ────────────────────────────────────────────────────── */}
      <div className="setup-footer">
        <p className="honesty-note">
          Player names are cosmetic labels — they don't affect kick probabilities.
        </p>
        <button className="start-btn" onClick={handleStart} disabled={loading}>
          {loading ? 'Starting…' : 'START SHOOTOUT'}
        </button>
      </div>

    </div>
  );
}

function CustomTeamForm({ label, data, onNameChange, onTeamSelect, onPlayerChange }) {
  return (
    <div className="custom-team-col">
      <div className="custom-team-label">{label}</div>
      <TeamAutocomplete
        value={data.team_name}
        onChange={onNameChange}
        onTeamSelect={onTeamSelect}
        placeholder="Country name…"
      />
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
