import api from './api'

const playerService = {
  getPlayers:   (params) => api.get('/players/', { params }),
  getPlayer:    (id)     => api.get(`/players/${id}/`),
  getByTag:     (tag)    => api.get(`/players/tag/${encodeURIComponent(tag)}/`),
  getRanking:   (params) => api.get('/players/ranking/', { params }),
  compare:      (params) => api.get('/players/compare/', { params }),
  getStats:     (id)     => api.get(`/players/${id}/stats/`),
  getMonthly:   (id)     => api.get(`/players/${id}/monthly/`),
}

export default playerService