import { useState } from "react";

interface DiffInputProps {
  onSubmit: (diff: string, prUrl: string) => void;
  isLoading: boolean;
}

export function DiffInput({ onSubmit, isLoading }: DiffInputProps) {
  const [mode, setMode] = useState<"diff" | "url">("diff");
  const [diff, setDiff] = useState("");
  const [prUrl, setPrUrl] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (mode === "diff" && diff.trim()) {
      onSubmit(diff, "");
    } else if (mode === "url" && prUrl.trim()) {
      onSubmit("", prUrl);
    }
  };

  const canSubmit =
    !isLoading && ((mode === "diff" && diff.trim()) || (mode === "url" && prUrl.trim()));

  return (
    <form onSubmit={handleSubmit} className="diff-input">
      <div className="tab-bar">
        <button
          type="button"
          className={`tab ${mode === "diff" ? "active" : ""}`}
          onClick={() => setMode("diff")}
        >
          Paste Diff
        </button>
        <button
          type="button"
          className={`tab ${mode === "url" ? "active" : ""}`}
          onClick={() => setMode("url")}
        >
          PR URL
        </button>
      </div>

      {mode === "diff" ? (
        <textarea
          value={diff}
          onChange={(e) => setDiff(e.target.value)}
          placeholder={`Paste your git diff here...\n\nExample:\ndiff --git a/file.py b/file.py\n--- a/file.py\n+++ b/file.py\n@@ -1,3 +1,4 @@\n def hello():\n-    print("hello")\n+    print("hello world")\n+    return True`}
          rows={16}
          spellCheck={false}
        />
      ) : (
        <input
          type="url"
          value={prUrl}
          onChange={(e) => setPrUrl(e.target.value)}
          placeholder="https://github.com/owner/repo/pull/123"
        />
      )}

      <button type="submit" className="btn-primary" disabled={!canSubmit}>
        {isLoading ? "Reviewing..." : "Review"}
      </button>
    </form>
  );
}
