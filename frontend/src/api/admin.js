import api from './client'

export const listUsers = () => api.get('/admin/users').then(r => r.data)
export const createUser = (email, password, role) => api.post('/admin/users', null, { params: { email, password, role } }).then(r => r.data)
export const listAuditLogs = () => api.get('/admin/audit-logs').then(r => r.data)
