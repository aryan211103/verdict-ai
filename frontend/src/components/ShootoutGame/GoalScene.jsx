/**
 * GoalScene — shared broadcast-style goal SVG.
 *
 * Used in two modes:
 *   "shoot" — 9 clickable zones (TL/TC/TR/ML/MC/MR/BL/BC/BR) on the goal
 *             mouth. Ball rests on the penalty spot. No keeper figure.
 *   "dive"  — 3 full-height zones (L / C / R) on the goal mouth.
 *             A pair of keeper gloves marks the goal line.
 *             Selected zone highlights in amber (keeper went there).
 *
 * Stage: STATIC — no animation yet.
 * Logic: none. All game logic lives upstream; this component is visual only.
 */
import { useState } from 'react';

/* ── Goal geometry (viewBox 0 0 400 270) ──────────────────────────────────
 * Goal width 360 / height 120 → exactly 3 : 1, matching a real goal.
 */
const G = {
  left:   20,
  right:  380,
  top:    14,
  bottom: 134,
  get w()  { return this.right - this.left; },   // 360
  get h()  { return this.bottom - this.top; },   // 120
  get cw() { return this.w / 3; },               // 120  column width
  get rh() { return this.h / 3; },               // 40   row height
};

const SPOT = { cx: 200, cy: 210 };

