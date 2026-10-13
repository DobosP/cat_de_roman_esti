import { render } from "preact";
import { LocationProvider } from "preact-iso";

// Order matters: the kit's cascade-layer order first (layers.css, REQ-9), then the
// design-system base, the app's token overrides, self-hosted fonts and the app layer.
import "./styles/layers.css";
import "@roedu/ui/styles.css";
import "./styles/theme.css";
import "./styles/fonts.css";
import "./styles/arcade.css";

import App from "./App";
import { installReleaseRecovery } from "./releaseRecovery.mjs";
import { PORTED_LINK_SCOPE } from "./routes";

installReleaseRecovery();

// UI 1.0 has no ThemeProvider: the explicit .roedu-root wrapper carries the
// tokens (theme.css). Links outside the ported scope are left to the browser so
// the server's frozen legacy bundle answers them (ADR-0197).
render(
  <div className="roedu-root">
    <LocationProvider scope={PORTED_LINK_SCOPE}>
      <App />
    </LocationProvider>
  </div>,
  document.getElementById("root")!,
);
