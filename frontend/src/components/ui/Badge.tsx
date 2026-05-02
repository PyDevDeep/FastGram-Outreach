import { STATUS_COLORS, TAG_COLORS } from "@/lib/constants";
import type { LeadStatus } from "@/types/lead";

interface BadgeProps {
  value: string | null;
}

export function Badge({ value }: BadgeProps) {
  if (!value) return <span>—</span>;

  const colorClass =
    STATUS_COLORS[value as LeadStatus] ||
    TAG_COLORS[value] ||
    "bg-slate-500/10 text-slate-500 border-slate-500/20"; // нейтральний fallback

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border uppercase ${colorClass}`}
    >
      {value}
    </span>
  );
}