/* ── Shoot-mode zone definitions ─────────────────────────────────────── */
const SHOOT_ZONES = [
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

/* ── Dive-mode zone definitions ──────────────────────────────────────────
 * Labels use "goal-left / goal-right" — the same orientation the shooter
 * sees. Clicking the left third covers all shots mapped to the L column
 * (TL / ML / BL). No "whose left" ambiguity.
 */
const DIVE_ZONES = [
  { id: 'L', label: 'Cover LEFT',   sub: 'left third',   x: G.left,        w: G.cw },
  { id: 'C', label: 'Cover CENTRE', sub: 'centre',        x: G.left + G.cw, w: G.cw },
  { id: 'R', label: 'Cover RIGHT',  sub: 'right third',  x: G.left + 2*G.cw, w: G.cw },
];

export default function GoalScene({ mode = 'shoot', selected, onZoneClick, loading = false }) {
  const [hovered, setHovered] = useState(null);

  const isShoot = mode === 'shoot';

  return (
    <svg
      viewBox="0 0 400 270"
      style={{ width: '100%', display: 'block', userSelect: 'none' }}
      aria-label={isShoot ? 'Goal mouth — tap a zone to pick your shot' : 'Goal mouth — tap to choose your dive direction'}
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        {/* Diamond net mesh — rotated 45° grid gives the rhombus net look */}
        <pattern id="netDiamond"
          width="18" height="18"
          patternTransform="rotate(45 200 74)"
          patternUnits="userSpaceOnUse">
          <path d="M 0,0 L 18,0 M 0,0 L 0,18"
                stroke="rgba(210,230,210,0.22)" strokeWidth="0.9" fill="none"/>
        </pattern>

        {/* Pitch mow stripes — horizontal alternating bands */}
        <pattern id="mowStripes" x="0" y="0" width="400" height="52" patternUnits="userSpaceOnUse">
          <rect width="400" height="26" fill="#1b4520"/>
          <rect y="26" width="400" height="26" fill="#183d1d"/>
        </pattern>
      </defs>

      {/* ── PITCH (fills the entire SVG — no void around it) ──────────── */}
      <rect width="400" height="270" fill="#183d1d"/>
      <rect width="400" height="270" fill="url(#mowStripes)" opacity="0.7"/>

      {/* ── PENALTY AREA MARKINGS ────────────────────────────────────── */}
      {/* 18-yard box */}
      <rect x="36" y={G.bottom} width="328" height="86"
            fill="none" stroke="rgba(255,255,255,0.48)" strokeWidth="1.5"/>
      {/* 6-yard box */}
      <rect x="116" y={G.bottom} width="168" height="34"
            fill="none" stroke="rgba(255,255,255,0.28)" strokeWidth="1"/>
      {/* Goal line (flush with goal bottom) */}
      <line x1="36" y1={G.bottom} x2="364" y2={G.bottom}
            stroke="rgba(255,255,255,0.60)" strokeWidth="2"/>
      {/* Penalty arc */}
      <path d={`M 108,${G.bottom} A 92,92 0 0,0 292,${G.bottom}`}
            fill="none" stroke="rgba(255,255,255,0.38)" strokeWidth="1.5"/>
      {/* Centre spot (for reference) */}
      <circle cx="200" cy="250" r="3" fill="rgba(255,255,255,0.30)"/>

      {/* ── GOAL BACK SHADOW (depth) ──────────────────────────────────── */}
      <rect x={G.left} y={G.top} width={G.w} height={G.h}
            fill="#07120a"/>

      {/* ── GOAL NET MESH ─────────────────────────────────────────────── */}
      <rect x={G.left} y={G.top} width={G.w} height={G.h}
            fill="url(#netDiamond)"/>

      {/* Subtle top-of-net gradient (darker inside) */}
      <rect x={G.left} y={G.top} width={G.w} height={G.h}
            fill="url(#netDepth)"/>

      {/* Soft shadow along top and sides of net interior */}
      <rect x={G.left} y={G.top} width={G.w} height="22"
            fill="rgba(0,0,0,0.28)"/>
      <rect x={G.left} y={G.top} width="22" height={G.h}
            fill="rgba(0,0,0,0.18)"/>
      <rect x={G.right-22} y={G.top} width="22" height={G.h}
            fill="rgba(0,0,0,0.18)"/>

      {/* ── ZONE DIVIDER LINES ON NET ─────────────────────────────────── */}
      {isShoot && [1, 2].map(col => (
        <line key={`vc${col}`}
              x1={G.left + col * G.cw} y1={G.top}
              x2={G.left + col * G.cw} y2={G.bottom}
              stroke="rgba(255,255,255,0.16)" strokeWidth="1" pointerEvents="none"/>
      ))}
      {isShoot && [1, 2].map(row => (
        <line key={`hr${row}`}
              x1={G.left} y1={G.top + row * G.rh}
              x2={G.right} y2={G.top + row * G.rh}
              stroke="rgba(255,255,255,0.16)" strokeWidth="1" pointerEvents="none"/>
      ))}
      {/* Dive mode: just vertical dividers */}
      {!isShoot && [1, 2].map(col => (
        <line key={`dvc${col}`}
              x1={G.left + col * G.cw} y1={G.top}
              x2={G.left + col * G.cw} y2={G.bottom}
              stroke="rgba(255,255,255,0.20)" strokeWidth="1" pointerEvents="none"/>
      ))}

      {/* ── SHOOT ZONES ───────────────────────────────────────────────── */}
      {isShoot && SHOOT_ZONES.map(z => {
        const x   = G.left + z.col * G.cw;
        const y   = G.top  + z.row * G.rh;
        const sel = selected === z.id;
        const hov = hovered  === z.id;
        return (
          <g key={z.id}
             onClick={() => !loading && onZoneClick(z.id)}
             onMouseEnter={() => setHovered(z.id)}
             onMouseLeave={() => setHovered(null)}
             style={{ cursor: loading ? 'not-allowed' : 'pointer' }}>
            {/* Fill */}
            <rect x={x} y={y} width={G.cw} height={G.rh}
                  fill={sel ? 'rgba(74,222,128,0.38)' : hov ? 'rgba(255,255,255,0.09)' : 'transparent'}/>
            {/* Selected ring */}
            {sel && (
              <rect x={x+2} y={y+2} width={G.cw-4} height={G.rh-4}
                    fill="none" stroke="rgba(74,222,128,0.90)" strokeWidth="1.5"
                    strokeDasharray="5,3" pointerEvents="none"/>
            )}
            {/* Corner dots (amber) */}
            {z.kind === 'corner' && !sel && (
              <circle
                cx={x + (z.col === 0 ? 11 : G.cw-11)}
                cy={y + (z.row === 0 ? 10 : G.rh-10)}
                r="4.5" fill="rgba(245,158,11,0.55)" pointerEvents="none"/>
            )}
            {/* Centre dot */}
            {z.kind === 'center' && !sel && (
              <circle cx={x + G.cw/2} cy={y + G.rh/2}
                      r="4" fill="rgba(255,255,255,0.20)" pointerEvents="none"/>
            )}
          </g>
        );
      })}

      {/* ── DIVE ZONES (full-height L/C/R) ────────────────────────────── */}
      {!isShoot && DIVE_ZONES.map(z => {
        const sel = selected === z.id;
        const hov = hovered  === z.id;
        return (
          <g key={z.id}
             onClick={() => !loading && onZoneClick(z.id)}
             onMouseEnter={() => setHovered(z.id)}
             onMouseLeave={() => setHovered(null)}
             style={{ cursor: loading ? 'not-allowed' : 'pointer' }}>
            <rect x={z.x} y={G.top} width={z.w} height={G.h}
                  fill={sel ? 'rgba(245,158,11,0.40)' : hov ? 'rgba(255,255,255,0.08)' : 'transparent'}/>
            {sel && (
              <rect x={z.x+3} y={G.top+3} width={z.w-6} height={G.h-6}
                    fill="none" stroke="rgba(251,191,36,0.90)" strokeWidth="2"
                    strokeDasharray="6,3" pointerEvents="none"/>
            )}
            {/* Main label */}
            <text
              x={z.x + z.w/2} y={G.top + G.h/2 - 2}
              textAnchor="middle"
              fill={sel ? 'rgba(251,191,36,0.98)' : 'rgba(255,255,255,0.38)'}
              fontSize="13"
              fontFamily="'Barlow Condensed', sans-serif"
              fontWeight="700"
              letterSpacing="0.06em"
              style={{ textTransform: 'uppercase' }}
              pointerEvents="none">
              {z.label}
            </text>
            {/* Sub-label */}
            <text
              x={z.x + z.w/2} y={G.top + G.h/2 + 14}
              textAnchor="middle"
              fill={sel ? 'rgba(251,191,36,0.70)' : 'rgba(255,255,255,0.20)'}
              fontSize="10"
              fontFamily="'Inter', sans-serif"
              fontWeight="500"
              letterSpacing="0.04em"
              style={{ textTransform: 'lowercase' }}
              pointerEvents="none">
              {z.sub}
            </text>
          </g>
        );
      })}

      {/* ── GOAL FRAME (posts + crossbar, drawn last so they sit on top) ─ */}
      {/* Post shadow for depth */}
      <line x1={G.left+5} y1={G.top+6} x2={G.left+5} y2={G.bottom}
            stroke="rgba(0,0,0,0.40)" strokeWidth="4" strokeLinecap="round"/>
      <line x1={G.right-5} y1={G.top+6} x2={G.right-5} y2={G.bottom}
            stroke="rgba(0,0,0,0.40)" strokeWidth="4" strokeLinecap="round"/>
      {/* Left post */}
      <line x1={G.left} y1={G.top-3} x2={G.left} y2={G.bottom}
            stroke="#ffffff" strokeWidth="7" strokeLinecap="round"/>
      {/* Right post */}
      <line x1={G.right} y1={G.top-3} x2={G.right} y2={G.bottom}
            stroke="#ffffff" strokeWidth="7" strokeLinecap="round"/>
      {/* Crossbar */}
      <line x1={G.left-3} y1={G.top} x2={G.right+3} y2={G.top}
            stroke="#ffffff" strokeWidth="7" strokeLinecap="round"/>

      {/* ── KEEPER GLOVES (dive mode only — static for now) ───────────── */}
      {!isShoot && (
        <g opacity="0.88">
          {/* Left glove */}
          <rect x="152" y="116" width="34" height="22" rx="9"
                fill="#f59e0b" stroke="rgba(0,0,0,0.25)" strokeWidth="1"/>
          <rect x="156" y="119" width="12" height="7" rx="3"
                fill="rgba(255,255,255,0.45)"/>
          {/* Right glove */}
          <rect x="214" y="116" width="34" height="22" rx="9"
                fill="#f59e0b" stroke="rgba(0,0,0,0.25)" strokeWidth="1"/>
          <rect x="218" y="119" width="12" height="7" rx="3"
                fill="rgba(255,255,255,0.45)"/>
        </g>
      )}

      {/* ── BALL (shoot mode only — on penalty spot) ──────────────────── */}
      {isShoot && (
        <g>
          <circle cx={SPOT.cx} cy={SPOT.cy} r="11"
                  fill="white" filter="drop-shadow(0 3px 5px rgba(0,0,0,0.60))"/>
          {/* Classic seam lines */}
          <circle cx={SPOT.cx} cy={SPOT.cy} r="11"
                  fill="none" stroke="rgba(0,0,0,0.18)" strokeWidth="0.9"/>
          <path d={`M ${SPOT.cx},${SPOT.cy-8} C ${SPOT.cx+6},${SPOT.cy-2} ${SPOT.cx+6},${SPOT.cy+3} ${SPOT.cx},${SPOT.cy+8}`}
                stroke="rgba(0,0,0,0.18)" strokeWidth="0.9" fill="none"/>
          <path d={`M ${SPOT.cx},${SPOT.cy-8} C ${SPOT.cx-6},${SPOT.cy-2} ${SPOT.cx-6},${SPOT.cy+3} ${SPOT.cx},${SPOT.cy+8}`}
                stroke="rgba(0,0,0,0.18)" strokeWidth="0.9" fill="none"/>
          {/* Penalty spot mark */}
          <circle cx={SPOT.cx} cy={SPOT.cy+16} r="3"
                  fill="rgba(255,255,255,0.55)"/>
        </g>
      )}
    </svg>
  );
}

// Named export for the label lookup (used by GoalGrid)
export { SHOOT_ZONES };
export const ZONE_LABELS = Object.fromEntries(
  SHOOT_ZONES.map(z => [z.id, z.label])
);
