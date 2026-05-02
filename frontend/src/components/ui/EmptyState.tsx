import { FileX } from "lucide-react";

interface EmptyStateProps {
  message?: string;
}

export function EmptyState({ message = "Немає даних" }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-muted-foreground bg-card border border-border rounded-md">
      <FileX className="w-12 h-12 mb-4 opacity-20" />
      <p className="text-sm font-medium">{message}</p>
    </div>
  );
}
