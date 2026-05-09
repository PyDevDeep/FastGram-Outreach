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
  // FastAPI currently returns an array of objects instead of paginated structure.
  // Map the response to match the PaginatedLeads interface.
  const items = await apiFetch<Lead[]>(
    `/api/leads/?limit=${limit}&offset=${offset}`,
  );

  return {
    items: Array.isArray(items) ? items : [],
    total: 1000, // TODO: Replace with real value when FastAPI starts returning count
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
