// Hardcoded preset squads — cosmetic labels only, never affect game logic.
export const PRESETS = [
  {
    id: 'wc2022',
    label: '2022 World Cup Final',
    teamA: { team_name: 'Argentina', players: ['Messi','Dybala','Paredes','Montiel','Di María'] },
    teamB: { team_name: 'France',    players: ['Mbappé','Muani','Griezmann','Coman','Tchouaméni'] },
  },
  {
    id: 'euro2020',
    label: 'Euro 2020 Final',
    teamA: { team_name: 'Italy',   players: ['Berardi','Belotti','Bonucci','Bernardeschi','Jorginho'] },
    teamB: { team_name: 'England', players: ['Kane','Rashford','Sancho','Saka','Mount'] },
  },
  {
    id: 'copa2021',
    label: '2021 Copa América Final',
    teamA: { team_name: 'Argentina', players: ['Messi','Di María','Paredes','Lautaro','De Paul'] },
    teamB: { team_name: 'Brazil',    players: ['Neymar','Richarlison','Paquetá','Gabriel','Everton'] },
  },
  {
    id: 'custom',
    label: 'Custom Teams',
    teamA: null,
    teamB: null,
  },
];
