import { apiFetch } from "./client";
import type { SystemConfig } from "@/types/config";

const DEFAULT_CONFIG: SystemConfig = {
  max_daily: 20,
  message_template: "Hi, interested?",
  initial_limit: 5,
  step: 5,
  min_seconds: 30,
  max_seconds: 60,
  work_hours_start: 9,
  work_hours_end: 21,
};

export async function fetchConfig(): Promise<SystemConfig> {
  try {
    return await apiFetch<SystemConfig>("/api/config");
  } catch (error) {
    console.warn(
      "Backend /api/config missing or failed. Using DEFAULT_CONFIG.",
      error,
    );
    return DEFAULT_CONFIG;
  }
}

export function saveConfig(config: SystemConfig): Promise<SystemConfig> {
  return apiFetch<SystemConfig>("/api/config", {
    method: "POST",
    body: JSON.stringify(config),
  });
}
