import type { ReviewResult } from "../types";
import { ReviewCategory } from "./ReviewCategory";

interface ReviewResultsProps {
  result: ReviewResult;
}

export function ReviewResults({ result }: ReviewResultsProps) {
  const totalIssues = result.categories.reduce(
    (sum, cat) => sum + cat.issues.length,
    0
  );
  const criticalCount = result.categories.reduce(
    (sum, cat) => sum + cat.issues.filter((i) => i.severity === "critical").length,
    0
  );

  return (
    <div className="review-results">
      {/* Summary section */}
      {result.overall_summary && (
        <div className="overall-summary">
          <h2>Review Summary</h2>
          <div className="summary-stats">
            <span className="stat">{totalIssues} issues found</span>
            {criticalCount > 0 && (
              <span className="stat critical">{criticalCount} critical</span>
            )}
          </div>
          <p>{result.overall_summary}</p>
        </div>
      )}

      {/* Category reviews */}
      <div className="categories">
        {result.categories.map((cat, i) => (
          <ReviewCategory key={i} review={cat} />
        ))}
      </div>

      {/* Suggested patch */}
      {result.suggested_patch && (
        <div className="suggested-patch">
          <h2>Suggested Patch</h2>
          <pre>
            <code>{result.suggested_patch}</code>
          </pre>
        </div>
      )}

      {/* Test suggestions */}
      {result.test_suggestions && (
        <div className="test-suggestions">
          <h2>Test Suggestions</h2>
          <p>{result.test_suggestions}</p>
        </div>
      )}
    </div>
  );
}
