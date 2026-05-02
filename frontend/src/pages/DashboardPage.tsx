import { PageWrapper } from "@/components/layout/PageWrapper";
import { StatsRow } from "@/components/dashboard/StatsRow";
import { LiveStatusPanel } from "@/components/dashboard/LiveStatusPanel";
import { ActivityLog } from "@/components/dashboard/ActivityLog";

export default function DashboardPage() {
  return (
    <PageWrapper title="Дашборд">
      <StatsRow />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <LiveStatusPanel />
        </div>
        <div className="lg:col-span-2">
          <ActivityLog />
        </div>
      </div>
    </PageWrapper>
  );
}
