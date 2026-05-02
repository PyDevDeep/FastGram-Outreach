import { useSystemStatus } from "@/hooks/useSystemStatus";
import { EmptyState } from "@/components/ui/EmptyState";
import { formatDate } from "@/lib/formatters";

export function ActivityLog() {
  const { logs, isLogsLoading } = useSystemStatus();

  return (
    <div className="bg-card border border-border rounded-lg overflow-hidden flex flex-col h-[400px]">
      <div className="p-5 border-b border-border font-semibold text-foreground">
        Журнал подій
      </div>

      {isLogsLoading && !logs ? (
        <div className="p-5 flex flex-col gap-3">
          <div className="h-10 bg-muted animate-pulse rounded w-full"></div>
          <div className="h-10 bg-muted animate-pulse rounded w-full"></div>
          <div className="h-10 bg-muted animate-pulse rounded w-full"></div>
        </div>
      ) : !logs || logs.length === 0 ? (
        <div className="flex-1 flex items-center justify-center">
          <EmptyState message="Немає подій" />
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-muted/50 sticky top-0 shadow-sm">
              <tr>
                <th className="px-5 py-3 font-medium text-muted-foreground">
                  Час
                </th>
                <th className="px-5 py-3 font-medium text-muted-foreground">
                  Подія
                </th>
                <th className="px-5 py-3 font-medium text-muted-foreground">
                  Деталі
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {logs.map((log) => (
                <tr
                  key={log.id}
                  className="hover:bg-muted/30 transition-colors"
                >
                  <td className="px-5 py-3 text-muted-foreground whitespace-nowrap">
                    {formatDate(log.timestamp)}
                  </td>
                  <td className="px-5 py-3 font-medium text-foreground">
                    {log.event}
                  </td>
                  <td className="px-5 py-3 text-muted-foreground">
                    {log.details || "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
