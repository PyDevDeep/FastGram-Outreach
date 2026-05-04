import { useUIStore } from "@/store/uiStore";
import type { SystemConfig } from "@/types/config";

interface TimingsFormProps {
  config: Partial<SystemConfig>;
  onChange: (partial: Partial<SystemConfig>) => void;
}

export function TimingsForm({ config, onChange }: TimingsFormProps) {
  const { setConfigDirty } = useUIStore();

  const handleChange = (field: keyof SystemConfig, value: number) => {
    onChange({ [field]: value });
    setConfigDirty(true);
  };

  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <h2 className="text-lg font-semibold text-foreground mb-4">
        Паузи та Робочі години
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6">
        <div>
          <label className="block text-sm font-medium text-muted-foreground mb-1">
            Мін. затримка (с)
          </label>
          <input
            type="number"
            min="1"
            value={config.min_seconds || 0}
            onChange={(e) =>
              handleChange("min_seconds", parseInt(e.target.value) || 0)
            }
            className="w-full bg-background border border-border text-foreground rounded px-3 py-2 focus:ring-1 focus:ring-ring focus:outline-none"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-muted-foreground mb-1">
            Макс. затримка (с)
          </label>
          <input
            type="number"
            min="1"
            value={config.max_seconds || 0}
            onChange={(e) =>
              handleChange("max_seconds", parseInt(e.target.value) || 0)
            }
            className="w-full bg-background border border-border text-foreground rounded px-3 py-2 focus:ring-1 focus:ring-ring focus:outline-none"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-muted-foreground mb-1">
            Початок роботи (год)
          </label>
          <input
            type="number"
            min="0"
            max="23"
            value={config.work_hours_start || 0}
            onChange={(e) =>
              handleChange("work_hours_start", parseInt(e.target.value) || 0)
            }
            className="w-full bg-background border border-border text-foreground rounded px-3 py-2 focus:ring-1 focus:ring-ring focus:outline-none"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-muted-foreground mb-1">
            Кінець роботи (год)
          </label>
          <input
            type="number"
            min="0"
            max="23"
            value={config.work_hours_end || 0}
            onChange={(e) =>
              handleChange("work_hours_end", parseInt(e.target.value) || 0)
            }
            className="w-full bg-background border border-border text-foreground rounded px-3 py-2 focus:ring-1 focus:ring-ring focus:outline-none"
          />
        </div>
      </div>
    </div>
  );
}
