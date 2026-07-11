import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { ThemeProvider } from "@roedu/ui";

// Order matters: design-system base first, then self-hosted fonts, then the app layer.
import "@roedu/ui/styles.css";
import "./styles/fonts.css";
import "./styles/arcade.css";

import App from "./App";
import { catTheme } from "./theme";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ThemeProvider theme={catTheme}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ThemeProvider>
  </StrictMode>,
);
