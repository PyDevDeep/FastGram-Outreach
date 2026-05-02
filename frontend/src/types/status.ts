export interface SystemStatus {
  engine_active: boolean;
  proxy_valid: boolean;
  account_valid: boolean;
  account_banned: boolean;
}

export interface ActivityLogEntry {
  id: number;
  timestamp: string;
  event: string;
  details: string | null;
}
