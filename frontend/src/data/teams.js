// Static national team data — cosmetic only.
// Names are suggestion labels; they never enter game resolution logic.
// Colors: primary jersey / kit colour used for UI accents only.

export const TEAMS = [
  {
    name: 'Argentina', flag: '🇦🇷', color: '#75AADB',
    players: ['Messi', 'Lautaro Martínez', 'Ángel Di María', 'Paulo Dybala', 'Rodrigo De Paul'],
  },
  {
    name: 'France', flag: '🇫🇷', color: '#003189',
    players: ['Mbappé', 'Antoine Griezmann', 'Olivier Giroud', 'Marcus Thuram', 'Ousmane Dembélé'],
  },
  {
    name: 'Brazil', flag: '🇧🇷', color: '#009C3B',
    players: ['Vinicius Jr', 'Rodrygo', 'Raphinha', 'Endrick', 'Lucas Paquetá'],
  },
  {
    name: 'England', flag: '🏴󠁧󠁢󠁥󠁮󠁧󠁿', color: '#CF081F',
    players: ['Harry Kane', 'Bukayo Saka', 'Marcus Rashford', 'Jude Bellingham', 'Phil Foden'],
  },
  {
    name: 'Germany', flag: '🇩🇪', color: '#000000',
    players: ['Thomas Müller', 'Kai Havertz', 'Florian Wirtz', 'Jamal Musiala', 'Serge Gnabry'],
  },
  {
    name: 'Spain', flag: '🇪🇸', color: '#AA151B',
    players: ['Lamine Yamal', 'Pedri', 'Álvaro Morata', 'Nico Williams', 'Dani Olmo'],
  },
  {
    name: 'Italy', flag: '🇮🇹', color: '#003399',
    players: ['Federico Chiesa', 'Nicolo Barella', 'Lorenzo Pellegrini', 'Mateo Retegui', 'Giacomo Raspadori'],
  },
  {
    name: 'Portugal', flag: '🇵🇹', color: '#006600',
    players: ['Cristiano Ronaldo', 'Bruno Fernandes', 'Bernardo Silva', 'João Félix', 'Rafael Leão'],
  },
  {
    name: 'Netherlands', flag: '🇳🇱', color: '#FF6600',
    players: ['Virgil van Dijk', 'Cody Gakpo', 'Wout Weghorst', 'Frenkie de Jong', 'Tijjani Reijnders'],
  },
  {
    name: 'Belgium', flag: '🇧🇪', color: '#EF3340',
    players: ['Kevin De Bruyne', 'Romelu Lukaku', 'Jeremy Doku', 'Leandro Trossard', 'Dodi Lukebakio'],
  },
  {
    name: 'Croatia', flag: '🇭🇷', color: '#FF3300',
    players: ['Luka Modrić', 'Mateo Kovačić', 'Marcelo Brozović', 'Nikola Vlašić', 'Andrej Kramarić'],
  },
  {
    name: 'Morocco', flag: '🇲🇦', color: '#006233',
    players: ['Achraf Hakimi', 'Hakim Ziyech', 'Youssef En-Nesyri', 'Azzedine Ounahi', 'Sofiane Boufal'],
  },
  {
    name: 'Uruguay', flag: '🇺🇾', color: '#75AADB',
    players: ['Edinson Cavani', 'Federico Valverde', 'Darwin Núñez', 'Rodrigo Bentancur', 'Ronald Araújo'],
  },
  {
    name: 'Mexico', flag: '🇲🇽', color: '#006847',
    players: ['Hirving Lozano', 'Alexis Vega', 'Santiago Giménez', 'Edson Álvarez', 'Roberto Alvarado'],
  },
  {
    name: 'Japan', flag: '🇯🇵', color: '#003DA5',
    players: ['Takefusa Kubo', 'Kaoru Mitoma', 'Ritsu Doan', 'Ayase Ueda', 'Wataru Endo'],
  },
  {
    name: 'Colombia', flag: '🇨🇴', color: '#FDD116',
    players: ['Luis Díaz', 'James Rodríguez', 'Jhon Córdoba', 'Cucho Hernández', 'Yerry Mina'],
  },
  {
    name: 'Senegal', flag: '🇸🇳', color: '#009A44',
    players: ['Sadio Mané', 'Ismaïla Sarr', 'Boulaye Dia', 'Nampalys Mendy', 'Pape Gueye'],
  },
  {
    name: 'Poland', flag: '🇵🇱', color: '#DC143C',
    players: ['Robert Lewandowski', 'Piotr Zieliński', 'Kamil Grosicki', 'Sebastian Szymański', 'Arkadiusz Milik'],
  },
  {
    name: 'Switzerland', flag: '🇨🇭', color: '#FF0000',
    players: ['Xherdan Shaqiri', 'Breel Embolo', 'Granit Xhaka', 'Manuel Akanji', 'Noah Okafor'],
  },
  {
    name: 'USA', flag: '🇺🇸', color: '#002868',
    players: ['Christian Pulisic', 'Gio Reyna', 'Weston McKennie', 'Tyler Adams', 'Ricardo Pepi'],
  },
  {
    name: 'Denmark', flag: '🇩🇰', color: '#C60C30',
    players: ['Christian Eriksen', 'Pierre-Emile Højbjerg', 'Kasper Dolberg', 'Martin Braithwaite', 'Andreas Skov Olsen'],
  },
  {
    name: 'Australia', flag: '🇦🇺', color: '#FFCD00',
    players: ['Mathew Leckie', 'Tom Rogic', 'Mitch Duke', 'Jackson Irvine', 'Ajdin Hrustic'],
  },
];

export function findTeam(query) {
  const q = query.toLowerCase().trim();
  return TEAMS.filter(t => t.name.toLowerCase().includes(q));
}

export function teamColor(name) {
  return TEAMS.find(t => t.name === name)?.color ?? null;
}
