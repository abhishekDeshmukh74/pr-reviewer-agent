import { DiffInput } from "./components/DiffInput";
import { StatusLog } from "./components/StatusLog";
import { ReviewResults } from "./components/ReviewResults";
import { useReviewStream } from "./hooks/useReviewStream";
import "./index.css";

export default function App() {
  const { result, statuses, isLoading, error, startReview, reset } =
    useReviewStream();

  return (
    <div className="app">
      <header>
        <h1>PR Reviewer Agent</h1>
        <p className="subtitle">
          AI-powered code review — paste a diff or GitHub PR link
        </p>
      </header>

      <main>
        <DiffInput onSubmit={startReview} isLoading={isLoading} />

        {error && (
          <div className="error-banner">
            <strong>Error:</strong> {error}
            <button onClick={reset} className="btn-reset">
              Dismiss
            </button>
          </div>
        )}

        <StatusLog statuses={statuses} isLoading={isLoading} />

        {result && <ReviewResults result={result} />}
      </main>

      <footer>
        <p>
          Built with LangGraph + LangChain + FastAPI + React
        </p>
      </footer>
    </div>
  );
}
