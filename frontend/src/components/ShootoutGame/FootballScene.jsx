/**
 * FootballScene — static SVG penalty scene (Stage 2).
 * Contains: pitch markings, goal with net, stylized keeper and kicker
 * silhouettes, ball on penalty spot, and 9 clickable zones overlaid on
 * the goal mouth.
 *
 * Stage: STATIC. No diving or ball-flight animation yet.
 * Logic: purely presentational. onZoneClick(cellId) is the only output.
 */
import { useState } from 'react';

/* ── Goal geometry ─────────────────────────────────────────────────────────
 * All coordinates in SVG user units, viewBox "0 0 400 300".
 * The goal spans most of the upper portion; the pitch and spot below.
 */
const G = {
  left:   62,
  right:  338,
  top:    20,
  bottom: 180,
  get w()  { return this.right - this.left; },   // 276
  get h()  { return this.bottom - this.top; },   // 160
  get cw() { return this.w / 3; },               // 92
  get rh() { return this.h / 3; },               // 53.3
};

const SPOT = { cx: 200, cy: 248 };

/* ── Zone definitions ──────────────────────────────────────────────────── */
const ZONES = [
  { id: 'TL', label: 'Top Left',   col: 0, row: 0, kind: 'corner' },
  { id: 'TC', label: 'Top Centre', col: 1, row: 0, kind: 'edge'   },
  { id: 'TR', label: 'Top Right',  col: 2, row: 0, kind: 'corner' },
  { id: 'ML', label: 'Mid Left',   col: 0, row: 1, kind: 'side'   },
  { id: 'MC', label: 'Centre',     col: 1, row: 1, kind: 'center' },
  { id: 'MR', label: 'Mid Right',  col: 2, row: 1, kind: 'side'   },
  { id: 'BL', label: 'Bot Left',   col: 0, row: 2, kind: 'corner' },
  { id: 'BC', label: 'Bot Centre', col: 1, row: 2, kind: 'edge'   },
  { id: 'BR', label: 'Bot Right',  col: 2, row: 2, kind: 'corner' },
];

