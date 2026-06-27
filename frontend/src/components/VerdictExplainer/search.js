/**
 * Incident search — matches user queries to verified incidents only.
 * NO model calls, NO generated answers. Verified incidents only.
 *
 * Returns the best-matching incident or null if nothing scores above threshold.
 * Caller must show the "no match" fallback (list of incidents) when null.
 */

// Per-incident keyword index — player names, actions, competition context.
// Entries are lowercased and space-separated; any token in the index can match.
const SEARCH_INDEX = {
  suarez_handball_wc2010_qf:
    'suarez handball ghana dogso penalty goal line red card uruguay quarter-final 2010 asamoah gyan',
  zidane_headbutt_wc2006_final:
    'zidane headbutt head-butt materazzi italy france final 2006 violent conduct',
  henry_handball_wc2010_qualifier:
    'henry handball ireland gallas qualifier playoff play-off 2010',
  maradona_hand_of_god_wc1986_qf:
    'maradona hand god handball argentina england 1986 punch fist shilton quarter-final',
  tevez_offside_wc2010_r16:
    'tevez offside mexico round 16 2010 argentina header',
  keane_haaland_seriousfoulplay_2001:
    'keane haaland serious foul play manchester united city 2001',
  suarez_biting_chiellini_wc2014:
    'suarez bite biting chiellini uruguay italy 2014 violent conduct',
  dejong_xabialonso_wc2010_final:
    'de jong dejong xabi alonso final 2010 netherlands spain yellow karate boot chest',
  rooney_stamp_wc2006_qf:
    'rooney stamp carvalho england portugal 2006 violent conduct groin',
  dicancio_push_referee_pl1998:
    'di canio push referee alcock sheffield wednesday arsenal 1998 violent conduct',
};

// Words too generic to anchor a match — common football / query words
const SKIP = new Set([
  'why', 'did', 'get', 'was', 'the', 'and', 'how', 'what',
  'who', 'for', 'red', 'card', 'goal', 'that', 'this', 'with',
  'when', 'about', 'explain', 'tell', 'show',
  // Common football terms that appear in many incidents
  'penalty', 'foul', 'match', 'play', 'player', 'ball', 'game',
  'kick', 'shot', 'world', 'final', 'cup', 'incident', 'call',
]);

export function searchIncidents(query, incidents) {
  const tokens = query
    .toLowerCase()
    .split(/\W+/)
    .filter(t => t.length >= 3 && !SKIP.has(t));

  if (tokens.length === 0) return null;

  let best = null;
  let bestScore = 0;

  for (const inc of incidents) {
    const index  = SEARCH_INDEX[inc.incident_id] ?? '';
    const title  = inc.title.toLowerCase();
    const combined = `${index} ${title}`;

    let score = 0;
    for (const token of tokens) {
      if (combined.includes(token)) {
        // Longer tokens (more specific) score higher
        score += Math.max(1, token.length - 3);
      }
    }

    // Bonus when the query matches most of the meaningful tokens
    if (score > 0 && score >= tokens.length * 2) score += 3;

    if (score > bestScore) { bestScore = score; best = inc; }
  }

  // Threshold: at least 2 points (one meaningful specific token)
  return bestScore >= 2 ? best : null;
}
