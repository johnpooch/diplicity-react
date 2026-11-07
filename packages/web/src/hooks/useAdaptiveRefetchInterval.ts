import { useEffect, useMemo } from "react";
import { focusManager } from "@tanstack/react-query";
import { createAdaptiveRefetchInterval } from "./adaptiveRefetchInterval";

export const useAdaptiveRefetchInterval = <Data>(
  schedule: Parameters<typeof createAdaptiveRefetchInterval<Data>>[0],
  enabled?: (data: Data | undefined) => boolean
) => {
  const { refetchInterval, reset } = useMemo(
    () => createAdaptiveRefetchInterval(schedule, enabled),
    [schedule, enabled]
  );

  useEffect(
    () =>
      focusManager.subscribe(focused => {
        if (focused) reset();
      }),
    [reset]
  );

  return refetchInterval;
};