export default function FootballScene({ selected, onZoneClick }) {
  const [hovered, setHovered] = useState(null);

  return (
    <svg
      viewBox="0 0 400 300"
      style={{ width: '100%', maxWidth: 440, display: 'block', userSelect: 'none' }}
      aria-label="Penalty goal — tap a zone to select your shot placement"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        {/* Net mesh — subtle diagonal/grid inside goal */}
        <pattern id="netMesh" x={G.left} y={G.top} width="18" height="18" patternUnits="userSpaceOnUse">
          <path d="M 0,0 L 0,18 M 0,0 L 18,0"
                stroke="rgba(255,255,255,0.11)" strokeWidth="0.7" fill="none"/>
        </pattern>

        {/* Mow-stripe pitch pattern — horizontal bands */}
        <pattern id="mowStripes" x="0" y="0" width="400" height="60" patternUnits="userSpaceOnUse">
          <rect width="400" height="30" fill="#1e4820"/>
          <rect y="30" width="400" height="30" fill="#1a3d1c"/>
        </pattern>

        {/* Goal-mouth gradient — slight vignette into net depth */}
        <linearGradient id="goalDepth" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%"   stopColor="#060e06"/>
          <stop offset="100%" stopColor="#0c1a0c"/>
        </linearGradient>

        {/* Zone hover shadow */}
        <filter id="zoneShadow">
          <feDropShadow dx="0" dy="0" stdDeviation="3" floodColor="#4ade80" floodOpacity="0.5"/>
        </filter>
      </defs>

      {/* ── PITCH SURFACE ────────────────────────────────────────────────── */}
      <rect width="400" height="300" fill="#1a3d1c"/>
      <rect width="400" height="300" fill="url(#mowStripes)" opacity="0.65"/>

      {/* ── PENALTY AREA MARKINGS ────────────────────────────────────────── */}
      {/* Penalty area (18-yard box) */}
      <rect x="38" y={G.bottom} width="324" height="90"
            fill="none" stroke="rgba(255,255,255,0.50)" strokeWidth="1.5"/>
      {/* 6-yard box */}
      <rect x="118" y={G.bottom} width="164" height="38"
            fill="none" stroke="rgba(255,255,255,0.30)" strokeWidth="1"/>
      {/* Goal line (flush with bottom of goal) */}
      <line x1={G.left} y1={G.bottom} x2={G.right} y2={G.bottom}
            stroke="rgba(255,255,255,0.65)" strokeWidth="2"/>
      {/* Penalty arc — D */}
      <path d={`M 114,${G.bottom} A 88,88 0 0,0 286,${G.bottom}`}
            fill="none" stroke="rgba(255,255,255,0.40)" strokeWidth="1.5"/>

      {/* ── PENALTY SPOT ─────────────────────────────────────────────────── */}
      <circle cx={SPOT.cx} cy={SPOT.cy} r="4" fill="rgba(255,255,255,0.70)"/>

      {/* ── GOAL INTERIOR ────────────────────────────────────────────────── */}
      {/* Dark interior — back of net in shadow */}
      <rect x={G.left} y={G.top} width={G.w} height={G.h}
            fill="url(#goalDepth)"/>
      {/* Net mesh overlay */}
      <rect x={G.left} y={G.top} width={G.w} height={G.h}
            fill="url(#netMesh)"/>

      {/* ── ZONE DIVIDER LINES (faint) ───────────────────────────────────── */}
      {[1, 2].map(col => (
        <line key={`vc${col}`}
              x1={G.left + col * G.cw} y1={G.top}
              x2={G.left + col * G.cw} y2={G.bottom}
              stroke="rgba(255,255,255,0.13)" strokeWidth="1" pointerEvents="none"/>
      ))}
      {[1, 2].map(row => (
        <line key={`hr${row}`}
              x1={G.left} y1={G.top + row * G.rh}
              x2={G.right} y2={G.top + row * G.rh}
              stroke="rgba(255,255,255,0.13)" strokeWidth="1" pointerEvents="none"/>
      ))}

      {/* ── CLICKABLE ZONE OVERLAYS ──────────────────────────────────────── */}
      {ZONES.map(z => {
        const x  = G.left + z.col * G.cw;
        const y  = G.top  + z.row * G.rh;
        const sel = selected === z.id;
        const hov = hovered  === z.id;

        return (
          <g key={z.id}
             onClick={() => onZoneClick(z.id)}
             onMouseEnter={() => setHovered(z.id)}
             onMouseLeave={() => setHovered(null)}
             style={{ cursor: 'pointer' }}>
            {/* Main clickable fill */}
            <rect
              x={x} y={y} width={G.cw} height={G.rh}
              fill={
                sel ? 'rgba(58,122,58,0.55)'
                : hov ? 'rgba(255,255,255,0.09)'
                : 'transparent'
              }
            />
            {/* Selected: dashed green border */}
            {sel && (
              <rect x={x+2} y={y+2} width={G.cw-4} height={G.rh-4}
                    fill="none" stroke="rgba(74,222,128,0.85)" strokeWidth="1.5"
                    strokeDasharray="5,3" pointerEvents="none"/>
            )}
            {/* Corner dot — amber hint, indicates hard-to-save zones */}
            {z.kind === 'corner' && !sel && (
              <circle
                cx={x + (z.col === 0 ? 10 : G.cw - 10)}
                cy={y + (z.row === 0 ? 10 : G.rh - 10)}
                r="4" fill="rgba(245,158,11,0.50)" pointerEvents="none"/>
            )}
            {/* Centre dot — muted, easiest to save */}
            {z.kind === 'center' && !sel && (
              <circle cx={x + G.cw / 2} cy={y + G.rh / 2}
                      r="4" fill="rgba(255,255,255,0.18)" pointerEvents="none"/>
            )}
          </g>
        );
      })}

      {/* ── GOALKEEPER SILHOUETTE ────────────────────────────────────────── */}
      <Keeper footY={G.bottom} cx={200}/>

      {/* ── GOAL FRAME (rendered on top so it overlaps keeper/net) ───────── */}
      {/* Shadow under posts for depth */}
      <line x1={G.left + 5} y1={G.top + 6} x2={G.left + 5} y2={G.bottom}
            stroke="rgba(0,0,0,0.35)" strokeWidth="3" strokeLinecap="round"/>
      <line x1={G.right - 5} y1={G.top + 6} x2={G.right - 5} y2={G.bottom}
            stroke="rgba(0,0,0,0.35)" strokeWidth="3" strokeLinecap="round"/>
      {/* Left post */}
      <line x1={G.left} y1={G.top - 2} x2={G.left} y2={G.bottom}
            stroke="white" strokeWidth="7" strokeLinecap="round"/>
      {/* Right post */}
      <line x1={G.right} y1={G.top - 2} x2={G.right} y2={G.bottom}
            stroke="white" strokeWidth="7" strokeLinecap="round"/>
      {/* Crossbar */}
      <line x1={G.left - 3} y1={G.top} x2={G.right + 3} y2={G.top}
            stroke="white" strokeWidth="7" strokeLinecap="round"/>

      {/* ── BALL ─────────────────────────────────────────────────────────── */}
      <circle cx={SPOT.cx} cy={SPOT.cy} r="10" fill="white"
              filter="drop-shadow(0 3px 4px rgba(0,0,0,0.55))"/>
      {/* Simple panel seam lines */}
      <circle cx={SPOT.cx} cy={SPOT.cy} r="10"
              fill="none" stroke="rgba(0,0,0,0.18)" strokeWidth="0.8"/>
      <path d={`M ${SPOT.cx},${SPOT.cy-7}
                C ${SPOT.cx+5},${SPOT.cy-2} ${SPOT.cx+5},${SPOT.cy+3} ${SPOT.cx},${SPOT.cy+7}`}
            stroke="rgba(0,0,0,0.18)" strokeWidth="0.8" fill="none"/>
      <path d={`M ${SPOT.cx},${SPOT.cy-7}
                C ${SPOT.cx-5},${SPOT.cy-2} ${SPOT.cx-5},${SPOT.cy+3} ${SPOT.cx},${SPOT.cy+7}`}
            stroke="rgba(0,0,0,0.18)" strokeWidth="0.8" fill="none"/>

      {/* ── KICKER SILHOUETTE ────────────────────────────────────────────── */}
      <Kicker cx={172} footY={SPOT.cy + 3}/>
    </svg>
  );
}

