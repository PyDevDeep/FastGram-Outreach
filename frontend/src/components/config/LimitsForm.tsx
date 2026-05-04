import { useUIStore } from "@/store/uiStore";
import type { SystemConfig } from "@/types/config";

interface LimitsFormProps {
  config: Partial<SystemConfig>;
  onChange: (partial: Partial<SystemConfig>) => void;
}

export function LimitsForm({ config, onChange }: LimitsFormProps) {
  const { setConfigDirty } = useUIStore();

  const handleChange = (field: keyof SystemConfig, value: number) => {
    onChange({ [field]: value });
    setConfigDirty(true);
  };

  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <h2 className="text-lg font-semibold text-foreground mb-4">
        Ліміти та Прогрів
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div>
          <label className="block text-sm font-medium text-muted-foreground mb-1">
            Макс. на день
          </label>
          <input
            type="number"
            min="1"
            value={config.max_daily || 0}
            onChange={(e) =>
              handleChange("max_daily", parseInt(e.target.value) || 0)
            }
            className="w-full bg-background border border-border text-foreground rounded px-3 py-2 focus:ring-1 focus:ring-ring focus:outline-none"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-muted-foreground mb-1">
            Початковий ліміт (Warmup)
          </label>
          <input
            type="number"
            min="1"
            value={config.initial_limit || 0}
            onChange={(e) =>
              handleChange("initial_limit", parseInt(e.target.value) || 0)
            }
            className="w-full bg-background border border-border text-foreground rounded px-3 py-2 focus:ring-1 focus:ring-ring focus:outline-none"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-muted-foreground mb-1">
            Крок збільшення (Warmup)
          </label>
          <input
            type="number"
            min="1"
            value={config.step || 0}
            onChange={(e) =>
              handleChange("step", parseInt(e.target.value) || 0)
            }
            className="w-full bg-background border border-border text-foreground rounded px-3 py-2 focus:ring-1 focus:ring-ring focus:outline-none"
          />
        </div>
      </div>
    </div>
  );
}
