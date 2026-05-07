import { TimelineEntry } from '../api';

interface Props {
  entries: TimelineEntry[];
  full?: boolean;
}

const riskIcons: Record<string, string> = {
  low: '🟢',
  medium: '🟡',
  high: '🔴',
  critical: '⛔',
};

function formatTime(ts: string): string {
  try {
    const d = new Date(ts);
    return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  } catch {
    return ts;
  }
}

function formatState(state: Record<string, any>): string {
  return Object.entries(state)
    .map(([k, v]) => `${k}=${v}`)
    .join(', ');
}

export function Timeline({ entries, full }: Props) {
  return (
    <div className={full ? 'card' : ''}>
      {full && <h2 className="text-lg font-semibold mb-4">📋 Action Timeline</h2>}

      {entries.length === 0 ? (
        <p className="text-gray-500 text-sm text-center py-4">No actions yet. Try controlling some devices!</p>
      ) : (
        <div className="space-y-2">
          {entries.map(entry => (
            <div
              key={entry.id}
              className="bg-xiaomi-darker/50 rounded-lg p-3 border-l-2 border-gray-700"
            >
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <span>{riskIcons[entry.risk_level] || '⚪'}</span>
                  <span className="text-sm font-medium text-white">{entry.device_name}</span>
                  <span className="text-xs font-mono text-gray-400">→ {entry.action}</span>
                </div>
                <span className="text-xs text-gray-500">{formatTime(entry.timestamp)}</span>
              </div>

              {entry.explanation && (
                <p className="text-xs text-gray-400 mb-1">{entry.explanation}</p>
              )}

              {full && (
                <div className="flex gap-4 text-xs text-gray-500 mt-1">
                  <span>
                    Before: <span className="text-gray-400">{formatState(entry.before_state)}</span>
                  </span>
                  <span>
                    After: <span className="text-green-400">{formatState(entry.after_state)}</span>
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
