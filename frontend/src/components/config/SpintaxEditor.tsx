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
        Шаблон повідомлення (Spintax)
      </h2>
      <textarea
        value={value}
        onChange={handleChange}
        placeholder="Введіть spintax-шаблон, наприклад: {Привіт|Вітаю}, {як справи?|як успіхи?}"
        className="w-full h-40 bg-background border border-border text-foreground rounded-md p-3 focus:ring-2 focus:ring-ring focus:outline-none resize-y"
      />
      <p className="text-sm text-muted-foreground mt-2">
        Використовуйте фігурні дужки та вертикальну риску для варіативності
        тексту.
      </p>
    </div>
  );
}
