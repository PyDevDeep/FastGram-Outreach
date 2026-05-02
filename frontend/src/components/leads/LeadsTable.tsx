import type { Lead, LeadStatus } from "@/types/lead";
import { LeadRow } from "./LeadRow";
import { EmptyState } from "@/components/ui/EmptyState";

interface LeadsTableProps {
  leads: Lead[];
  isLoading: boolean;
  onStatusChange: (id: number, status: LeadStatus) => void;
}

export function LeadsTable({
  leads,
  isLoading,
  onStatusChange,
}: LeadsTableProps) {
  if (isLoading) {
    return (
      <div className="w-full border border-border rounded-md overflow-hidden bg-card">
        <table className="w-full text-left text-sm">
          <thead className="bg-muted/50 border-b border-border text-muted-foreground">
            <tr>
              <th className="px-4 py-3 font-medium">Username</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Tag</th>
              <th className="px-4 py-3 font-medium">Sent At</th>
              <th className="px-4 py-3 font-medium">Reply Text</th>
              <th className="px-4 py-3 font-medium text-right">Action</th>
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: 5 }).map((_, i) => (
              <tr key={i} className="border-b border-border">
                <td className="px-4 py-3">
                  <div className="h-4 bg-muted animate-pulse rounded w-24"></div>
                </td>
                <td className="px-4 py-3">
                  <div className="h-4 bg-muted animate-pulse rounded w-16"></div>
                </td>
                <td className="px-4 py-3">
                  <div className="h-4 bg-muted animate-pulse rounded w-20"></div>
                </td>
                <td className="px-4 py-3">
                  <div className="h-4 bg-muted animate-pulse rounded w-32"></div>
                </td>
                <td className="px-4 py-3">
                  <div className="h-4 bg-muted animate-pulse rounded w-48"></div>
                </td>
                <td className="px-4 py-3">
                  <div className="h-6 bg-muted animate-pulse rounded w-28 ml-auto"></div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (leads.length === 0) {
    return <EmptyState message="Лідів не знайдено" />;
  }

  return (
    <div className="w-full border border-border rounded-md overflow-x-auto bg-card">
      <table className="w-full text-left text-sm min-w-[800px]">
        <thead className="bg-muted/50 border-b border-border text-muted-foreground">
          <tr>
            <th className="px-4 py-3 font-medium">Username</th>
            <th className="px-4 py-3 font-medium">Status</th>
            <th className="px-4 py-3 font-medium">Tag</th>
            <th className="px-4 py-3 font-medium">Sent At</th>
            <th className="px-4 py-3 font-medium">Reply Text</th>
            <th className="px-4 py-3 font-medium text-right">Action</th>
          </tr>
        </thead>
        <tbody>
          {leads.map((lead) => (
            <LeadRow
              key={lead.id}
              lead={lead}
              onStatusChange={onStatusChange}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}
