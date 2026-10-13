// App.tsx — routing shell for the word-game arcade. Every screen is a real URL
// (shareable/bookmarkable; the Go server serves the shell on deep links) and
// screen changes animate through the kit Presence. Game logic lives per screen;
// the shell owns only toasts + transitions.
//
// Only the M2 ported set is routed here (ADR-0197): the server serves "/",
// "/intrusul", "/perechi" and "/conexiuni" from this bundle and everything
// else from the frozen legacy bundle. The exiting screen is retained by Presence until its
// animation settles; its `useIsPresent()` turns false so held replies and
// actions stay inert. Screens are chosen per path, not through a live Router,
// so a retained frame keeps showing the screen it left with.

import type { ComponentChildren, VNode } from "preact";
import { useCallback, useEffect, useRef, useState } from "preact/hooks";
import { ErrorBoundary, useLocation } from "preact-iso";
import { ToastStack, type ToastData, type ToastKind } from "@roedu/ui";
import { Presence } from "@roedu/ui/motion";
import Home from "./screens/Home";
import { RouteErrorBoundary } from "./components/RouteErrorBoundary";
import { OptionalChromeBoundary } from "./components/OptionalChromeBoundary";
import { lazyScreen } from "./lazyScreen";
import { portedPath } from "./routes";

// Home is the only screen every visitor needs. Each game is deliberately loaded
// on first play so low-end devices do not parse both game engines up front.
const AccountBar = lazyScreen(() => import("./components/AccountBar"));
const Intrusul = lazyScreen(() => import("./screens/Intrusul"));
const Perechi = lazyScreen(() => import("./screens/Perechi"));
const Conexiuni = lazyScreen(() => import("./screens/Conexiuni"));

export type { ToastKind };

// The document this shell was served for. A client-side navigation to any
// other path is a legacy route the server owns, so the browser must load it.
const initialUrl = typeof location === "undefined" ? "/" : location.pathname + location.search;

function ScreenFrame({ children }: { children: ComponentChildren }) {
  return <div className="screen">{children}</div>;
}

function LegacyRoute({ url }: { url: string }) {
  useEffect(() => {
    if (url !== initialUrl) window.location.assign(url);
  }, [url]);
  return (
    <div className="screen-pad fill">
      <section className="container card col route-error-content" role="status" aria-live="polite">
        {url === initialUrl ? <p>Pagina nu este disponibilă în această versiune.</p> : <p>Se încarcă…</p>}
        <div className="row wrap"><a href="/">Înapoi la jocuri</a></div>
      </section>
    </div>
  );
}

export default function App() {
  const { path, url, route } = useLocation();
  const [toasts, setToasts] = useState<ToastData[]>([]);
  const toastIdRef = useRef(0);

  const dismissToast = useCallback((id: number) => {
    setToasts((ts) => ts.filter((t) => t.id !== id));
  }, []);

  const pushToast = useCallback(
    (message: string, kind: ToastKind = "info") => {
      const id = ++toastIdRef.current;
      setToasts((ts) => [...ts, { id, kind, message }]);
      window.setTimeout(() => dismissToast(id), 3600);
    },
    [dismissToast],
  );

  const goHome = useCallback(() => route("/", true), [route]);

  // The ported set is matched on the exact document path; everything else is
  // the server's (legacy) route. Keep this switch literal: the route-budget
  // evaluator binds every case to its screen module.
  let screen: VNode;
  switch (portedPath(path) ? path : "legacy") {
    case "/":
      screen = <Home onToast={pushToast} />;
      break;
    case "/intrusul":
      screen = <Intrusul onExit={goHome} onToast={pushToast} />;
      break;
    case "/perechi":
      screen = <Perechi onExit={goHome} onToast={pushToast} />;
      break;
    case "/conexiuni":
      screen = <Conexiuni onExit={goHome} onToast={pushToast} />;
      break;
    default:
      screen = <LegacyRoute url={url} />;
  }

  return (
    <RouteErrorBoundary pathname={path}>
      <div className="app-shell">
        <OptionalChromeBoundary>
          <ErrorBoundary>
            <AccountBar />
          </ErrorBoundary>
        </OptionalChromeBoundary>
        <div className="app-notices">
          <ToastStack toasts={toasts} onDismiss={dismissToast} dismissLabel="Închide" />
        </div>
        <div className="app-content">
          <Presence mode="wait">
            <ScreenFrame key={path}>
              <ErrorBoundary>{screen}</ErrorBoundary>
            </ScreenFrame>
          </Presence>
        </div>
      </div>
    </RouteErrorBoundary>
  );
}
