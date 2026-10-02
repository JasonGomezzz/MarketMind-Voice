import axios from 'axios'
import { attachSessionInterceptors } from './session'

// Spring validates Django access tokens. All consumers share one refresh operation.
const userApi = axios.create({
  baseURL: import.meta.env.VITE_USER_API_URL,
  headers: { 'Content-Type': 'application/json' },
})

attachSessionInterceptors(userApi)
export default userApi
