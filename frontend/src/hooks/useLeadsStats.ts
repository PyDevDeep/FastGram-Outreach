import { useQuery } from "@tanstack/react-query";
import { fetchLeadsStats } from "@/api/leads";

export function useLeadsStats() {
  return useQuery({
    queryKey: ["leads-stats"],
    queryFn: fetchLeadsStats,
  });
}
