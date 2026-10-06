import { useEffect, useState } from 'react';
import { getAnalytics, type Analytics } from '../services/api';

export default function AnalyticsPanel({ sessionToken }: { sessionToken: string | null }) {
  const [data, setData] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(false);

  const refresh = async () => {
    if (!sessionToken) return;
    setLoading(true);
    try {
      setData(await getAnalytics(sessionToken));
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refresh();
    const timer = window.setInterval(() => void refresh(), 10000);
    return () => window.clearInterval(timer);
  }, [sessionToken]);

  return (
    <section className="rounded-xl border border-gray-800 bg-gray-900/80 p-3">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-200">Session Analytics</h2>
        <button onClick={() => void refresh()} className="text-[10px] text-gray-500 hover:text-white">
          {loading ? '...' : 'Refresh'}
        </button>
      </div>
      {data ? (
        <>
          <div className="grid grid-cols-4 gap-2">
            {[
              ['Analyses', data.analyses],
              ['Fixed', data.errors_fixed],
              ['Hints', data.hints],
              ['Tests', data.tests_passed + '/' + data.tests_total],
            ].map(([label, value]) => (
              <div key={String(label)} className="rounded-lg bg-black/20 p-2 text-center">
                <div className="text-sm font-semibold text-white">{value}</div>
                <div className="text-[9px] uppercase tracking-wide text-gray-500">{label}</div>
              </div>
            ))}
          </div>
          <div className="mt-3 text-[11px] text-gray-500">
            Fast path {data.avg_analysis_ms.toFixed(1)}ms · Sandbox {data.avg_execution_ms.toFixed(1)}ms
          </div>
          <div className="mt-2 flex flex-wrap gap-1">
            {data.top_categories.map(item => (
              <span key={item.category} className="rounded-full border border-white/10 px-2 py-0.5 text-[9px] text-gray-400">
                {item.category}: {item.count}
              </span>
            ))}
          </div>
        </>
      ) : (
        <div className="text-xs text-gray-500">No analytics yet.</div>
      )}
    </section>
  );
}
