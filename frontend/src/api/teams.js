import api from './client'

export const listTeams = (compId) => api.get('/teams', { params: { competition_id: compId } }).then(r => r.data)
export const getTeam = (id) => api.get(`/teams/${id}`).then(r => r.data)
export const createTeam = (data) => api.post('/teams', data).then(r => r.data)
export const deleteTeam = (id) => api.delete(`/teams/${id}`).then(r => r.data)
export const addMember = (teamId, userId, isLeader) => api.post(`/teams/${teamId}/members`, null, { params: { user_id: userId, is_leader: isLeader } }).then(r => r.data)
export const getMyTeam = () => api.get('/teams/mine').then(r => r.data)
export const getMyTeamSubmissions = (competitionId) => api.get('/teams/mine/submissions', { params: { competition_id: competitionId } }).then(r => r.data)
