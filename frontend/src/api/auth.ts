
import { http } from './client'

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

export interface CurrentUser {
  id: number
  username: string
  role: 'viewer' | 'workflow_approver'
  is_active: boolean
}

export async function login(
  data: LoginRequest,
): Promise<LoginResponse> {
  const response = await http.post<LoginResponse>(
    '/api/v1/auth/login',
    data,
  )

  return response.data
}

export async function getMe(): Promise<CurrentUser> {
  const response = await http.get<CurrentUser>(
    '/api/v1/auth/me',
  )

  return response.data
}
