import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
const API_KEY = import.meta.env.VITE_API_KEY;

if (!API_BASE_URL || !API_KEY) {
  console.error(
    "КРИТИЧНО: Відсутні змінні оточення VITE_API_BASE_URL або VITE_API_KEY",
  );
}

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json",
  },
});

export const getLeads = async (limit = 100, offset = 0) => {
  const response = await apiClient.get(
    `/leads/?limit=${limit}&offset=${offset}`,
  );
  return response.data;
};

export const getStats = async () => {
  const response = await apiClient.get("/leads/stats");
  return response.data;
};

export const syncLeads = async () => {
  const response = await apiClient.post("/leads/sync");
  return response.data;
};
export const checkAuthStatus = async () => {
  const response = await apiClient.get("/auth/status");
  return response.data;
};

export const triggerLogin = async (code?: string) => {
  const response = await apiClient.post("/auth/login", {
    verification_code: code,
  });
  return response.data;
};
