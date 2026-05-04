import { useUIStore } from "@/store/uiStore";
import { Spinner } from "@/components/ui/Spinner";
import { Save } from "lucide-react";

interface ConfigSaveButtonProps {
  onSave: () => void;
  isLoading: boolean;
}

export function ConfigSaveButton({ onSave, isLoading }: ConfigSaveButtonProps) {
  const { configDirty } = useUIStore();

  return (
    <button
      onClick={onSave}
      disabled={!configDirty || isLoading}
      className="inline-flex items-center justify-center gap-2 px-6 py-2 text-sm font-medium transition-colors rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:pointer-events-none"
    >
      {isLoading ? <Spinner size="sm" /> : <Save className="w-4 h-4" />}
      Зберегти конфігурацію
    </button>
  );
}
