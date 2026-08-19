import api from './client'

export const listCompetitions = () => api.get('/competitions/').then(r => r.data)
export const getCompetition = (id) => api.get(`/competitions/${id}`).then(r => r.data)
export const createCompetition = (data) => api.post('/competitions/', data).then(r => r.data)
export const deleteCompetition = (id) => api.delete(`/competitions/${id}`).then(r => r.data)
export const getLeaderboard = (id) => api.get(`/competitions/${id}/leaderboard`).then(r => r.data)
