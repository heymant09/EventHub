import api from './client'

export async function getEvents(params) {
  const { data } = await api.get('/events/', { params })
  return data
}

export async function getCategories() {
  const { data } = await api.get('/categories/')
  return data
}

export async function createCategory(categoryData) {
  const { data } = await api.post('/categories/', categoryData)
  return data
}

export async function updateCategory(categoryId, categoryData) {
  const { data } = await api.patch(`/categories/${categoryId}`, categoryData)
  return data
}

export async function deleteCategory(categoryId) {
  await api.delete(`/categories/${categoryId}`)
}

export async function getEvent(eventId) {
  const { data } = await api.get(`/events/${eventId}`)
  return data
}

export async function getEventReviews(eventId) {
  const [reviews, summary] = await Promise.all([
    api.get(`/events/${eventId}/reviews`, { params: { skip: 0, limit: 20 } }),
    api.get(`/events/${eventId}/reviews/summary`),
  ])
  return { reviews: reviews.data, summary: summary.data }
}

export async function createEventReview(eventId, reviewData) {
  const { data } = await api.post(`/events/${eventId}/reviews`, reviewData)
  return data
}

export async function updateEventReview(eventId, reviewId, reviewData) {
  const { data } = await api.patch(`/events/${eventId}/reviews/${reviewId}`, reviewData)
  return data
}

export async function deleteEventReview(eventId, reviewId) {
  await api.delete(`/events/${eventId}/reviews/${reviewId}`)
}

export async function registerForEvent(eventId) {
  const { data } = await api.post(`/events/${eventId}/register`)
  return data
}

export async function getMyRegistrations() {
  const { data } = await api.get('/users/me/registrations')
  return data
}

export async function cancelRegistration(eventId) {
  const { data } = await api.delete(`/events/${eventId}/register`)
  return data
}

export async function getManageableEvents(params = {}) {
  const { data } = await api.get('/events/manage', { params })
  return data
}

export async function createEvent(eventData) {
  const { data } = await api.post('/events/', eventData)
  return data
}

export async function updateEvent(eventId, eventData) {
  const { data } = await api.patch(`/events/${eventId}`, eventData)
  return data
}

export async function publishEvent(eventId) {
  const { data } = await api.post(`/events/${eventId}/publish`)
  return data
}

export async function cancelEvent(eventId) {
  const { data } = await api.delete(`/events/${eventId}`)
  return data
}

export async function completeEvent(eventId) {
  const { data } = await api.post(`/events/${eventId}/complete`)
  return data
}

export async function getEventRegistrations(eventId) {
  const { data } = await api.get(`/events/${eventId}/registrations`, { params: { skip: 0, limit: 100 } })
  return data
}
