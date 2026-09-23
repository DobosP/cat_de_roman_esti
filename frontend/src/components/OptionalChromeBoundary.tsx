import { Component, type ReactNode } from "react";

/**
 * Hide optional shell chrome (the lazy AccountBar) when it fails, so its chunk
 * cannot take down Home and every game with it. With CAT_ACCOUNTS_ENABLED=1 a
 * silent null also hides the consent gate; acceptable while production is
 * anonymous per DEPLOY.md.
 */
export class OptionalChromeBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch(error: unknown) {
    console.error(error);
  }

  render() {
    return this.state.failed ? null : this.props.children;
  }
}
