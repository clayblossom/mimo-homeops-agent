import { useState, useEffect } from 'react';
import { api, AutomationRule } from '../api';

export function Automations() {
  const [rules, setRules] = useState<AutomationRule[]>([]);
  const [loading, setLoading] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [checkResult, setCheckResult] = useState<any>(null);

  const loadRules = async () => {
    try {
      const data = await api.automations();
      setRules(data);
    } catch (err) {
      console.error('Failed to load automations:', err);
    }
  };

  useEffect(() => {
    loadRules();
  }, []);

  const handleToggle = async (id: string) => {
    await api.toggleAutomation(id);
    loadRules();
  };

  const handleDelete = async (id: string) => {
    if (confirm('Delete this automation?')) {
      await api.deleteAutomation(id);
      loadRules();
    }
  };

  const handleCheck = async () => {
    setLoading(true);
    try {
      const result = await api.checkAutomations();
      setCheckResult(result);
    } catch (err) {
      console.error('Check failed:', err);
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
            <h2 className="text-lg font-semibold">⚡ Automation Rules</h2>
            <p className="text-sm text-gray-400">Create IF-THEN rules for your smart home</p>
          </div>
          <div className="flex gap-2">
            <button onClick={handleCheck} disabled={loading} className="btn-secondary text-sm">
              {loading ? '⏳ Checking...' : '▶️ Run Check'}
            </button>
            <button onClick={() => setShowCreate(!showCreate)} className="btn-primary text-sm">
              {showCreate ? '✕ Cancel' : '+ Create Rule'}
            </button>
          </div>
        </div>
      </div>

      {/* Check Result */}
      {checkResult && (
        <div className="card bg-blue-900/20 border-blue-700/30">
          <p className="text-sm text-blue-300">
            ✅ Checked {checkResult.checked} rules, triggered {checkResult.triggered} actions
          </p>
          {checkResult.actions?.length > 0 && (
            <div className="mt-2 space-y-1">
              {checkResult.actions.map((a: any, i: number) => (
                <p key={i} className="text-xs text-blue-400">
                  {a.error ? '❌' : '✅'} {a.rule}: {a.device} → {a.action || a.error}
                </p>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Create Form */}
      {showCreate && <CreateRuleForm onCreated={() => { loadRules(); setShowCreate(false); }} />}

      {/* Rules List */}
      {rules.length === 0 && !showCreate ? (
        <div className="card text-center py-12">
          <p className="text-4xl mb-3">⚡</p>
          <p className="text-gray-400">No automation rules yet</p>
          <p className="text-xs text-gray-500 mt-1">Create rules like "IF bedroom temp {'>'} 27 THEN turn on AC"</p>
        </div>
      ) : (
        <div className="space-y-3">
          {rules.map(rule => (
            <div key={rule.id} className={`card ${!rule.enabled ? 'opacity-60' : ''}`}>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className={`w-2.5 h-2.5 rounded-full ${rule.enabled ? 'bg-green-400' : 'bg-gray-600'}`} />
                  <h3 className="font-medium text-sm">{rule.name}</h3>
                </div>
                <div className="flex gap-1">
                  <button
                    onClick={() => handleToggle(rule.id)}
                    className={`px-2 py-1 rounded text-xs ${
                      rule.enabled ? 'bg-green-900/30 text-green-400' : 'bg-gray-700 text-gray-400'
                    }`}
                  >
                    {rule.enabled ? 'ON' : 'OFF'}
                  </button>
                  <button
                    onClick={() => handleDelete(rule.id)}
                    className="px-2 py-1 rounded text-xs bg-red-900/30 text-red-400 hover:bg-red-900/50"
                  >
                    🗑
                  </button>
                </div>
              </div>

              {/* Conditions */}
              <div className="text-xs space-y-1 mb-2">
                <p className="text-gray-500 font-medium">IF:</p>
                {rule.conditions.map((c, i) => (
                  <p key={i} className="text-blue-400 ml-2 font-mono">
                    {c.field} {c.operator} {String(c.value)}
                  </p>
                ))}
              </div>

              {/* Actions */}
              <div className="text-xs space-y-1">
                <p className="text-gray-500 font-medium">THEN:</p>
                {rule.actions.map((a, i) => (
                  <p key={i} className="text-green-400 ml-2 font-mono">
                    {a.device_id} → {a.action}
                    {a.parameters && ` (${JSON.stringify(a.parameters)})`}
                  </p>
                ))}
              </div>

              {rule.reason && (
                <p className="text-xs text-gray-500 mt-2 italic">💡 {rule.reason}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function CreateRuleForm({ onCreated }: { onCreated: () => void }) {
  const [name, setName] = useState('');
  const [conditionField, setConditionField] = useState('br_sensor_temp.value');
  const [conditionOp, setConditionOp] = useState('>');
  const [conditionValue, setConditionValue] = useState('27');
  const [actionDevice, setActionDevice] = useState('br_ac_1');
  const [actionName, setActionName] = useState('ac.on');
  const [reason, setReason] = useState('');
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    setSaving(true);
    try {
      await api.createAutomation({
        name,
        conditions: [{ field: conditionField, operator: conditionOp, value: conditionValue }],
        actions: [{ device_id: actionDevice, action: actionName }],
        reason,
      });
      onCreated();
    } catch (err) {
      console.error('Create failed:', err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="card border-xiaomi-orange/30">
      <h3 className="font-semibold mb-4">⚡ Create Automation Rule</h3>
      <form onSubmit={handleSubmit} className="space-y-3">
        {/* Name */}
        <div>
          <label className="text-xs text-gray-400 block mb-1">Rule Name</label>
          <input
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="e.g. Bedroom Comfort"
            className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:border-xiaomi-orange focus:outline-none"
          />
        </div>

        {/* Condition */}
        <div className="bg-gray-800/50 rounded-lg p-3">
          <p className="text-xs text-gray-400 mb-2 font-medium">IF condition:</p>
          <div className="flex gap-2">
            <input
              value={conditionField}
              onChange={e => setConditionField(e.target.value)}
              placeholder="sensor_id.attribute"
              className="flex-1 bg-gray-800 border border-gray-600 rounded px-2 py-1.5 text-xs font-mono text-white"
            />
            <select
              value={conditionOp}
              onChange={e => setConditionOp(e.target.value)}
              className="bg-gray-800 border border-gray-600 rounded px-2 py-1.5 text-xs text-white"
            >
              <option value=">">&gt;</option>
              <option value="<">&lt;</option>
              <option value=">=">&gt;=</option>
              <option value="<=">&lt;=</option>
              <option value="==">==</option>
              <option value="!=">!=</option>
            </select>
            <input
              value={conditionValue}
              onChange={e => setConditionValue(e.target.value)}
              placeholder="value"
              className="w-24 bg-gray-800 border border-gray-600 rounded px-2 py-1.5 text-xs font-mono text-white"
            />
          </div>
        </div>

        {/* Action */}
        <div className="bg-gray-800/50 rounded-lg p-3">
          <p className="text-xs text-gray-400 mb-2 font-medium">THEN action:</p>
          <div className="flex gap-2">
            <input
              value={actionDevice}
              onChange={e => setActionDevice(e.target.value)}
              placeholder="device_id"
              className="flex-1 bg-gray-800 border border-gray-600 rounded px-2 py-1.5 text-xs font-mono text-white"
            />
            <input
              value={actionName}
              onChange={e => setActionName(e.target.value)}
              placeholder="domain.command"
              className="flex-1 bg-gray-800 border border-gray-600 rounded px-2 py-1.5 text-xs font-mono text-white"
            />
          </div>
        </div>

        {/* Reason */}
        <div>
          <label className="text-xs text-gray-400 block mb-1">Reason (optional)</label>
          <input
            value={reason}
            onChange={e => setReason(e.target.value)}
            placeholder="Why this rule?"
            className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:border-xiaomi-orange focus:outline-none"
          />
        </div>

        <button type="submit" disabled={saving || !name.trim()} className="btn-primary w-full">
          {saving ? '⏳ Saving...' : '✅ Create Rule'}
        </button>
      </form>
    </div>
  );
}
