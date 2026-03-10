import type { CategoryReview as CategoryReviewType } from "../types";

interface ReviewCategoryProps {
  review: CategoryReviewType;
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: "#ef4444",
  warning: "#f59e0b",
  info: "#3b82f6",
};

const SEVERITY_LABELS: Record<string, string> = {
  critical: "CRITICAL",
  warning: "WARNING",
  info: "INFO",
};

export function ReviewCategory({ review }: ReviewCategoryProps) {
  return (
    <div className="review-category">
      <div className="category-header">
        <h3>{review.category}</h3>
        <span className="issue-count">
          {review.issues.length} issue{review.issues.length !== 1 ? "s" : ""}
        </span>
      </div>
      {review.summary && <p className="category-summary">{review.summary}</p>}

      {review.issues.length > 0 && (
        <div className="issues-list">
          {review.issues.map((issue, i) => (
            <div key={i} className="issue-card">
              <div className="issue-header">
                <span
                  className="severity-badge"
                  style={{ backgroundColor: SEVERITY_COLORS[issue.severity] || "#6b7280" }}
                >
                  {SEVERITY_LABELS[issue.severity] || issue.severity}
                </span>
                <span className="issue-title">{issue.title}</span>
                {issue.file && (
                  <span className="issue-file">
                    {issue.file}
                    {issue.line ? `:${issue.line}` : ""}
                  </span>
                )}
              </div>
              <p className="issue-description">{issue.description}</p>
              {issue.suggestion && (
                <div className="issue-suggestion">
                  <strong>Suggestion:</strong> {issue.suggestion}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
