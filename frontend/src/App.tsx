import { useState, useEffect } from "react";
import { AlertCircleIcon, XIcon, SunIcon, MoonIcon } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { TooltipProvider } from "@/components/ui/tooltip";
import { DiffInput } from "./components/DiffInput";
import { StatusLog } from "./components/StatusLog";
import { ReviewResults } from "./components/ReviewResults";
import { useReviewStream } from "./hooks/useReviewStream";

export default function App() {
  const { result, statuses, isLoading, error, startReview, reset } =
    useReviewStream();

  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    const root = document.documentElement;
    if (isDark) {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
  }, [isDark]);

  return (
    <TooltipProvider>
      <div className="min-h-screen bg-background text-foreground">
        <div className="mx-auto max-w-3xl px-4 py-10 flex flex-col gap-6">
          {/* Header */}
          <header className="relative text-center space-y-1">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsDark(!isDark)}
              className="absolute right-0 top-0"
              aria-label="Toggle theme"
            >
              {isDark ? (
                <SunIcon className="size-5" />
              ) : (
                <MoonIcon className="size-5" />
              )}
            </Button>
            <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-foreground to-foreground/50 bg-clip-text text-transparent">
              PR Reviewer Agent
            </h1>
            <p className="text-muted-foreground text-sm">
              AI-powered code review — paste a diff or GitHub PR link
            </p>
          </header>

          {/* Input */}
          <DiffInput onSubmit={startReview} isLoading={isLoading} />

          {/* Error */}
          {error && (
            <Alert variant="destructive">
              <AlertCircleIcon className="size-4" />
              <AlertDescription className="flex items-center justify-between gap-2">
                <span>{error}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={reset}
                  className="shrink-0 h-auto py-0.5"
                >
                  <XIcon className="size-3.5" />
                  Dismiss
                </Button>
              </AlertDescription>
            </Alert>
          )}

          {/* Agent progress */}
          <StatusLog statuses={statuses} isLoading={isLoading} />

          {/* Review results */}
          {result && <ReviewResults result={result} />}

          {/* Footer */}
          <footer className="text-center text-xs text-muted-foreground pt-4">
            Built with LangGraph + LangChain + FastAPI + React
          </footer>
        </div>
      </div>
    </TooltipProvider>
  );
}
