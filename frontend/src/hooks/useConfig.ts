import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchConfig, saveConfig } from "@/api/config";
import { useUIStore } from "@/store/uiStore";
import toast from "react-hot-toast";
import type { SystemConfig } from "@/types/config";

export function useConfig() {
  return useQuery({
    queryKey: ["config"],
    queryFn: fetchConfig,
    staleTime: 0, // Конфіг не кешується агресивно, завжди свіжий при відкритті сторінки
  });
}

export function useSaveConfig() {
  const queryClient = useQueryClient();
  const { setConfigDirty } = useUIStore();

  return useMutation({
    mutationFn: (config: SystemConfig) => saveConfig(config),
    onSuccess: () => {
      toast.success("Конфігурацію збережено");
      queryClient.invalidateQueries({ queryKey: ["config"] });
      setConfigDirty(false);
    },
    onError: (error: Error) => {
      toast.error(error.message || "Помилка збереження конфігурації");
    },
  });
}
