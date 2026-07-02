import { lazy } from "react";
import type { ComponentType } from "react";
import { isStaleChunkError, reloadForStaleChunk } from "./staleChunk";

// Rendered for the instant before reloadForStaleChunk() navigates to the fresh
// deploy, instead of crashing into the error boundary.
const StaleChunkFallback: ComponentType = () => null;

// Resolves a screen's lazy module, healing the stale-chunk failure modes that
// the global `vite:preloadError` handler misses. On WebKit (Safari) and some
// Android Chrome builds, a dynamic import for a chunk that no longer exists
// after a deploy neither fires `vite:preloadError` nor rejects with a known
// message — it resolves to `undefined`, so `module.ScreenName` throws a
// TypeError ("undefined is not an object (evaluating 't.PlayerInfoScreen')")
// that lands in the error boundary and Sentry. Here we detect the undefined
// module / missing export and the known rejection messages, and reload to the
// latest deploy instead. reloadForStaleChunk() debounces via sessionStorage,
// so this cannot loop.
export const resolveScreenModule = async <
  K extends string,
  M extends Record<K, ComponentType>,
>(
  factory: () => Promise<M>,
  name: K
): Promise<{ default: ComponentType }> => {
  try {
    const module: M | undefined = await factory();
    const component = module?.[name];
    if (!component) {
      reloadForStaleChunk();
      return { default: StaleChunkFallback };
    }
    return { default: component };
  } catch (error) {
    if (isStaleChunkError(error)) {
      reloadForStaleChunk();
      return { default: StaleChunkFallback };
    }
    throw error;
  }
};

export const lazyScreen = <K extends string, M extends Record<K, ComponentType>>(
  factory: () => Promise<M>,
  name: K
) => lazy(() => resolveScreenModule(factory, name));
