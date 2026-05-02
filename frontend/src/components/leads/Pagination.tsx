import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";

interface PaginationProps {
  offset: number;
  limit: number;
  total: number;
  onPrev: () => void;
  onNext: () => void;
}

export function Pagination({
  offset,
  limit,
  total,
  onPrev,
  onNext,
}: PaginationProps) {
  const start = total === 0 ? 0 : offset + 1;
  const end = Math.min(offset + limit, total);

  return (
    <div className="flex items-center justify-between px-2 py-4 border-t border-border mt-4">
      <div className="text-sm text-muted-foreground">
        Записи {start}–{end} з {total}
      </div>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={onPrev}
          disabled={offset === 0}
        >
          <ChevronLeft className="w-4 h-4 mr-1" />
          Попередня
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onNext}
          disabled={offset + limit >= total}
        >
          Наступна
          <ChevronRight className="w-4 h-4 ml-1" />
        </Button>
      </div>
    </div>
  );
}
