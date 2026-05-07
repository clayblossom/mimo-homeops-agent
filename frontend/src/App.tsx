import { useState, useEffect } from 'react';
import { api, HomeSummary, TimelineEntry, ChatResponse } from './api';
import { Header } from './components/Header';
import { HomeOverview } from './components/HomeOverview';
import { ChatPanel } from './components/ChatPanel';
import { Timeline } from './components/Timeline';
import { DeviceGrid } from './components/DeviceGrid';
import { Reports } from './pages/Reports';

type Tab = 'home' | 'devices' | 'timeline' | 'reports';

const tabs: { id: Tab; label: string }[] = [
  { id: 'home', label: '🏠 Home' },
  { id: 'devices', label: '📱 Devices' },
  { id: 'timeline', label: '📋 Timeline' },
  { id: 'reports', label: '📊 Reports' },
];

function App() {
  const [home, setHome] = useState<HomeSummary | null>(null);
  const [timeline, setTimeline] = useState<TimelineEntry[]>([]);
  const [chatHistory, setChatHistory] = useState<{ role: string; text: string }[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>('home');

  const loadData = async () => {
    try {
      const [homeData, timelineData] = await Promise.all([
        api.homeSummary(),
        api.timeline(30),
      ]);
      setHome(homeData);
      setTimeline(timelineData);
    } catch (err) {
      console.error('Failed to load data:', err);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleChat = async (message: string) => {
    setChatHistory(prev => [...prev, { role: 'user', text: message }]);
    setLoading(true);
    try {
      // First, get the plan (dry-run)
      let resp: ChatResponse = await api.chat(message, true, false);
      setChatHistory(prev => [...prev, { role: 'assistant', text: resp.reply }]);

      // If no confirmation needed and plan has actions, auto-execute
      if (resp.plan?.actions?.length > 0 && !resp.needs_confirmation) {
        setChatHistory(prev => [...prev, { role: 'assistant', text: '⏳ Executing...' }]);
        const execResp = await api.chat(message, false, true);
        // Replace the executing message with the result
        setChatHistory(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = { role: 'assistant', text: execResp.reply };
          return updated;
        });
      }

      // Refresh data
      const [homeData, timelineData] = await Promise.all([
        api.homeSummary(),
        api.timeline(30),
      ]);
      setHome(homeData);
      setTimeline(timelineData);
    } catch (err) {
      setChatHistory(prev => [...prev, { role: 'assistant', text: `Error: ${err}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-xiaomi-dark">
      <Header />

      {/* Tab Navigation */}
      <div className="max-w-7xl mx-auto px-4 mt-4">
        <div className="flex gap-1 bg-xiaomi-darker rounded-lg p-1 w-fit overflow-x-auto">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors whitespace-nowrap ${
                activeTab === tab.id
                  ? 'bg-xiaomi-orange text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {activeTab === 'home' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              {home && <HomeOverview home={home} onRefresh={loadData} />}
              <Timeline entries={timeline.slice(0, 10)} />
            </div>
            <div className="lg:col-span-1">
              <ChatPanel
                history={chatHistory}
                onSend={handleChat}
                loading={loading}
              />
            </div>
          </div>
        )}

        {activeTab === 'devices' && <DeviceGrid />}

        {activeTab === 'timeline' && <Timeline entries={timeline} full />}

        {activeTab === 'reports' && <Reports />}
      </main>
    </div>
  );
}

export default App;
