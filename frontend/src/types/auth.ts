export interface User {
  id: number
  login_id: string
  display_name: string
  role: 'admin' | 'user'
  status: 'active' | 'pending' | 'disabled'
  last_login_at?: string
  created_at?: string
}

export interface LoginRequest {
  login_id: string
  password: string
}

export interface RegisterRequest {
  token: string
  login_id: string
  password: string
  display_name?: string
}

export interface InviteCreateRequest {
  role: 'admin' | 'user'
}

export interface Invite {
  token: string
  expires_at: string
  role: 'admin' | 'user'
  provisional_user_id: number
}
