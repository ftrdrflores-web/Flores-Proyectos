import api from './api'

const authService = {
  login: (credentials) =>
    api.post('/auth/login/', credentials),

  logout: (refreshToken) =>
    api.post('/auth/logout/', { refresh: refreshToken }),

  me: () =>
    api.get('/auth/me/'),

  register: (data) =>
    api.post('/auth/register/', data),

  changePassword: (data) =>
    api.post('/auth/change-password/', data),

  refreshToken: (refresh) =>
    api.post('/auth/refresh/', { refresh }),
}

export default authService