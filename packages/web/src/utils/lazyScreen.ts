import { lazy } from "react";
import type { ComponentType, FC, LazyExoticComponent } from "react";
import { isStaleChunkError, reloadForStaleChunk } from "./staleChunk";
import {
  recordChunkLoad,
  recordStaleChunkReload,
  type StaleChunkSource,
} from "./chunkTelemetry";

// Rendered for the instant before reloadForStaleChunk() navigates to the fresh
// deploy, instead of crashing into the error boundary.
export const StaleChunkFallback: FC = () => null;

interface LoadOptions {
  navigationWaiting: boolean;
}

// Resolves a lazily-loaded component, healing the stale-chunk failure modes
// that the global `vite:preloadError` handler misses. On WebKit (Safari) and
// some Android Chrome builds, a dynamic import for a chunk that no longer
// exists after a deploy neither fires `vite:preloadError` nor rejects with a
// known message — it resolves to `undefined`, so `module.ScreenName` throws a
// TypeError ("undefined is not an object (evaluating 't.PlayerInfoScreen')")
// that lands in the error boundary and Sentry. Here we detect the undefined
// module / missing export and the known rejection messages, and reload to the
// latest deploy instead. reloadForStaleChunk() debounces via sessionStorage,
// so this cannot loop.
export const healLazyImport = async <T>(
  chunk: string,
  load: () => Promise<T | undefined>,
  fallback: T,
  { navigationWaiting }: LoadOptions = { navigationWaiting: true }
): Promise<{ default: T }> => {
  const startedAt = Date.now();
  const heal = (source: StaleChunkSource, error: unknown) => {
    recordChunkLoad({ chunk, startedAt, outcome: "stale", navigationWaiting });
    if (!navigationWaiting) throw error;
    recordStaleChunkReload(source);
    reloadForStaleChunk();
    return { default: fallback };
  };

  let component: T | undefined;
  try {
    component = await load();
  } catch (error) {
    if (isStaleChunkError(error)) return heal("import_error", error);
    recordChunkLoad({ chunk, startedAt, outcome: "error", navigationWaiting });
    throw error;
  }
  if (!component) {
    return heal("missing_module", new Error(`Missing module for chunk ${chunk}`));
  }
  recordChunkLoad({ chunk, startedAt, outcome: "loaded", navigationWaiting });
  return { default: component };
};

export const resolveScreenModule = <K extends string, M extends Record<K, ComponentType>>(
  factory: () => Promise<M>,
  name: K,
  options?: LoadOptions
) =>
  healLazyImport<ComponentType>(
    name,
    async () => (await factory())?.[name],
    StaleChunkFallback,
    options
  );

export type LazyScreen = LazyExoticComponent<ComponentType> & {
  preload: () => Promise<void>;
};

export const lazyScreen = <K extends string, M extends Record<K, ComponentType>>(
  factory: () => Promise<M>,
  name: K
): LazyScreen => {
  let pending: Promise<{ default: ComponentType }> | undefined;
  const load = (navigationWaiting: boolean) => {
    pending ??= resolveScreenModule(factory, name, { navigationWaiting }).catch(
      error => {
        pending = undefined;
        throw error;
      }
    );
    return pending;
  };
  return Object.assign(
    lazy(() => pending?.catch(() => load(true)) ?? load(true)),
    { preload: () => load(false).then(() => undefined, () => undefined) }
  );
};

const PREFETCH_FALLBACK_DELAY_MS = 500;
const PREFETCH_IDLE_TIMEOUT_MS = 2000;

const whenIdle = () =>
  new Promise<void>(resolve => {
    if (typeof window.requestIdleCallback === "function") {
      window.requestIdleCallback(() => resolve(), {
        timeout: PREFETCH_IDLE_TIMEOUT_MS,
      });
    } else {
      setTimeout(resolve, PREFETCH_FALLBACK_DELAY_MS);
    }
  });

const prefersReducedData = () =>
  (navigator as Navigator & { connection?: { saveData?: boolean } }).connection
    ?.saveData === true;

export const prefetchScreens = async (
  screens: Record<string, LazyScreen>
): Promise<void> => {
  if (prefersReducedData()) return;
  for (const screen of Object.values(screens)) {
    await whenIdle();
    await screen.preload();
  }
};
