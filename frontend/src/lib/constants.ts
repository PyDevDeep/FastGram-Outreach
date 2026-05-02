import type { LeadStatus } from "@/types/lead";

export const STATUS_COLORS: Record<LeadStatus, string> = {
  pending: "bg-amber-500/10 text-amber-500 border-amber-500/20",
  sent: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
  replied: "bg-blue-500/10 text-blue-500 border-blue-500/20",
  failed: "bg-red-500/10 text-red-500 border-red-500/20",
  banned: "bg-rose-500/10 text-rose-500 border-rose-500/20",
  ignored: "bg-slate-500/10 text-slate-500 border-slate-500/20",
};

export const TAG_COLORS: Record<string, string> = {
  Interested: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
  NotInterested: "bg-red-500/10 text-red-500 border-red-500/20",
};

export const POLL_INTERVALS = {
  STATUS_MS: 10000,
  LOGS_MS: 15000,
} as const;

export const PAGE_SIZE = 50;
