import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";

import { PageWrapper } from "@/components/layout/PageWrapper";
import { LeadsTable } from "@/components/leads/LeadsTable";
import { SyncButton } from "@/components/leads/SyncButton";
import { Pagination } from "@/components/leads/Pagination";

import { useLeads } from "@/hooks/useLeads";
import { updateLeadStatus } from "@/api/leads";
import { PAGE_SIZE } from "@/lib/constants";
import type { LeadStatus } from "@/types/lead";

export default function LeadsPage() {
  const [offset, setOffset] = useState(0);
  const { data, isLoading } = useLeads(PAGE_SIZE, offset);
  const queryClient = useQueryClient();

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: LeadStatus }) =>
      updateLeadStatus(id, status),
    onSuccess: () => {
      toast.success("Статус оновлено");
      queryClient.invalidateQueries({ queryKey: ["leads"] });
      queryClient.invalidateQueries({ queryKey: ["leads-stats"] });
    },
    onError: (error: Error) => {
      toast.error(error.message || "Помилка оновлення статусу");
    },
  });

  const handleStatusChange = (id: number, status: LeadStatus) => {
    statusMutation.mutate({ id, status });
  };

  const handlePrev = () => setOffset((prev) => Math.max(0, prev - PAGE_SIZE));
  const handleNext = () => setOffset((prev) => prev + PAGE_SIZE);

  const leads = data?.items || [];
  const total = data?.total || 0;

  return (
    <PageWrapper title="Управління лідами">
      <div className="flex justify-end mb-4">
        <SyncButton />
      </div>

      <LeadsTable
        leads={leads}
        isLoading={isLoading}
        onStatusChange={handleStatusChange}
      />

      <Pagination
        offset={offset}
        limit={PAGE_SIZE}
        total={total}
        onPrev={handlePrev}
        onNext={handleNext}
      />
    </PageWrapper>
  );
}
