import { useLeadsStats } from "@/hooks/useLeadsStats";
import { StatCard } from "@/components/ui/StatCard";
import { Clock, Send, XCircle, MessageCircle, Hash } from "lucide-react";

export function StatsRow() {
  const { data, isLoading } = useLeadsStats();

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-4">
      <StatCard
        label="Pending"
        value={data?.pending}
        icon={<Clock className="w-4 h-4 text-amber-500" />}
        isLoading={isLoading}
      />
      <StatCard
        label="Sent"
        value={data?.sent}
        icon={<Send className="w-4 h-4 text-emerald-500" />}
        isLoading={isLoading}
      />
      <StatCard
        label="Failed"
        value={data?.failed}
        icon={<XCircle className="w-4 h-4 text-red-500" />}
        isLoading={isLoading}
      />
      <StatCard
        label="Replied"
        value={data?.replied}
        icon={<MessageCircle className="w-4 h-4 text-blue-500" />}
        isLoading={isLoading}
      />
      <StatCard
        label="Total"
        value={data?.total}
        icon={<Hash className="w-4 h-4 text-slate-500" />}
        isLoading={isLoading}
      />
    </div>
  );
}
