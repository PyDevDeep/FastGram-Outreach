import { QueryClient } from "@tanstack/react-query";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000, // 30 секунд (дані вважаються свіжими)
      retry: 2, // дві повторні спроби при помилці
      refetchOnWindowFocus: false, // polling покриватиме фокус
    },
  },
});
