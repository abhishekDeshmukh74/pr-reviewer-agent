import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  PromptInput,
  PromptInputBody,
  PromptInputFooter,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputTools,
  type PromptInputMessage,
} from "@/components/ai-elements/prompt-input";
import { InputGroupInput } from "@/components/ui/input-group";

interface DiffInputProps {
  onSubmit: (diff: string, prUrl: string) => void;
  isLoading: boolean;
}

export function DiffInput({ onSubmit, isLoading }: DiffInputProps) {
  const [mode, setMode] = useState<"diff" | "url">("diff");

  const handleSubmit = (message: PromptInputMessage) => {
    const text = message.text.trim();
    if (!text) return;
    if (mode === "diff") onSubmit(text, "");
    else onSubmit("", text);
  };

  const status = isLoading ? ("streaming" as const) : undefined;

  return (
    <Tabs value={mode} onValueChange={(v) => setMode(v as "diff" | "url")}>
      <TabsList className="mb-3">
        <TabsTrigger value="diff">Paste Diff</TabsTrigger>
        <TabsTrigger value="url">PR URL</TabsTrigger>
      </TabsList>

      <TabsContent value="diff">
        <PromptInput onSubmit={handleSubmit}>
          <PromptInputBody>
            <PromptInputTextarea
              placeholder={`Paste your git diff here...\n\nExample:\ndiff --git a/file.py b/file.py`}
              className="min-h-48 font-mono text-xs"
              spellCheck={false}
            />
          </PromptInputBody>
          <PromptInputFooter>
            <PromptInputTools />
            <PromptInputSubmit status={status} disabled={isLoading} />
          </PromptInputFooter>
        </PromptInput>
      </TabsContent>

      <TabsContent value="url">
        <PromptInput onSubmit={handleSubmit}>
          <PromptInputBody>
            <InputGroupInput
              name="message"
              type="url"
              placeholder="https://github.com/owner/repo/pull/123"
              className="py-3"
            />
          </PromptInputBody>
          <PromptInputFooter>
            <PromptInputTools />
            <PromptInputSubmit status={status} disabled={isLoading} />
          </PromptInputFooter>
        </PromptInput>
      </TabsContent>
    </Tabs>
  );
}
