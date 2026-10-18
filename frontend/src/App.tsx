// App.tsx — routing shell for the word-game arcade. Every screen is a real URL
// (shareable/bookmarkable; the Go server serves the shell on deep links) and
// screen changes animate through the kit Presence. Game logic lives per screen;
// the shell owns only toasts + transitions.
//
// The full M3 route set is routed here. The exiting screen is retained by Presence until its
// animation settles; its `useIsPresent()` turns false so held replies and
// actions stay inert. Screens are chosen per path, not through a live Router,
// so a retained frame keeps showing the screen it left with.

import type { ComponentChildren, VNode } from "preact";
import { useCallback, useEffect, useRef, useState } from "preact/hooks";
import { ErrorBoundary, useLocation } from "preact-iso";
import { ToastStack, type ToastData, type ToastKind } from "@roedu/ui";
import { Presence, useIsPresent } from "@roedu/ui/motion";
import { RouteErrorBoundary } from "./components/RouteErrorBoundary";
import { OptionalChromeBoundary } from "./components/OptionalChromeBoundary";
import { lazyScreen } from "./lazyScreen";
import { pathOf, portedPath } from "./routes";
import { ScreenURL } from "./screenLocation";

// Load only the selected screen. Deep links do not need the Home view;
// AccountBar remains immediately mounted and charged on every route.
const AccountBar = lazyScreen(() => import("./components/AccountBar"));
const Home = lazyScreen(() => import("./screens/Home"));
const Intrusul = lazyScreen(() => import("./screens/Intrusul"));
const Perechi = lazyScreen(() => import("./screens/Perechi"));
const Conexiuni = lazyScreen(() => import("./screens/Conexiuni"));
const Alchimie = lazyScreen(() => import("./screens/Alchimie"));
const CaldRece = lazyScreen(() => import("./screens/CaldRece"));
const Lant = lazyScreen(() => import("./screens/Lant"));
const Ranking = lazyScreen(() => import("./screens/Ranking"));

export type { ToastKind };

function ScreenFrame({ children, url }: { children: ComponentChildren; url: string }) {
  const present = useIsPresent();
  return <ScreenURL.Provider value={url}><div className="screen" inert={!present}>{children}</div></ScreenURL.Provider>;
}

function FallbackRoute({ url }: { url: string }) {
  const { route } = useLocation();
  useEffect(() => {
    const target = new URL(url, "http://local.invalid");
    // A single trailing slash on a known screen retains its query. Unknown
    // document paths return Home, matching the original wildcard destination.
    const canonical = target.pathname.endsWith("/") ? target.pathname.slice(0, -1) : "";
    route(portedPath(canonical) ? canonical + target.search : "/", true);
  }, [route, url]);
  return (
    <div className="screen-pad fill">
      <section className="container card col route-error-content" role="status" aria-live="polite">
        <p>Se încarcă…</p>
        <div className="row wrap"><a href="/">Înapoi la jocuri</a></div>
      </section>
    </div>
  );
}

export default function App() {
  const { url, route } = useLocation();
  // LocationProvider normalizes trailing slashes in its `path`. Match the raw
  // document path so the explicit fallback can canonicalize a known slash and
  // preserve its query before selecting a game.
  const path = pathOf(url);
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

  // The ported set is matched on the exact document path. Keep this switch literal: the route-budget
  // evaluator binds every case to its screen module.
  let screen: VNode;
  switch (portedPath(path) ? path : "fallback") {
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
    case "/alchimie":
      screen = <Alchimie url={url} onExit={goHome} onToast={pushToast} />;
      break;
    case "/cald-rece":
      screen = <CaldRece onExit={goHome} onToast={pushToast} />;
      break;
    case "/lant":
      screen = <Lant onExit={goHome} onToast={pushToast} />;
      break;
    case "/clasament":
      screen = <Ranking />;
      break;
    default:
      screen = <FallbackRoute url={url} />;
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
            <ScreenFrame key={path} url={url}>
              <ErrorBoundary>{screen}</ErrorBoundary>
            </ScreenFrame>
          </Presence>
        </div>
      </div>
    </RouteErrorBoundary>
  );
}
