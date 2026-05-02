import { RefreshCw } from "lucide-react";
import { useUIStore } from "@/store/uiStore";
import { useSync } from "@/hooks/useSync";

export function SyncButton() {
  const { isSyncing } = useUIStore();
  const { mutate } = useSync();

  return (
    <button
      onClick={() => mutate()}
      disabled={isSyncing}
      className="inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium transition-colors rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:pointer-events-none"
    >
      <RefreshCw className={`w-4 h-4 ${isSyncing ? "animate-spin" : ""}`} />
      {isSyncing ? "Синхронізація..." : "Синхронізувати з Sheets"}
    </button>
  );
}
