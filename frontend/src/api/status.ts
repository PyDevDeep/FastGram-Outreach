import { apiFetch } from "./client";
import type { SystemStatus, ActivityLogEntry } from "@/types/status";

const MOCK_STATUS: SystemStatus = {
  engine_active: false,
  proxy_valid: false,
  account_valid: false,
  account_banned: false,
};

export async function fetchSystemStatus(): Promise<SystemStatus> {
  try {
    return await apiFetch<SystemStatus>("/api/status");
  } catch (error) {
    console.warn(
      "Backend /api/status missing or failed. Using MOCK_STATUS.",
      error,
    );
    return MOCK_STATUS;
    return MOCK_STATUS;
  }
}

export async function fetchActivityLogs(
  limit: number = 50,
): Promise<ActivityLogEntry[]> {
  try {
    return await apiFetch<ActivityLogEntry[]>(`/api/logs?limit=${limit}`);
  } catch (error) {
    console.warn(
      "Backend /api/logs missing or failed. Returning empty logs.",
      error,
    );
    return [];
    return [];
  }
}
