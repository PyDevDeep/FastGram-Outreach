interface StatusIndicatorProps {
  active: boolean;
  label: string;
}

export function StatusIndicator({ active, label }: StatusIndicatorProps) {
  return (
    <div className="flex items-center gap-2">
      <div className="relative flex h-3 w-3">
        {active && (
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
        )}
        <span
          className={`relative inline-flex rounded-full h-3 w-3 ${
            active ? "bg-emerald-500" : "bg-slate-500"
          }`}
        ></span>
      </div>
      <span className="text-sm font-medium text-foreground">{label}</span>
    </div>
  );
}
