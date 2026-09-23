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

  render() {
    if (!this.state.failed) return this.props.children;
    return (
      <div className="screen screen-pad">
        <section className="container card col" role="alert" style={{ padding: 24, gap: 16 }}>
          <h1 tabIndex={-1} ref={(heading) => heading?.focus()}>Nu am putut încărca jocul.</h1>
          <p>Reîncarcă pagina sau alege alt joc.</p>
          <div className="row wrap">
            <Button type="button" onClick={() => window.location.reload()}>Reîncarcă pagina</Button>
            <Link to="/">Înapoi la jocuri</Link>
          </div>
        </section>
      </div>
    );
  }
}
