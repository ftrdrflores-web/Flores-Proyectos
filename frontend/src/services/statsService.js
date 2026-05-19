import api from './api'

const statsService = {
  getDashboard:  ()     => api.get('/stats/dashboard/'),
  getLeaderboard:(params)=> api.get('/stats/leaderboard/', { params }),
  getTrends:     (params)=> api.get('/stats/trends/', { params }),
  getWarLog:     (params)=> api.get('/stats/war-log/', { params }),
  getPlayerStats:(tag)   => api.get(`/stats/player/${encodeURIComponent(tag)}/`),
  compare:       (params)=> api.get('/stats/compare/', { params }),
}

export default statsService