/**
 * Keeper — stylized broadcast-style silhouette.
 * Standing in goal mouth, arms spread, feet on goal line.
 */
function Keeper({ footY, cx }) {
  const hy = footY - 72;    // head centre Y
  const fill = '#cde3cd';   // pale kit colour — light against dark net

  return (
    <g>
      {/* Head */}
      <circle cx={cx} cy={hy} r={12} fill={fill}/>
      {/* Neck + upper body */}
      <rect x={cx - 6} y={hy + 11} width={12} height={8} rx={2} fill={fill}/>
      {/* Torso — slightly wider at shoulders, tapered to hips */}
      <path d={`
        M ${cx - 17},${hy + 19}
        Q ${cx},${hy + 14}
        ${cx + 17},${hy + 19}
        L ${cx + 14},${hy + 52}
        Q ${cx},${hy + 54}
        ${cx - 14},${hy + 52}
        Z
      `} fill={fill}/>
      {/* Left arm — spread wide, slight downward angle (keeper stance) */}
      <line x1={cx - 17} y1={hy + 24}
            x2={cx - 54} y2={hy + 37}
            stroke={fill} strokeWidth="10" strokeLinecap="round"/>
      {/* Right arm */}
      <line x1={cx + 17} y1={hy + 24}
            x2={cx + 54} y2={hy + 37}
            stroke={fill} strokeWidth="10" strokeLinecap="round"/>
      {/* Left leg */}
      <line x1={cx - 8}  y1={hy + 52}
            x2={cx - 11} y2={footY}
            stroke={fill} strokeWidth="9" strokeLinecap="round"/>
      {/* Right leg */}
      <line x1={cx + 8}  y1={hy + 52}
            x2={cx + 11} y2={footY}
            stroke={fill} strokeWidth="9" strokeLinecap="round"/>
    </g>
  );
}

/**
 * Kicker — stylized approach silhouette.
 * Leaning forward over the ball, one leg back in run-up position.
 */
function Kicker({ cx, footY }) {
  const hy = footY - 46;   // head centre Y
  const fill = '#cde3cd';

  return (
    <g>
      {/* Head, tilted slightly forward */}
      <circle cx={cx + 5} cy={hy} r={9} fill={fill}/>
      {/* Torso — leaning forward toward ball */}
      <line x1={cx + 2} y1={hy + 10}
            x2={cx + 8} y2={hy + 33}
            stroke={fill} strokeWidth="8" strokeLinecap="round"/>
      {/* Left arm (back, for balance) */}
      <line x1={cx} y1={hy + 16}
            x2={cx - 16} y2={hy + 26}
            stroke={fill} strokeWidth="5" strokeLinecap="round"/>
      {/* Right arm (slightly forward) */}
      <line x1={cx + 4} y1={hy + 16}
            x2={cx + 16} y2={hy + 22}
            stroke={fill} strokeWidth="5" strokeLinecap="round"/>
      {/* Standing leg (planted) */}
      <line x1={cx + 6} y1={hy + 33}
            x2={cx + 1} y2={footY}
            stroke={fill} strokeWidth="7" strokeLinecap="round"/>
      {/* Kicking leg (back, raised slightly — run-up) */}
      <line x1={cx + 6} y1={hy + 33}
            x2={cx + 22} y2={footY - 6}
            stroke={fill} strokeWidth="7" strokeLinecap="round"/>
    </g>
  );
}
