import {
  Component,
  lazy,
  Suspense,
  type ErrorInfo,
  type ReactNode,
} from "react";
import { Link, Route, Routes } from "react-router-dom";

import { FeedPage } from "./components/FeedPage";

const StoryPage = lazy(() =>
  import("./components/StoryPage").then((module) => ({
    default: module.StoryPage,
  })),
);

class ErrorBoundary extends Component<
  { children: ReactNode },
  { failed: boolean }
> {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Ripple render error", error, info);
  }

  render() {
    if (this.state.failed) {
      return (
        <main className="state-page">
          <p className="eyebrow">Interface error</p>
          <h1>The evidence view could not be rendered.</h1>
          <button onClick={() => window.location.reload()}>
            Reload Ripple
          </button>
        </main>
      );
    }
    return this.props.children;
  }
}

function Shell({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <header className="site-header">
        <Link className="wordmark" to="/" aria-label="Ripple home">
          <span aria-hidden="true">◌</span> RIPPLE
        </Link>
        <p>Evidence-first causal pathways</p>
        <span className="fixture-key">
          <i /> fixture dataset
        </span>
      </header>
      {children}
    </div>
  );
}

export function App() {
  return (
    <ErrorBoundary>
      <Shell>
        <Routes>
          <Route path="/" element={<FeedPage />} />
          <Route
            path="/story/:storyId"
            element={
              <Suspense
                fallback={
                  <main className="story-loading">
                    <p className="eyebrow">LOADING EXPLORER</p>
                    <div className="pulse-ring" />
                  </main>
                }
              >
                <StoryPage />
              </Suspense>
            }
          />
          <Route
            path="*"
            element={
              <main className="state-page">
                <h1>Path not found</h1>
                <Link to="/">Return to the feed</Link>
              </main>
            }
          />
        </Routes>
      </Shell>
    </ErrorBoundary>
  );
}
