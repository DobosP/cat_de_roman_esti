import { Component, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { Button } from "@roedu/ui";

type Props = { children: ReactNode; pathname: string };

/** Keep failed lazy content recoverable without retrying or deleting saved play. */
export class RouteErrorBoundary extends Component<Props, { failed: boolean }> {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidUpdate(previous: Props) {
    if (previous.pathname !== this.props.pathname && this.state.failed) {
      this.setState({ failed: false });
    }
  }

  // A stable callback focuses the heading only when the failure screen mounts,
  // not on every re-render of the failed boundary.
  private focusHeading = (heading: HTMLHeadingElement | null) => heading?.focus();

  render() {
    if (!this.state.failed) return this.props.children;
    // On '/' no game failed and a home link cannot leave the screen.
    const home = this.props.pathname === "/";
    return (
      <div className="screen screen-pad">
        <section className="container card col" role="alert" style={{ padding: 24, gap: 16 }}>
          <h1 tabIndex={-1} ref={this.focusHeading}>
            {home ? "Nu am putut încărca pagina." : "Nu am putut încărca jocul."}
          </h1>
          <p>{home ? "Reîncarcă pagina." : "Reîncarcă pagina sau alege alt joc."}</p>
          <div className="row wrap">
            <Button type="button" onClick={() => window.location.reload()}>Reîncarcă pagina</Button>
            {!home && <Link to="/">Înapoi la jocuri</Link>}
          </div>
        </section>
      </div>
    );
  }
}
