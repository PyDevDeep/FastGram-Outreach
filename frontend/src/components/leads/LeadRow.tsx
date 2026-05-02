import type { Lead, LeadStatus } from "@/types/lead";
import { formatDate, formatNullable } from "@/lib/formatters";
import { Badge } from "@/components/ui/Badge";
import { LeadStatusSelect } from "./LeadStatusSelect";

interface LeadRowProps {
  lead: Lead;
  onStatusChange: (id: number, status: LeadStatus) => void;
  isUpdating?: boolean;
}

export function LeadRow({ lead, onStatusChange, isUpdating }: LeadRowProps) {
  return (
    <tr className="border-b border-border hover:bg-muted/50 transition-colors">
      <td className="px-4 py-3 text-sm font-medium text-foreground whitespace-nowrap">
        {lead.username}
      </td>
      <td className="px-4 py-3 whitespace-nowrap">
        <Badge value={lead.status} />
      </td>
      <td className="px-4 py-3 whitespace-nowrap">
        <Badge value={lead.tag} />
      </td>
      <td className="px-4 py-3 text-sm text-muted-foreground whitespace-nowrap">
        {formatDate(lead.sent_at)}
      </td>
      <td
        className="px-4 py-3 text-sm text-muted-foreground max-w-xs truncate"
        title={lead.reply_text || ""}
      >
        {formatNullable(lead.reply_text)}
      </td>
      <td className="px-4 py-3 text-right whitespace-nowrap">
        <LeadStatusSelect
          currentStatus={lead.status}
          leadId={lead.id}
          onChange={onStatusChange}
          disabled={isUpdating}
        />
      </td>
    </tr>
  );
}
