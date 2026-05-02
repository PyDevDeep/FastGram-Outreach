export interface OutreachConfig {
  max_daily: number;
  message_template: string;
}

export interface WarmupConfig {
  initial_limit: number;
  step: number;
}

export interface PauseConfig {
  min_seconds: number;
  max_seconds: number;
  work_hours_start: number;
  work_hours_end: number;
}

export interface SystemConfig
  extends OutreachConfig, WarmupConfig, PauseConfig {}
