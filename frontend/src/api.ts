const API_BASE = '/api';

export interface Device {
  id: string;
  name: string;
  room: string;
  type: string;
  online: boolean;
  attributes: Record<string, any>;
}

export interface HomeSummary {
  home_name: string;
  total_devices: number;
  active_devices: number;
  rooms: Record<string, DeviceSummary[]>;
  sensor_alerts: string[];
}

export interface DeviceSummary {
  id: string;
  name: string;
  type: string;
  status: string;
  online: boolean;
}

export interface TimelineEntry {
  id: number;
  timestamp: string;
  device_id: string;
  device_name: string;
  action: string;
  before_state: Record<string, any>;
  after_state: Record<string, any>;
  explanation: string;
  risk_level: string;
  executed: boolean;
}

export interface ChatResponse {
  reply: string;
  plan: any | null;
  timeline_entries: any[];
  needs_confirmation: boolean;
}

export interface HealthResponse {
  status: string;
  version: string;
  uptime_seconds: number;
  device_count: number;
}

export interface AutomationRule {
  id: string;
  name: string;
  enabled: boolean;
  conditions: { field: string; operator: string; value: any }[];
  actions: { device_id: string; action: string; parameters?: Record<string, any> }[];
  reason: string;
  created_at: string;
}

async function fetchJson<T>(path: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!resp.ok) throw new Error(`API error: ${resp.status}`);
  return resp.json();
}

export const api = {
  health: () => fetchJson<HealthResponse>('/health'),
  homeSummary: () => fetchJson<HomeSummary>('/home/summary'),
  devices: () => fetchJson<Device[]>('/devices'),
  device: (id: string) => fetchJson<Device>(`/devices/${id}`),
  timeline: (limit = 50) => fetchJson<TimelineEntry[]>(`/timeline?limit=${limit}`),
  incidents: () => fetchJson<any[]>('/incidents'),
  resolveIncident: (id: number) =>
    fetchJson<any>(`/incidents/${id}/resolve`, { method: 'POST' }),
  chat: (message: string, dryRun = true, confirm = false) =>
    fetchJson<ChatResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify({ message, dry_run: dryRun, confirm }),
    }),
  deviceAction: (deviceId: string, action: string, params?: Record<string, any>) =>
    fetchJson<Device>(`/devices/${deviceId}/action?action=${action}`, {
      method: 'POST',
      body: JSON.stringify(params || {}),
    }),
  dailyReport: (date?: string) =>
    fetchJson<any>(`/reports/daily${date ? `?date=${date}` : ''}`),
  // Home Assistant
  haStatus: () => fetchJson<any>('/ha/status'),
  haSync: () => fetchJson<any>('/ha/sync', { method: 'POST' }),
  // Automations
  automations: () => fetchJson<AutomationRule[]>('/automations'),
  createAutomation: (rule: Partial<AutomationRule>) =>
    fetchJson<any>('/automations', {
      method: 'POST',
      body: JSON.stringify(rule),
    }),
  toggleAutomation: (id: string) =>
    fetchJson<any>(`/automations/${id}/toggle`, { method: 'PUT' }),
  deleteAutomation: (id: string) =>
    fetchJson<any>(`/automations/${id}`, { method: 'DELETE' }),
  checkAutomations: () =>
    fetchJson<any>('/automations/check', { method: 'POST' }),
  checkIncidents: () =>
    fetchJson<any>('/incidents/check', { method: 'POST' }),
};
