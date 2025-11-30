import axios from 'axios'
import { API_BASE_URL, withApiPrefix } from './api'

export interface AuthResponse {
  access_token: string
  token_type?: string
  user?: {
    username?: string
    email?: string
  }
}

export interface RegisterResponse {
  message: string
}

const authClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const loginRequest = async (payload: { username: string; password: string }) => {
  const { data } = await authClient.post<AuthResponse>(withApiPrefix('/auth/login'), payload)
  return data
}

export const registerRequest = async (payload: {
  email: string
  password: string
  full_name?: string
}) => {
  const { data } = await authClient.post<RegisterResponse>(withApiPrefix('/auth/register'), payload)
  return data
}
