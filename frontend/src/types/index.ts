/**
 * Type definitions for the PR Reviewer Agent API.
 */

export interface ReviewIssue {
  file: string;
  line: number | null;
  severity: "critical" | "warning" | "info";
  title: string;
  description: string;
  suggestion: string;
}

export interface CategoryReview {
  category: string;
  issues: ReviewIssue[];
  summary: string;
}

export interface ReviewResult {
  categories: CategoryReview[];
  suggested_patch: string;
  overall_summary: string;
  test_suggestions: string;
}

export interface ReviewRequest {
  diff: string;
  pr_url: string;
}

export interface StreamStatus {
  node: string;
  message: string;
}
