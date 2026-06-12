import axios from 'axios'

const API_BASE = '/api'

const request = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
})

request.interceptors.response.use(
  (res) => res.data,
  (err) => {
    console.error('[API Error]', err.response?.data || err.message)
    return Promise.reject(err)
  }
)

export default request
export { API_BASE }
