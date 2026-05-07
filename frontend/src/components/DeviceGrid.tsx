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

  const loadDevices = () => {
    api.devices().then(setDevices).catch(console.error);
  };

  useEffect(() => {
    loadDevices();
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
          <DeviceCard key={device.id} device={device} onUpdate={loadDevices} />
        ))}
      </div>
    </div>
  );
}

function DeviceCard({ device, onUpdate }: { device: Device; onUpdate: () => void }) {
  const isOn = device.attributes.on ?? device.attributes.cleaning ?? false;
  const attrs = device.attributes;
  const [loading, setLoading] = useState(false);

  const doAction = async (action: string, params?: Record<string, any>) => {
    setLoading(true);
    try {
      await api.deviceAction(device.id, action, params);
      onUpdate();
    } catch (err) {
      console.error('Action failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleOnOff = () => {
    const domain = device.type;
    if (device.type === 'vacuum') {
      doAction(isOn ? 'vacuum.stop' : 'vacuum.start');
    } else {
      doAction(`${domain}.${isOn ? 'off' : 'on'}`);
    }
  };

  return (
    <div className={`card transition-all ${isOn ? 'border-xiaomi-orange/50 shadow-xiaomi-orange/10' : ''} ${loading ? 'opacity-60' : ''}`}>
      {/* Header */}
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

      {/* Status Info */}
      <div className="space-y-1 text-xs mb-3">
        {device.type === 'sensor' ? (
          Object.entries(attrs).map(([k, v]) => (
            <div key={k} className="flex justify-between">
              <span className="text-gray-500">{k}</span>
              <span className={`font-mono ${
                typeof v === 'boolean' && v ? 'text-red-400' :
                typeof v === 'boolean' && !v ? 'text-green-400' :
                'text-blue-400'
              }`}>{String(v)}</span>
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
              <div className="flex justify-between items-center">
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

      {/* Interactive Controls */}
      {device.type !== 'sensor' && device.online && (
        <div className="border-t border-gray-700/50 pt-3 space-y-2">
          {/* On/Off Toggle */}
          <button
            onClick={toggleOnOff}
            disabled={loading}
            className={`w-full py-1.5 rounded-lg text-xs font-medium transition-colors ${
              isOn
                ? 'bg-green-900/40 text-green-400 border border-green-700/50 hover:bg-green-900/60'
                : 'bg-gray-700 text-gray-400 border border-gray-600 hover:bg-gray-600'
            }`}
          >
            {loading ? '...' : isOn ? '⏻ Turn OFF' : '⏻ Turn ON'}
          </button>

          {/* Brightness slider for lights */}
          {device.type === 'light' && attrs.brightness !== undefined && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500 w-8">🔆</span>
              <input
                type="range"
                min={0}
                max={100}
                value={attrs.brightness}
                onChange={e => doAction('light.brightness', { brightness: Number(e.target.value) })}
                className="flex-1 h-1 accent-xiaomi-orange"
              />
              <span className="text-xs text-gray-400 w-8 text-right">{attrs.brightness}%</span>
            </div>
          )}

          {/* Temperature slider for AC */}
          {device.type === 'ac' && attrs.temperature !== undefined && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500 w-8">🌡️</span>
              <input
                type="range"
                min={16}
                max={30}
                value={attrs.temperature}
                onChange={e => doAction('ac.set_temp', { temperature: Number(e.target.value) })}
                className="flex-1 h-1 accent-blue-400"
              />
              <span className="text-xs text-gray-400 w-10 text-right">{attrs.temperature}°C</span>
            </div>
          )}

          {/* Curtain position slider */}
          {device.type === 'curtain' && attrs.position !== undefined && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500 w-8">🪟</span>
              <input
                type="range"
                min={0}
                max={100}
                value={attrs.position}
                onChange={e => doAction('curtain.set_position', { position: Number(e.target.value) })}
                className="flex-1 h-1 accent-cyan-400"
              />
              <span className="text-xs text-gray-400 w-10 text-right">{attrs.position}%</span>
            </div>
          )}

          {/* Fan speed buttons */}
          {device.type === 'fan' && attrs.speed !== undefined && (
            <div className="flex items-center gap-1">
              <span className="text-xs text-gray-500 mr-1">💨</span>
              {Array.from({ length: attrs.max_speed || 5 }, (_, i) => i + 1).map(s => (
                <button
                  key={s}
                  onClick={() => doAction('fan.set_speed', { speed: s })}
                  className={`flex-1 py-1 rounded text-xs ${
                    attrs.speed === s
                      ? 'bg-teal-700 text-teal-300'
                      : 'bg-gray-800 text-gray-500 hover:bg-gray-700'
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          )}

          {/* AC mode buttons */}
          {device.type === 'ac' && (
            <div className="flex items-center gap-1">
              {['auto', 'cool', 'heat', 'dry', 'fan'].map(m => (
                <button
                  key={m}
                  onClick={() => doAction('ac.set_mode', { mode: m })}
                  className={`flex-1 py-1 rounded text-xs ${
                    attrs.mode === m
                      ? 'bg-blue-700 text-blue-300'
                      : 'bg-gray-800 text-gray-500 hover:bg-gray-700'
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>
          )}

          {/* Purifier mode buttons */}
          {device.type === 'purifier' && (
            <div className="flex items-center gap-1">
              {['auto', 'sleep', 'turbo', 'manual'].map(m => (
                <button
                  key={m}
                  onClick={() => doAction('purifier.set_mode', { mode: m })}
                  className={`flex-1 py-1 rounded text-xs ${
                    attrs.mode === m
                      ? 'bg-purple-700 text-purple-300'
                      : 'bg-gray-800 text-gray-500 hover:bg-gray-700'
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      <p className="text-xs text-gray-600 mt-2 font-mono">{device.id}</p>
    </div>
  );
}
