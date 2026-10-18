import { render } from "preact";
import { LocationProvider } from "preact-iso";

// The kit stylesheet declares its canonical cascade-layer order before its rules;
// load it before app token overrides, self-hosted fonts and app styles.
import "@roedu/ui/styles.css";
import "./styles/app.css";

import App from "./App";
import { installReleaseRecovery } from "./releaseRecovery.mjs";
import { PORTED_LINK_SCOPE } from "./routes";

installReleaseRecovery();

// UI 1.0 has no ThemeProvider: the explicit .roedu-root wrapper carries the
// tokens (theme.css). Links outside the app scope remain document navigations
// so native account/legal/API endpoints keep their server owner.
render(
  <div className="roedu-root">
    <LocationProvider scope={PORTED_LINK_SCOPE}>
      <App />
    </LocationProvider>
  </div>,
  document.getElementById("root")!,
);
