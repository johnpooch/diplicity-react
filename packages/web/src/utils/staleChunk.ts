const RELOAD_TIMESTAMP_KEY = "stale-chunk-reload-at";
const RELOAD_DEBOUNCE_MS = 10_000;

const STALE_CHUNK_MESSAGES = [
  "Failed to fetch dynamically imported module",
  "error loading dynamically imported module",
  "Importing a module script failed",
  "Expected a JavaScript-or-Wasm module script",
];

export const isStaleChunkError = (error: unknown): boolean => {
  const message =
    error instanceof Error
      ? error.message
      : typeof error === "string"
        ? error
        : "";
  return STALE_CHUNK_MESSAGES.some((candidate) => message.includes(candidate));
};

export const reloadForStaleChunk = (): void => {
  const lastReloadAt = Number(
    sessionStorage.getItem(RELOAD_TIMESTAMP_KEY) ?? "0"
  );
  if (Date.now() - lastReloadAt < RELOAD_DEBOUNCE_MS) return;
  sessionStorage.setItem(RELOAD_TIMESTAMP_KEY, String(Date.now()));
  window.location.reload();
};
