import React, { useMemo } from "react";
import type { DecoratorFunction } from "@storybook/csf";
import type { ReactRenderer } from "@storybook/react";
import { MessagingContext } from "../src/context/MessagingContext";

const withMessaging: DecoratorFunction<ReactRenderer> = (Story, context) => {
  const messagingConfig = context.parameters.messaging || {};

  const mockMessaging = useMemo(() => ({
    enabled: messagingConfig.enabled ?? false,
    permissionDenied: messagingConfig.permissionDenied ?? false,
    error: messagingConfig.error ?? null,
    isLoading: messagingConfig.isLoading ?? false,
    disableMessaging: messagingConfig.disableMessaging ?? (async () => {}),
    enableMessaging: messagingConfig.enableMessaging ?? (async () => {}),
  }), [messagingConfig]);

  return (
    <MessagingContext.Provider value={mockMessaging}>
      <Story />
    </MessagingContext.Provider>
  );
};

export default withMessaging;
