import { format, parseISO } from "date-fns";

export function formatDate(isoString: string | null): string {
  if (!isoString) return "—";
  try {
    const date = parseISO(isoString);
    return format(date, "dd.MM.yyyy, HH:mm:ss");
  } catch (error) {
    console.error("Invalid date format:", isoString, error);
    return "—";
  }
}

export function formatNullable(value: string | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return String(value);
}
