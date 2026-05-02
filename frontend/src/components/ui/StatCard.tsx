import type { ReactNode } from "react";

interface StatCardProps {
  label: string;
  value: number | undefined;
  icon: ReactNode;
  isLoading: boolean;
}

export function StatCard({ label, value, icon, isLoading }: StatCardProps) {
  return (
    <div className="bg-card p-6 rounded-lg border border-border flex flex-col gap-2">
      <div className="flex items-center gap-2 text-muted-foreground text-sm uppercase tracking-wider">
        {icon}
        <span>{label}</span>
      </div>
      <div className="text-3xl font-bold">
        {isLoading ? (
          <div
            data-testid="skeleton"
            className="h-9 w-16 bg-muted animate-pulse rounded"
          />
        ) : (
          (value ?? 0)
        )}
      </div>
    </div>
  );
}
