import api from './api'

const warService = {
  getWars:         (params) => api.get('/wars/', { params }),
  getWar:          (id)     => api.get(`/wars/${id}/`),
  getCurrentWar:   ()       => api.get('/wars/current/'),
  getAttacks:      (id)     => api.get(`/wars/${id}/attacks/`),
  getDefenses:     (id)     => api.get(`/wars/${id}/defenses/`),
  getPerformance:  (id)     => api.get(`/wars/${id}/performance/`),
  getPlayerHistory:(tag)    => api.get(`/wars/player/${encodeURIComponent(tag)}/history/`),
}

export default warService