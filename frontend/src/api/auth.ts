import { apiFetch } from "./client";
import type { AuthStatusResponse, LoginResponse } from "@/types/auth";

export function checkAuthStatus(): Promise<AuthStatusResponse> {
  return apiFetch<AuthStatusResponse>("/api/auth/status");
}

export function triggerLogin(
  verificationCode?: string,
): Promise<LoginResponse> {
  return apiFetch<LoginResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ verification_code: verificationCode || null }),
  });
}
