import { useState, useCallback, useRef } from "react";
import type {
  CategoryReview,
  ReviewResult,
  StreamStatus,
} from "../types";

interface UseReviewStreamReturn {
  result: ReviewResult | null;
  statuses: StreamStatus[];
  isLoading: boolean;
  error: string | null;
  startReview: (diff: string, prUrl: string) => void;
  reset: () => void;
}

export function useReviewStream(): UseReviewStreamReturn {
  const [result, setResult] = useState<ReviewResult | null>(null);
  const [statuses, setStatuses] = useState<StreamStatus[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setResult(null);
    setStatuses([]);
    setIsLoading(false);
    setError(null);
  }, []);

  const startReview = useCallback((diff: string, prUrl: string) => {
    reset();
    setIsLoading(true);

    const controller = new AbortController();
    abortRef.current = controller;

    const categories: CategoryReview[] = [];
    let patch = "";
    let overallSummary = "";
    let testSuggestions = "";

    fetch("/api/review/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ diff, pr_url: prUrl }),
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) {
          const body = await response.json().catch(() => ({}));
          throw new Error(body.detail || `HTTP ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) throw new Error("No response body");

        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          let currentEvent = "";
          for (const line of lines) {
            if (line.startsWith("event:")) {
              currentEvent = line.slice(6).trim();
            } else if (line.startsWith("data:")) {
              const data = line.slice(5).trim();
              if (!data) continue;

              try {
                const parsed = JSON.parse(data);

                switch (currentEvent) {
                  case "status":
                    setStatuses((prev) => [...prev, parsed as StreamStatus]);
                    break;
                  case "review":
                    categories.push(parsed as CategoryReview);
                    setResult({
                      categories: [...categories],
                      suggested_patch: patch,
                      overall_summary: overallSummary,
                      test_suggestions: testSuggestions,
                    });
                    break;
                  case "patch":
                    patch = parsed.patch || "";
                    setResult({
                      categories: [...categories],
                      suggested_patch: patch,
                      overall_summary: overallSummary,
                      test_suggestions: testSuggestions,
                    });
                    break;
                  case "summary":
                    overallSummary = parsed.overall_summary || "";
                    testSuggestions = parsed.test_suggestions || "";
                    setResult({
                      categories: [...categories],
                      suggested_patch: patch,
                      overall_summary: overallSummary,
                      test_suggestions: testSuggestions,
                    });
                    break;
                  case "error":
                    setError(parsed.detail || "Unknown error");
                    break;
                  case "done":
                    break;
                }
              } catch {
                // skip malformed JSON lines
              }
            }
          }
        }

        setIsLoading(false);
      })
      .catch((err: Error) => {
        if (err.name !== "AbortError") {
          setError(err.message);
          setIsLoading(false);
        }
      });
  }, [reset]);

  return { result, statuses, isLoading, error, startReview, reset };
}
