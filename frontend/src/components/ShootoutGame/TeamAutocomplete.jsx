import { useState, useRef, useEffect } from 'react';
import { findTeam } from '../../data/teams';

/**
 * Controlled autocomplete input for a national team name.
 * Cosmetic only — selecting a team fills the name and player slots;
 * no data flows into game resolution logic.
 *
 * Props:
 *   value        string   controlled team name value
 *   onChange     fn(name) called on every keystroke
 *   onTeamSelect fn(team) called when a suggestion is chosen;
 *                         team = { name, color, flag, players }
 *   placeholder  string
 */
export default function TeamAutocomplete({ value, onChange, onTeamSelect, placeholder }) {
  const [open,        setOpen]  = useState(false);
  const [suggestions, setSuggs] = useState([]);
  const [cursor,      setCursor] = useState(-1);
  const listRef = useRef(null);

  useEffect(() => {
    const matches = value.trim().length > 0 ? findTeam(value) : [];
    setSuggs(matches);
    setCursor(-1);
  }, [value]);

  function select(team) {
    onTeamSelect(team);
    setOpen(false);
  }

  function handleKey(e) {
    if (!open || suggestions.length === 0) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setCursor(c => Math.min(c + 1, suggestions.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setCursor(c => Math.max(c - 1, 0));
    } else if (e.key === 'Enter' && cursor >= 0) {
      e.preventDefault();
      select(suggestions[cursor]);
    } else if (e.key === 'Escape') {
      setOpen(false);
    }
  }

  // Scroll active item into view
  useEffect(() => {
    if (cursor >= 0 && listRef.current) {
      listRef.current.children[cursor]?.scrollIntoView({ block: 'nearest' });
    }
  }, [cursor]);

  return (
    <div className="autocomplete-wrap" onBlur={e => {
      if (!e.currentTarget.contains(e.relatedTarget)) setOpen(false);
    }}>
      <input
        className="ac-input"
        value={value}
        placeholder={placeholder ?? 'Team name…'}
        onChange={e => { onChange(e.target.value); setOpen(true); }}
        onFocus={() => setOpen(true)}
        onKeyDown={handleKey}
        autoComplete="off"
      />
      {open && suggestions.length > 0 && (
        <ul className="ac-list" ref={listRef} role="listbox">
          {suggestions.map((t, i) => (
            <li
              key={t.name}
              role="option"
              className={`ac-item ${i === cursor ? 'ac-item-active' : ''}`}
              onMouseDown={() => select(t)}
              style={{ '--team-color': t.color }}
            >
              <span className="ac-flag">{t.flag}</span>
              <span className="ac-name">{t.name}</span>
              <span className="ac-dot" />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
