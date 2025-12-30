import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { DecoratorFunction } from "@storybook/csf";
import type { ReactRenderer } from "@storybook/react";

const withQueryClient: DecoratorFunction<ReactRenderer> = Story => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: Infinity,
      },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <Story />
    </QueryClientProvider>
  );
};

export default withQueryClient;
