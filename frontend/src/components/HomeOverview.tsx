import { HomeSummary } from '../api';

interface Props {
  home: HomeSummary;
  onRefresh: () => void;
}

const typeIcons: Record<string, string> = {
  light: '💡',
  ac: '❄️',
  fan: '🌀',
  curtain: '🪟',
  purifier: '🌬️',
  vacuum: '🤖',
  plug: '🔌',
  sensor: '📡',
};

export function HomeOverview({ home, onRefresh }: Props) {
  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold">{home.home_name}</h2>
          <p className="text-sm text-gray-400">
            {home.total_devices} devices • {home.active_devices} active
          </p>
        </div>
        <button onClick={onRefresh} className="btn-secondary text-sm">
          🔄 Refresh
        </button>
      </div>

      {/* Sensor Alerts */}
      {home.sensor_alerts.length > 0 && (
        <div className="mb-4 p-3 bg-yellow-900/30 border border-yellow-700/50 rounded-lg">
          <p className="text-sm font-medium text-yellow-400 mb-1">⚠️ Alerts</p>
          {home.sensor_alerts.map((alert, i) => (
            <p key={i} className="text-xs text-yellow-300">{alert}</p>
          ))}
        </div>
      )}

      {/* Rooms */}
      <div className="space-y-3">
        {Object.entries(home.rooms).map(([room, devices]) => (
          <div key={room} className="bg-xiaomi-darker/50 rounded-lg p-3">
            <h3 className="text-sm font-medium text-gray-300 mb-2">🏠 {room}</h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {devices.map(d => (
                <div
                  key={d.id}
                  className="flex items-center gap-2 text-xs bg-gray-800/50 rounded-lg px-2 py-1.5"
                >
                  <span>{typeIcons[d.type] || '❓'}</span>
                  <div className="min-w-0">
                    <p className="text-gray-300 truncate">{d.name}</p>
                    <p className={`font-mono ${d.status === 'ON' || d.status === 'CLEANING' ? 'text-green-400' : d.status === 'OFF' || d.status === 'IDLE' ? 'text-gray-500' : 'text-blue-400'}`}>
                      {d.status}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
