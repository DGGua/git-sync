import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// Response interceptor for error handling
api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// Config API
export const configApi = {
  get: () => api.get('/config'),
  update: (data) => api.put('/config', data),
}

// Repositories API
export const repositoriesApi = {
  list: () => api.get('/repositories'),
  get: (name) => api.get(`/repositories/${encodeURIComponent(name)}`),
  create: (data) => api.post('/repositories', data),
  update: (name, data) => api.put(`/repositories/${encodeURIComponent(name)}`, data),
  delete: (name) => api.delete(`/repositories/${encodeURIComponent(name)}`),
  reorder: (orderedNames) => api.put('/repositories/order', { repositories: orderedNames }),
}

// Keys API
export const keysApi = {
  list: () => api.get('/keys'),
  generate: (data) => api.post('/keys', data),
  delete: (name) => api.delete(`/keys/${encodeURIComponent(name)}`),
}

// Sync API
export const syncApi = {
  run: (repository = null, dryRun = false) => api.post('/sync', {
    repository,
    dry_run: dryRun,
  }),
  runSingle: (name, dryRun = false) => api.post(`/sync/${encodeURIComponent(name)}?dry_run=${dryRun}`),
  status: () => api.get('/sync/status'),
}

export default api
