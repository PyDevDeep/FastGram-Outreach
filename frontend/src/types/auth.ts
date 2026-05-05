export interface AuthStatusResponse {
  is_valid: boolean;
  proxy_alive: boolean;
  message: string;
  session_created_at?: string | null;
}

export interface LoginResponse {
  status: string;
  message: string;
}
