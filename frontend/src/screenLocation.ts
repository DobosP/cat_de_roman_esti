import { createContext } from "preact";

// A Presence-retained frame keeps the URL that selected its screen. The outer
// LocationProvider still owns navigation; this context never owns a second router.
export const ScreenURL = createContext<string | null>(null);
