import { QueryClient } from "@tanstack/react-query";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000, // 30 seconds (data considered fresh)
      retry: 2, // two retries on error
      refetchOnWindowFocus: false, // polling will cover focus
    },
  },
});
