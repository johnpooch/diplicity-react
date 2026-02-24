import React, { useMemo } from "react";
import type { DecoratorFunction } from "@storybook/csf";
import type { ReactRenderer } from "@storybook/react";
import { MessagingOverrideContext } from "../src/hooks/useMessaging";

type MessagingWrapperProps = {
  children: React.ReactNode;
  messagingConfig: Record<string, unknown>;
};

const MessagingWrapper: React.FC<MessagingWrapperProps> = ({
  children,
  messagingConfig,
}) => {
  const mockMessaging = useMemo(
    () => ({
      enabled: (messagingConfig?.enabled as boolean) ?? false,
      permissionDenied: (messagingConfig?.permissionDenied as boolean) ?? false,
      error: (messagingConfig?.error as string | null) ?? null,
      isLoading: (messagingConfig?.isLoading as boolean) ?? false,
      disableMessaging:
        (messagingConfig?.disableMessaging as () => Promise<void>) ??
        (async () => {}),
      enableMessaging:
        (messagingConfig?.enableMessaging as () => Promise<void>) ??
        (async () => {}),
    }),
    [messagingConfig]
  );

  return (
    <MessagingOverrideContext.Provider value={mockMessaging}>
      {children}
    </MessagingOverrideContext.Provider>
  );
};

const withMessaging: DecoratorFunction<ReactRenderer> = (Story, context) => {
  const messagingConfig = context.parameters.messaging || {};

  return (
    <MessagingWrapper messagingConfig={messagingConfig}>
      <Story />
    </MessagingWrapper>
  );
};

export default withMessaging;
