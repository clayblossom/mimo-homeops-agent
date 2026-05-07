import { useState, useEffect } from 'react';
import { api, Device } from '../api';

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

export function DeviceGrid() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    api.devices().then(setDevices).catch(console.error);
  }, []);

  const filtered = filter === 'all'
    ? devices
    : devices.filter(d => d.type === filter);

  const types = [...new Set(devices.map(d => d.type))];

  return (
    <div>
      {/* Filters */}
      <div className="flex gap-2 mb-4 flex-wrap">
        <button
          onClick={() => setFilter('all')}
          className={`px-3 py-1.5 rounded-lg text-sm ${filter === 'all' ? 'bg-xiaomi-orange text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}`}
        >
          All ({devices.length})
        </button>
        {types.map(t => (
          <button
            key={t}
            onClick={() => setFilter(t)}
            className={`px-3 py-1.5 rounded-lg text-sm ${filter === t ? 'bg-xiaomi-orange text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}`}
          >
            {typeIcons[t] || '❓'} {t} ({devices.filter(d => d.type === t).length})
          </button>
        ))}
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {filtered.map(device => (
          <DeviceCard key={device.id} device={device} />
        ))}
      </div>
    </div>
  );
}

function DeviceCard({ device }: { device: Device }) {
  const isOn = device.attributes.on ?? device.attributes.cleaning ?? false;
  const attrs = device.attributes;

  return (
    <div className={`card transition-all ${isOn ? 'border-xiaomi-orange/50 shadow-xiaomi-orange/10' : ''}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{typeIcons[device.type] || '❓'}</span>
          <div>
            <p className="font-medium text-sm">{device.name}</p>
            <p className="text-xs text-gray-500">{device.room}</p>
          </div>
        </div>
        <span className={`w-2.5 h-2.5 rounded-full ${device.online ? (isOn ? 'bg-green-400' : 'bg-gray-600') : 'bg-red-500'}`} />
      </div>

      <div className="space-y-1 text-xs">
        {device.type === 'sensor' ? (
          Object.entries(attrs).map(([k, v]) => (
            <div key={k} className="flex justify-between">
              <span className="text-gray-500">{k}</span>
              <span className="text-blue-400 font-mono">{String(v)}</span>
            </div>
          ))
        ) : (
          <>
            <div className="flex justify-between">
              <span className="text-gray-500">Status</span>
              <span className={isOn ? 'text-green-400' : 'text-gray-500'}>
                {isOn ? 'ON' : 'OFF'}
              </span>
            </div>
            {attrs.brightness !== undefined && (
              <div className="flex justify-between">
                <span className="text-gray-500">Brightness</span>
                <span className="text-yellow-400">{attrs.brightness}%</span>
              </div>
            )}
            {attrs.temperature !== undefined && (
              <div className="flex justify-between">
                <span className="text-gray-500">Temp</span>
                <span className="text-blue-400">{attrs.temperature}°C</span>
              </div>
            )}
            {attrs.mode !== undefined && (
              <div className="flex justify-between">
                <span className="text-gray-500">Mode</span>
                <span className="text-purple-400">{attrs.mode}</span>
              </div>
            )}
            {attrs.position !== undefined && (
              <div className="flex justify-between">
                <span className="text-gray-500">Position</span>
                <span className="text-cyan-400">{attrs.position}%</span>
              </div>
            )}
            {attrs.speed !== undefined && (
              <div className="flex justify-between">
                <span className="text-gray-500">Speed</span>
                <span className="text-teal-400">{attrs.speed}/{attrs.max_speed || 5}</span>
              </div>
            )}
          </>
        )}
      </div>

      <p className="text-xs text-gray-600 mt-2 font-mono">{device.id}</p>
    </div>
  );
}
