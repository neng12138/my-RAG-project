import request from './request'

export const documentApi = {
  upload: (formData) =>
    request.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  list: () => request.get('/documents/list'),
  delete: (id) => request.delete(`/documents/${id}`),
}
