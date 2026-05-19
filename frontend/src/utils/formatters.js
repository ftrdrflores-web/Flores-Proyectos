// ─── Fechas ──────────────────────────────────────────────────────────────────
export const formatDate = (dateStr) => {
  if (!dateStr) return '—'
  return new Intl.DateTimeFormat('es-MX', {
    day:   '2-digit',
    month: 'short',
    year:  'numeric',
    timeZone: 'America/Tijuana',
  }).format(new Date(dateStr))
}

export const formatDateTime = (dateStr) => {
  if (!dateStr) return '—'
  return new Intl.DateTimeFormat('es-MX', {
    day:    '2-digit',
    month:  'short',
    year:   'numeric',
    hour:   '2-digit',
    minute: '2-digit',
    timeZone: 'America/Tijuana',
  }).format(new Date(dateStr))
}

export const timeAgo = (dateStr) => {
  if (!dateStr) return '—'
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1)  return 'ahora'
  if (mins < 60) return `hace ${mins}m`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24)  return `hace ${hrs}h`
  return `hace ${Math.floor(hrs / 24)}d`
}

// ─── Números ─────────────────────────────────────────────────────────────────
export const formatNumber = (n) =>
  n != null ? new Intl.NumberFormat('es-MX').format(n) : '—'

export const formatPercent = (n, decimals = 1) =>
  n != null ? `${Number(n).toFixed(decimals)}%` : '—'

export const formatStars = (n) =>
  n != null ? `${'★'.repeat(n)}${'☆'.repeat(3 - n)}` : '—'

// ─── Guerra ──────────────────────────────────────────────────────────────────
export const warStateLabel = (state) => {
  const map = {
    preparation: 'Preparación',
    inWar:       'En guerra',
    warEnded:    'Terminada',
    notInWar:    'Sin guerra',
  }
  return map[state] ?? state
}

export const warResultLabel = (result) => {
  const map = { win: 'Victoria', lose: 'Derrota', tie: 'Empate' }
  return map[result] ?? result
}

export const warResultColor = (result) => {
  const map = {
    win:  'text-green-400',
    lose: 'text-red-400',
    tie:  'text-yellow-400',
  }
  return map[result] ?? 'text-gray-400'
}

// ─── Jugadores ────────────────────────────────────────────────────────────────
export const roleLabel = (role) => {
  const map = {
    leader:     'Líder',
    coLeader:   'Co-Líder',
    elder:      'Anciano',
    member:     'Miembro',
  }
  return map[role] ?? role
}

export const thLabel = (level) => `TH${level}`

// ─── Misc ────────────────────────────────────────────────────────────────────
export const cn = (...classes) =>
  classes.filter(Boolean).join(' ')