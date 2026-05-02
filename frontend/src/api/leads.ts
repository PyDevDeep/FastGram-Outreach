import { apiFetch } from "./client";
import type {
  PaginatedLeads,
  LeadsStats,
  Lead,
  LeadStatus,
} from "@/types/lead";

export async function fetchLeads(
  limit: number,
  offset: number,
): Promise<PaginatedLeads> {
  // FastAPI зараз повертає масив об'єктів замість пагінованої структури.
  // Мапимо відповідь для відповідності інтерфейсу PaginatedLeads.
  const items = await apiFetch<Lead[]>(
    `/api/leads/?limit=${limit}&offset=${offset}`,
  );

  return {
    items: Array.isArray(items) ? items : [],
    total: 1000, // TODO: Замінити на реальне значення, коли FastAPI почне віддавати count
    limit,
    offset,
  };
}

export function fetchLeadsStats(): Promise<LeadsStats> {
  return apiFetch<LeadsStats>("/api/leads/stats");
}

export function syncLeads(): Promise<{ message: string }> {
  return apiFetch<{ message: string }>("/api/leads/sync", { method: "POST" });
}

export function updateLeadStatus(
  id: number,
  status: LeadStatus,
): Promise<Lead> {
  return apiFetch<Lead>(`/api/leads/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}
