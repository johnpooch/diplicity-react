const FAST_INTERVAL_MS = 5_000;
const IDLE_INTERVAL_MS = 15_000;
const QUIET_INTERVAL_MS = 60_000;
const GAME_IDLE_THRESHOLD_MS = 60_000;
const GAME_QUIET_THRESHOLD_MS = 300_000;
const CHANNEL_IDLE_THRESHOLD_MS = 120_000;

interface PollStep {
  idleFor: number;
  interval: number;
}

interface PollQuery<Data> {
  queryHash: string;
  state: {
    data: Data | undefined;
    isInvalidated: boolean;
  };
}

export const GAME_POLL_SCHEDULE: readonly PollStep[] = [
  { idleFor: 0, interval: FAST_INTERVAL_MS },
  { idleFor: GAME_IDLE_THRESHOLD_MS, interval: IDLE_INTERVAL_MS },
  { idleFor: GAME_QUIET_THRESHOLD_MS, interval: QUIET_INTERVAL_MS },
];

export const CHANNEL_POLL_SCHEDULE: readonly PollStep[] = [
  { idleFor: 0, interval: FAST_INTERVAL_MS },
  { idleFor: CHANNEL_IDLE_THRESHOLD_MS, interval: IDLE_INTERVAL_MS },
];

export const createAdaptiveRefetchInterval = <Data>(
  schedule: readonly PollStep[],
  enabled?: (data: Data | undefined) => boolean
) => {
  let previousData: Data | undefined;
  let previousQueryHash: string | undefined;
  let lastChangedAt = Date.now();

  const reset = () => {
    lastChangedAt = Date.now();
  };

  const refetchInterval = (query: PollQuery<Data>) => {
    if (
      query.queryHash !== previousQueryHash ||
      query.state.data !== previousData ||
      query.state.isInvalidated
    ) {
      previousQueryHash = query.queryHash;
      previousData = query.state.data;
      reset();
    }
    if (enabled && !enabled(query.state.data)) return false;
    const idleFor = Date.now() - lastChangedAt;
    return schedule.reduce(
      (interval, step) => (idleFor >= step.idleFor ? step.interval : interval),
      FAST_INTERVAL_MS
    );
  };

  return { refetchInterval, reset };
};
