import { lazy } from "react";
import type { ComponentType, FC } from "react";
import { isStaleChunkError, reloadForStaleChunk } from "./staleChunk";

// Rendered for the instant before reloadForStaleChunk() navigates to the fresh
// deploy, instead of crashing into the error boundary.
export const StaleChunkFallback: FC = () => null;

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
  load: () => Promise<T | undefined>,
  fallback: T
): Promise<{ default: T }> => {
  try {
    const component = await load();
    if (!component) {
      reloadForStaleChunk();
      return { default: fallback };
    }
    return { default: component };
  } catch (error) {
    if (isStaleChunkError(error)) {
      reloadForStaleChunk();
      return { default: fallback };
    }
    throw error;
  }
};

export const resolveScreenModule = <K extends string, M extends Record<K, ComponentType>>(
  factory: () => Promise<M>,
  name: K
) => healLazyImport<ComponentType>(async () => (await factory())?.[name], StaleChunkFallback);

export const lazyScreen = <K extends string, M extends Record<K, ComponentType>>(
  factory: () => Promise<M>,
  name: K
) => lazy(() => resolveScreenModule(factory, name));
