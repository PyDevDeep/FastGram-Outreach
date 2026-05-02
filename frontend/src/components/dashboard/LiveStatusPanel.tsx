import { useSystemStatus } from "@/hooks/useSystemStatus";
import { StatusIndicator } from "@/components/ui/StatusIndicator";

export function LiveStatusPanel() {
  const { status, isStatusLoading } = useSystemStatus();

  const isEngineActive = status?.engine_active ?? false;
  const isProxyValid = status?.proxy_valid ?? false;
  const isAccountValid = status?.account_valid ?? false;
  const isBanned = status?.account_banned ?? false;

  return (
    <div className="bg-card border border-border rounded-lg p-6 flex flex-col gap-6 h-full">
      <h2 className="text-lg font-semibold text-foreground">Статус Системи</h2>

      {isStatusLoading && !status ? (
        <div className="flex flex-col gap-4">
          <div className="h-5 bg-muted animate-pulse rounded w-3/4"></div>
          <div className="h-5 bg-muted animate-pulse rounded w-2/3"></div>
          <div className="h-5 bg-muted animate-pulse rounded w-1/2"></div>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          <StatusIndicator active={isEngineActive} label="Outreach Engine" />
          <StatusIndicator active={isProxyValid} label="Proxy Connection" />
          <StatusIndicator
            active={isAccountValid && !isBanned}
            label={isBanned ? "Account (BANNED)" : "Instagram Account"}
          />
        </div>
      )}
    </div>
  );
}
