import { BotIcon } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Message,
  MessageContent,
  MessageResponse,
} from "@/components/ai-elements/message";
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
    <div className="space-y-4">
      {/* Overall summary as assistant message */}
      {result.overall_summary && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <BotIcon className="size-4" />
            <span>Review complete</span>
            <Badge variant="secondary">{totalIssues} issue{totalIssues !== 1 ? "s" : ""}</Badge>
            {criticalCount > 0 && (
              <Badge variant="destructive">{criticalCount} critical</Badge>
            )}
          </div>
          <Message from="assistant">
            <MessageContent>
              <MessageResponse>{result.overall_summary}</MessageResponse>
            </MessageContent>
          </Message>
        </div>
      )}

      {/* Category reviews */}
      {result.categories.length > 0 && (
        <div className="space-y-3">
          {result.categories.map((cat, i) => (
            <ReviewCategory key={i} review={cat} />
          ))}
        </div>
      )}

      {/* Suggested patch */}
      {result.suggested_patch && (
        <Message from="assistant">
          <MessageContent>
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
              Suggested Patch
            </p>
            <pre className="text-xs overflow-x-auto font-mono bg-muted/40 p-3 rounded-md border">
              <code>{result.suggested_patch}</code>
            </pre>
          </MessageContent>
        </Message>
      )}

      {/* Test suggestions */}
      {result.test_suggestions && (
        <Message from="assistant">
          <MessageContent>
            <MessageResponse>
              {`**Test Suggestions**\n\n${result.test_suggestions}`}
            </MessageResponse>
          </MessageContent>
        </Message>
      )}
    </div>
  );
}
