import { useQuery } from "@tanstack/react-query";
import { fetchLeads } from "@/api/leads";

export function useLeads(limit: number, offset: number) {
  return useQuery({
    queryKey: ["leads", limit, offset],
    queryFn: () => fetchLeads(limit, offset),
  });
}
