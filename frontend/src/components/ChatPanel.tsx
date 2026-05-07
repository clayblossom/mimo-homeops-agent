import { useState, useRef, useEffect } from 'react';

interface Props {
  history: { role: string; text: string }[];
  onSend: (message: string) => void;
  loading: boolean;
}

const quickCommands = [
  { label: '🌙 Sleep Mode', msg: 'Prepare my home for sleep mode' },
  { label: '💡 Lights Off', msg: 'Matikan semua lampu' },
  { label: '❄️ Cool Down', msg: 'Kamar panas, nyalakan AC' },
  { label: '⚡ Save Energy', msg: 'Hemat energi' },
  { label: '📊 Status', msg: 'Apa status rumah sekarang?' },
];

export function ChatPanel({ history, onSend, loading }: Props) {
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [history]);

  const handleSend = () => {
    if (!input.trim() || loading) return;
    onSend(input.trim());
    setInput('');
  };

  return (
    <div className="card flex flex-col h-[600px]">
      <h2 className="text-lg font-semibold mb-3">🤖 MiMo Chat</h2>

      {/* Quick Commands */}
      <div className="flex flex-wrap gap-1.5 mb-3">
        {quickCommands.map(cmd => (
          <button
            key={cmd.label}
            onClick={() => onSend(cmd.msg)}
            disabled={loading}
            className="text-xs bg-gray-700 hover:bg-gray-600 px-2 py-1 rounded-full transition-colors disabled:opacity-50"
          >
            {cmd.label}
          </button>
        ))}
      </div>

      {/* Chat History */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-3 mb-3 pr-1">
        {history.length === 0 && (
          <div className="text-center text-gray-500 text-sm mt-8">
            <p className="text-2xl mb-2">🏠</p>
            <p>Ask MiMo to control your home!</p>
            <p className="text-xs mt-1">Try a quick command above</p>
          </div>
        )}
        {history.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-xl px-3 py-2 text-sm whitespace-pre-wrap ${
                msg.role === 'user'
                  ? 'bg-xiaomi-orange text-white rounded-br-sm'
                  : 'bg-gray-700 text-gray-200 rounded-bl-sm'
              }`}
            >
              {msg.text}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-700 rounded-xl px-3 py-2 text-sm text-gray-400">
              <span className="animate-pulse">Thinking...</span>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          placeholder="Tell MiMo what to do..."
          className="flex-1 bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-xiaomi-orange"
          disabled={loading}
        />
        <button onClick={handleSend} disabled={loading || !input.trim()} className="btn-primary">
          ➤
        </button>
      </div>
    </div>
  );
}
