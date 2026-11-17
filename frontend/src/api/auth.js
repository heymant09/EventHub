import api from './client'

export async function login(credentials) {
  const { data } = await api.post('/auth/login', credentials)
  return data
}

export async function registerUser(userData) {
  const { data } = await api.post('/auth/register', userData)
  return data
}

export async function getCurrentUser() {
  const { data } = await api.get('/users/me')
  return data
}

export async function updateMyProfile(profileData) {
  const { data } = await api.patch('/users/me', profileData)
  return data
}

export async function getUsers(params = {}) {
  const { data } = await api.get('/users/', { params })
  return data
}

export async function updateUserRole(userId, role) {
  const { data } = await api.patch(`/users/${userId}/role`, { role })
  return data
}
