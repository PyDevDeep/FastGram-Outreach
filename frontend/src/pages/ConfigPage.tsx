import { useState } from "react";
import { PageWrapper } from "@/components/layout/PageWrapper";
import { SpintaxEditor } from "@/components/config/SpintaxEditor";
import { LimitsForm } from "@/components/config/LimitsForm";
import { TimingsForm } from "@/components/config/TimingsForm";
import { ConfigSaveButton } from "@/components/config/ConfigSaveButton";
import { useConfig, useSaveConfig } from "@/hooks/useConfig";
import type { SystemConfig } from "@/types/config";

export default function ConfigPage() {
  const { data: serverConfig, isLoading: isFetching } = useConfig();
  const { mutate: saveConfig, isPending: isSaving } = useSaveConfig();
  const [overrides, setOverrides] = useState<Partial<SystemConfig>>({});

  const localConfig = { ...serverConfig, ...overrides };

  const handleUpdate = (partial: Partial<SystemConfig>) => {
    setOverrides((prev) => ({ ...prev, ...partial }));
  };

  const handleSave = () => {
    if (localConfig.max_daily !== undefined) {
      saveConfig(localConfig as SystemConfig);
    }
  };

  if (isFetching) {
    return (
      <PageWrapper title="Налаштування">
        <div className="flex justify-center py-20">
          <div className="animate-pulse text-muted-foreground">
            Завантаження конфігурації...
          </div>
        </div>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper title="Налаштування">
      <div className="flex flex-col gap-6 pb-20">
        <SpintaxEditor
          value={localConfig.message_template || ""}
          onChange={(val) => handleUpdate({ message_template: val })}
        />
        <LimitsForm config={localConfig} onChange={handleUpdate} />
        <TimingsForm config={localConfig} onChange={handleUpdate} />

        <div className="fixed bottom-0 left-0 right-0 p-4 bg-background/80 backdrop-blur-md border-t border-border flex justify-end px-8 z-10 lg:pl-72">
          <ConfigSaveButton onSave={handleSave} isLoading={isSaving} />
        </div>
      </div>
    </PageWrapper>
  );
}
