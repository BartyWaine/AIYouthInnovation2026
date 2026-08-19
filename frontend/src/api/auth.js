import api from './client'

export async function login(email, password) {
  const params = new URLSearchParams()
  params.append('username', email)
  params.append('password', password)
  const res = await api.post('/auth/login', params, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  localStorage.setItem('token', res.data.access_token)
  return res.data
}

export async function getMe() {
  const res = await api.get('/auth/me')
  return res.data
}

export function logout() {
  localStorage.removeItem('token')
}

export async function changePassword(currentPassword, newPassword) {
  const res = await api.post('/auth/change-password', {
    current_password: currentPassword,
    new_password: newPassword,
  })
  return res.data
}

export async function resetPassword(userId, newPassword = null) {
  const res = await api.post('/auth/reset-password', {
    user_id: userId,
    new_password: newPassword,
  })
  return res.data
}
