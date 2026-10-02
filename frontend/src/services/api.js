import axios from 'axios'
import { attachSessionInterceptors } from './session'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: { 'Content-Type': 'application/json' },
})

attachSessionInterceptors(api)
export default api
