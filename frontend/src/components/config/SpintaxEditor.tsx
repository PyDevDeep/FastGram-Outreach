import { useUIStore } from "@/store/uiStore";

interface SpintaxEditorProps {
  value: string;
  onChange: (value: string) => void;
}

export function SpintaxEditor({ value, onChange }: SpintaxEditorProps) {
  const { setConfigDirty } = useUIStore();

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value);
    setConfigDirty(true);
  };

  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <h2 className="text-lg font-semibold text-foreground mb-4">
        Message Template (Spintax)
      </h2>
      <textarea
        value={value}
        onChange={handleChange}
        placeholder="Enter spintax template, e.g.: {Hello|Hi}, {how are you?|how is it going?}"
        className="w-full h-40 bg-background border border-border text-foreground rounded-md p-3 focus:ring-2 focus:ring-ring focus:outline-none resize-y"
      />
      <p className="text-sm text-muted-foreground mt-2">
        Use curly braces and vertical pipes for text variation.
      </p>
    </div>
  );
}
