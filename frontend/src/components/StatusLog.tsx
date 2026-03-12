import { Loader2Icon, CheckIcon } from "lucide-react";
import {
  ChainOfThought,
  ChainOfThoughtContent,
  ChainOfThoughtHeader,
  ChainOfThoughtStep,
} from "@/components/ai-elements/chain-of-thought";
import type { StreamStatus } from "../types";

interface StatusLogProps {
  statuses: StreamStatus[];
  isLoading: boolean;
}

export function StatusLog({ statuses, isLoading }: StatusLogProps) {
  if (statuses.length === 0 && !isLoading) return null;

  return (
    <ChainOfThought defaultOpen>
      <ChainOfThoughtHeader>Agent Progress</ChainOfThoughtHeader>
      <ChainOfThoughtContent>
        {statuses.map((s, i) => {
          const isLast = i === statuses.length - 1;
          const stepStatus = isLast && isLoading ? "active" : "complete";
          return (
            <ChainOfThoughtStep
              key={i}
              icon={stepStatus === "active" ? Loader2Icon : CheckIcon}
              label={s.node}
              description={s.message}
              status={stepStatus}
            />
          );
        })}
        {isLoading && statuses.length === 0 && (
          <ChainOfThoughtStep
            icon={Loader2Icon}
            label="Starting review..."
            status="active"
          />
        )}
      </ChainOfThoughtContent>
    </ChainOfThought>
  );
}
