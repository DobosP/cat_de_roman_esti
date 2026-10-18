// lazyScreen — code-split screens for the preact-iso shell.
//
// preact-iso's own `lazy` keeps a rejected chunk suspended forever (its
// promise never resolves the boundary), which would hide a failed deploy chunk
// instead of reaching RouteErrorBoundary. This loader caches the module exactly
// once, resolves the suspension in every outcome and then re-throws the real
// error on the next render, so the existing recovery screen and the
// vite:preloadError release recovery keep their original behaviour.
import { h, type Attributes, type ComponentType, type VNode } from "preact";
import { useState } from "preact/hooks";

export interface LazyScreen<P> {
  (props: P): VNode<P & Attributes>;
  preload(): Promise<void>;
}

export function lazyScreen<P>(load: () => Promise<{ default: ComponentType<P> }>): LazyScreen<P> {
  let pending: Promise<void> | undefined;
  let loaded: ComponentType<P> | undefined;
  let failure: unknown;
  let failed = false;
  const start = () => {
    pending ??= load().then(
      (module) => { loaded = module.default; },
      (error: unknown) => { failure = error instanceof Error ? error : new Error(String(error)); failed = true; },
    );
    return pending;
  };
  function LazyComponent(props: P): VNode<P & Attributes> {
    const [, retry] = useState(0);
    // A suspended instance has not committed an effect. Register its one-shot
    // wakeup during initialization without mutating a hook value in render.
    useState(() => {
      if (!loaded && !failed) {
        void start().then(() => retry((revision) => revision + 1));
      }
      return null;
    });
    if (loaded) return h(loaded, props as P & Attributes);
    if (failed) throw failure;
    throw start();
  }
  return Object.assign(LazyComponent, { preload: start });
}
