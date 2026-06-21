export const FREQUENCY_SECONDS: Record<string, number> = {
  hourly: 3600,
  daily: 86400,
  every_2_days: 172800,
  weekly: 604800,
};

export function formatDurationSeconds(seconds: number): string {
  if (seconds < 3600) {
    const mins = Math.round(seconds / 60);
    return `${mins} ${mins === 1 ? "minute" : "minutes"}`;
  }
  if (seconds % 86400 === 0) {
    const days = seconds / 86400;
    return `${days} ${days === 1 ? "day" : "days"}`;
  }
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.round((seconds % 3600) / 60);
  if (mins === 0) return `${hrs} ${hrs === 1 ? "hour" : "hours"}`;
  return `${hrs}h ${mins}m`;
}
