import request from './request'

export const sessionApi = {
  create: (title = '新对话') => request.post('/sessions/create', { title }),
  list: () => request.get('/sessions/list'),
  delete: (id) => request.delete(`/sessions/${id}`),
}
