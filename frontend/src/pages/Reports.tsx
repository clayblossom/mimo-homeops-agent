import { useState } from 'react';
import { api } from '../api';

export function Reports() {
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const loadReport = async (date?: string) => {
    setLoading(true);
    try {
      const data = await api.dailyReport(date);
      setReport(data);
    } catch (err) {
      console.error('Report failed:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">📊 Energy & Comfort Report</h2>
            <p className="text-sm text-gray-400">Daily analysis of your smart home</p>
          </div>
          <button
            onClick={() => loadReport()}
            disabled={loading}
            className="btn-primary"
          >
            {loading ? '⏳ Generating...' : '📊 Generate Report'}
          </button>
        </div>
      </div>

      {!report && !loading && (
        <div className="card text-center py-12">
          <p className="text-4xl mb-3">📊</p>
          <p className="text-gray-400">Click "Generate Report" to see your home analysis</p>
        </div>
      )}

      {report && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <SummaryCard
              icon="🏠"
              label="Devices"
              value={`${report.summary.active_devices}/${report.summary.total_devices}`}
              sub="active"
            />
            <SummaryCard
              icon="🌡️"
              label="Comfort"
              value={`${report.summary.comfort_score}`}
              sub="/100"
              color={report.summary.comfort_score >= 80 ? 'text-green-400' : report.summary.comfort_score >= 60 ? 'text-yellow-400' : 'text-red-400'}
            />
            <SummaryCard
              icon="⚡"
              label="Actions"
              value={`${report.summary.actions_today}`}
              sub="today"
            />
            <SummaryCard
              icon="🚨"
              label="Incidents"
              value={`${report.summary.incidents}`}
              sub="total"
              color={report.summary.incidents === 0 ? 'text-green-400' : 'text-yellow-400'}
            />
          </div>

          {/* Energy Waste Alerts */}
          {report.energy_waste_alerts.length > 0 && (
            <div className="card">
              <h3 className="font-semibold text-yellow-400 mb-3">⚠️ Energy Waste Alerts</h3>
              <div className="space-y-2">
                {report.energy_waste_alerts.map((alert: string, i: number) => (
                  <div key={i} className="bg-yellow-900/20 border border-yellow-700/30 rounded-lg px-3 py-2 text-sm text-yellow-300">
                    {alert}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Comfort Details */}
          {report.comfort_details.length > 0 && (
            <div className="card">
              <h3 className="font-semibold mb-3">🌡️ Comfort Details</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {report.comfort_details.map((c: any, i: number) => (
                  <div key={i} className="bg-xiaomi-darker/50 rounded-lg p-3 flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-300">{c.room} — {c.sensor}</p>
                      <p className="text-lg font-mono">{c.value}{c.unit}</p>
                    </div>
                    <span className={`badge ${
                      c.status === 'ideal' ? 'badge-green' :
                      c.status === 'acceptable' ? 'badge-yellow' : 'badge-red'
                    }`}>
                      {c.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Active Devices */}
          {report.active_devices.length > 0 && (
            <div className="card">
              <h3 className="font-semibold mb-3">🔌 Active Devices ({report.active_devices.length})</h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {report.active_devices.map((d: any, i: number) => (
                  <div key={i} className="bg-xiaomi-darker/50 rounded-lg px-3 py-2 text-sm">
                    <p className="text-gray-300">{d.name}</p>
                    <p className="text-xs text-gray-500">{d.room} • {d.type}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Savings Suggestions */}
          {report.savings_suggestions.length > 0 && (
            <div className="card">
              <h3 className="font-semibold text-green-400 mb-3">💡 Savings Suggestions</h3>
              <div className="space-y-2">
                {report.savings_suggestions.map((sug: string, i: number) => (
                  <div key={i} className="bg-green-900/20 border border-green-700/30 rounded-lg px-3 py-2 text-sm text-green-300">
                    {sug}
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function SummaryCard({ icon, label, value, sub, color = 'text-white' }: {
  icon: string; label: string; value: string; sub: string; color?: string;
}) {
  return (
    <div className="card text-center">
      <p className="text-2xl mb-1">{icon}</p>
      <p className="text-xs text-gray-500">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>{value}<span className="text-sm text-gray-500">{sub}</span></p>
    </div>
  );
}
