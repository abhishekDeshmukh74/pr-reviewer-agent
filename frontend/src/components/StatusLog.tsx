import type { StreamStatus } from "../types";

interface StatusLogProps {
  statuses: StreamStatus[];
  isLoading: boolean;
}

export function StatusLog({ statuses, isLoading }: StatusLogProps) {
  if (statuses.length === 0 && !isLoading) return null;

  return (
    <div className="status-log">
      <h3>Agent Progress</h3>
      <div className="status-entries">
        {statuses.map((s, i) => (
          <div key={i} className="status-entry">
            <span className="status-node">{s.node}</span>
            <span className="status-msg">{s.message}</span>
          </div>
        ))}
        {isLoading && (
          <div className="status-entry loading">
            <span className="spinner" />
            <span className="status-msg">Processing...</span>
          </div>
        )}
      </div>
    </div>
  );
}
