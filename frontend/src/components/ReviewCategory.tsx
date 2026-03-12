import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { CategoryReview as CategoryReviewType } from "../types";

interface ReviewCategoryProps {
  review: CategoryReviewType;
}

const severityConfig = {
  critical: { variant: "destructive" as const, label: "Critical" },
  warning: { variant: "outline" as const, label: "Warning", extra: "border-yellow-500/50 text-yellow-500" },
  info: { variant: "secondary" as const, label: "Info" },
};

export function ReviewCategory({ review }: ReviewCategoryProps) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="text-base">{review.category}</CardTitle>
          <span className="text-xs text-muted-foreground shrink-0">
            {review.issues.length} issue{review.issues.length !== 1 ? "s" : ""}
          </span>
        </div>
        {review.summary && (
          <p className="text-sm text-muted-foreground">{review.summary}</p>
        )}
      </CardHeader>

      {review.issues.length > 0 && (
        <CardContent className="space-y-3 pt-0">
          {review.issues.map((issue, i) => {
            const cfg = severityConfig[issue.severity] ?? { variant: "secondary" as const, label: issue.severity };
            return (
              <div
                key={i}
                className="rounded-md border bg-muted/20 p-3 space-y-1.5"
              >
                <div className="flex items-start flex-wrap gap-2">
                  <Badge
                    variant={cfg.variant}
                    className={cn("shrink-0", (cfg as { extra?: string }).extra)}
                  >
                    {cfg.label}
                  </Badge>
                  <span className="font-medium text-sm">{issue.title}</span>
                  {issue.file && (
                    <span className="ml-auto text-xs text-muted-foreground font-mono">
                      {issue.file}{issue.line ? `:${issue.line}` : ""}
                    </span>
                  )}
                </div>
                <p className="text-sm text-muted-foreground">{issue.description}</p>
                {issue.suggestion && (
                  <p className="text-sm">
                    <span className="font-semibold">Suggestion:</span>{" "}
                    {issue.suggestion}
                  </p>
                )}
              </div>
            );
          })}
        </CardContent>
      )}
    </Card>
  );
}
