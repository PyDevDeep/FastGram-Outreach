import { useMutation, useQueryClient } from "@tanstack/react-query";
import { syncLeads } from "@/api/leads";
import { useUIStore } from "@/store/uiStore";
import toast from "react-hot-toast";

export function useSync() {
  const { setSyncing } = useUIStore();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: syncLeads,
    onMutate: () => {
      setSyncing(true);
    },
    onSuccess: () => {
      setSyncing(false);
      toast.success("Синхронізовано з Sheets");
      // Інвалідуємо кеш, щоб таблиця та статистика оновилися автоматично
      queryClient.invalidateQueries({ queryKey: ["leads"] });
      queryClient.invalidateQueries({ queryKey: ["leads-stats"] });
    },
    onError: (error: Error) => {
      setSyncing(false);
      toast.error(error.message || "Помилка синхронізації");
    },
  });
}
