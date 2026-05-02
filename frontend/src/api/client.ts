const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";
const API_KEY = import.meta.env.VITE_API_KEY || "";

export async function apiFetch<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const url = `${BASE_URL}${path}`;

  const defaultHeaders: HeadersInit = {
    "Content-Type": "application/json",
    ...(API_KEY ? { "X-API-Key": API_KEY } : {}),
  };

  const config: RequestInit = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options?.headers,
    },
  };

  const response = await fetch(url, config);

  if (!response.ok) {
    const errorBody = await response.text();
    console.error(
      `[API Error] ${response.status} ${response.statusText}`,
      errorBody,
    );
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  // Якщо відповідь порожня (наприклад, 204 No Content), повертаємо порожній об'єкт
  const text = await response.text();
  return text ? JSON.parse(text) : ({} as T);
}
