export type LeadStatus =
  | "pending"
  | "sent"
  | "failed"
  | "replied"
  | "banned"
  | "ignored";
export type LeadTag = "Interested" | "NotInterested" | null;

export interface Lead {
  id: number;
  username: string;
  status: LeadStatus;
  tag: LeadTag;
  sent_at: string | null;
  reply_text: string | null;
  created_at: string;
}

export interface LeadsStats {
  pending: number;
  sent: number;
  failed: number;
  replied: number;
  total: number;
}

export interface PaginatedLeads {
  items: Lead[];
  total: number;
  limit: number;
  offset: number;
}
