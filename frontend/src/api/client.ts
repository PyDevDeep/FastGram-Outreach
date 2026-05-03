const rawBaseUrl = import.meta.env.VITE_API_BASE_URL || "";
const BASE_URL = rawBaseUrl.endsWith("/")
  ? rawBaseUrl.slice(0, -1)
  : rawBaseUrl;
const API_KEY = import.meta.env.VITE_API_KEY || "";

export async function apiFetch<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const cleanPath = path.startsWith("/") ? path : `/${path}`;

  // Запобігання генерації дубльованого /api/api/
  const url =
    BASE_URL.endsWith("/api") && cleanPath.startsWith("/api")
      ? `${BASE_URL}${cleanPath.slice(4)}`
      : `${BASE_URL}${cleanPath}`;

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
