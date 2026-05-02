export function TopBar() {
  return (
    <header className="h-16 bg-card border-b border-border flex items-center justify-between px-8 flex-shrink-0">
      <div className="font-medium text-muted-foreground">
        Outreach Dashboard
      </div>
      <div id="topbar-status-slot" className="flex items-center gap-4">
        {/* Слот зарезервовано для індикаторів стану з Phase 3 */}
      </div>
    </header>
  );
}
