import { useQuery } from "@tanstack/react-query";
import { fetchSystemStatus, fetchActivityLogs } from "@/api/status";
import { POLL_INTERVALS } from "@/lib/constants";

export function useSystemStatus() {
  const statusQuery = useQuery({
    queryKey: ["system-status"],
    queryFn: fetchSystemStatus,
    refetchInterval: POLL_INTERVALS.STATUS_MS,
    refetchIntervalInBackground: false,
  });

  const logsQuery = useQuery({
    queryKey: ["activity-logs"],
    queryFn: () => fetchActivityLogs(50),
    refetchInterval: POLL_INTERVALS.LOGS_MS,
    refetchIntervalInBackground: false,
  });

  return {
    status: statusQuery.data,
    logs: logsQuery.data,
    isStatusLoading: statusQuery.isLoading,
    isLogsLoading: logsQuery.isLoading,
  };
}
