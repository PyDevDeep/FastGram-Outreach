import { useUIStore } from "@/store/uiStore";

export function useSync() {
  const { setSyncing } = useUIStore();

  const mutate = () => {
    setSyncing(true);
    // Симуляція запиту на час розробки UI
    setTimeout(() => {
      setSyncing(false);
    }, 2000);
  };

  return { mutate, isPending: false };
}
