import api from './api'

const clanService = {
  getClan:      ()     => api.get('/clan/'),
  updateClan:   (data) => api.patch('/clan/', data),
  getStats:     ()     => api.get('/clan/stats/'),
  getMembers:   ()     => api.get('/clan/members/'),
  getDashboard: ()     => api.get('/clan/dashboard/'),
}

export default clanService