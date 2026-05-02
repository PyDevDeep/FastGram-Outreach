import React from "react";
import type { LeadStatus } from "@/types/lead";

interface LeadStatusSelectProps {
  currentStatus: LeadStatus;
  leadId: number;
  onChange: (id: number, newStatus: LeadStatus) => void;
  disabled?: boolean;
}

const STATUS_OPTIONS: LeadStatus[] = [
  "pending",
  "sent",
  "replied",
  "failed",
  "banned",
  "ignored",
];

export function LeadStatusSelect({
  currentStatus,
  leadId,
  onChange,
  disabled,
}: LeadStatusSelectProps) {
  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onChange(leadId, e.target.value as LeadStatus);
  };

  return (
    <select
      value={currentStatus}
      onChange={handleChange}
      disabled={disabled}
      className="bg-background border border-border text-foreground text-xs rounded px-2 py-1 focus:ring-1 focus:ring-ring focus:outline-none w-full max-w-[120px] disabled:opacity-50"
    >
      {STATUS_OPTIONS.map((status) => (
        <option key={status} value={status}>
          {status.charAt(0).toUpperCase() + status.slice(1)}
        </option>
      ))}
    </select>
  );
}
