export const ROLES = {
  ADMIN:  'admin',
  MEMBER: 'member',
}

export const WAR_STATES = {
  PREPARATION: 'preparation',
  IN_WAR:      'inWar',
  ENDED:       'warEnded',
  NOT_IN_WAR:  'notInWar',
}

export const WAR_RESULTS = {
  WIN:  'win',
  LOSE: 'lose',
  TIE:  'tie',
}

export const PLAYER_STATUS = {
  ACTIVE: 'active',
  LEFT:   'left',
}

export const ROUTES = {
  LOGIN:       '/login',
  DASHBOARD:   '/',
  PLAYERS:     '/players',
  PLAYER:      '/players/:id',
  WARS:        '/wars',
  CURRENT_WAR: '/wars/current',
  WAR_DETAIL:  '/wars/:id',
  ADMIN:       '/admin',
}

export const TH_LEVELS = Array.from({ length: 16 }, (_, i) => i + 1)

export const CLAN_TAG = import.meta.env.VITE_CLAN_TAG || '#2C29G2RJL'