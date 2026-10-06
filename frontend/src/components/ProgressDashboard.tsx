/**
 * ProgressDashboard (PH6): live metrics from the learner tracker —
 * issues opened/resolved, time-to-resolution, hint usage and
 * recurring mistake patterns. Pure CSS bars, no chart dependency.
 */

import { useEffect, useState } from 'react'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface ProgressData {
  session_token: string
  total_issues: number
  resolved_issues: number
  open_issues: number
  avg_time_to_resolve_s: number
  total_hints: number
  adaptation?: {
    recurring_categories: string[]
    suggested_starting_level: number
    summary: string
  }
}

function Bar({ label, value, max, color }: { label: string; value: number; max: number; color: string }) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0
  return (
    <div className="mb-3">
      <div className="flex justify-between text-xs text-gray-400 mb-1">
        <span>{label}</span>
        <span className="font-mono text-gray-200">{value}</span>
      </div>
      <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

export function ProgressDashboard() {
  const [data, setData] = useState<ProgressData | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/v1/progress/dev-session`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`status ${r.status}`))))
      .then(setData)
      .catch((e) => setError(String(e)))
  }, [])

  if (error) {
    return <div className="text-xs text-gray-500 p-4">Progress unavailable: {error}</div>
  }
  if (!data) {
    return <div className="text-xs text-gray-500 p-4">Loading progress…</div>
  }

  const resolveRate =
    data.total_issues > 0 ? Math.round((data.resolved_issues / data.total_issues) * 100) : 0

  return (
    <div className="p-4 space-y-4 text-sm">
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-3">
          <div className="text-2xl font-bold text-emerald-400">{data.resolved_issues}</div>
          <div className="text-xs text-gray-400">issues resolved</div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-3">
          <div className="text-2xl font-bold text-blue-400">{resolveRate}%</div>
          <div className="text-xs text-gray-400">resolve rate</div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-3">
          <div className="text-2xl font-bold text-amber-400">{data.avg_time_to_resolve_s}s</div>
          <div className="text-xs text-gray-400">avg time to fix</div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-3">
          <div className="text-2xl font-bold text-purple-400">{data.total_hints}</div>
          <div className="text-xs text-gray-400">hints used</div>
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-3">
        <Bar label="Issues opened" value={data.total_issues} max={Math.max(data.total_issues, 1)} color="bg-blue-600" />
        <Bar label="Resolved" value={data.resolved_issues} max={Math.max(data.total_issues, 1)} color="bg-emerald-600" />
        <Bar label="Still open" value={data.open_issues} max={Math.max(data.total_issues, 1)} color="bg-amber-600" />
      </div>

      {data.adaptation && data.adaptation.recurring_categories.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-3">
          <div className="text-xs font-semibold text-gray-300 mb-2">Recurring patterns</div>
          <div className="flex flex-wrap gap-1.5">
            {data.adaptation.recurring_categories.map((c) => (
              <span key={c} className="text-[10px] bg-rose-950 text-rose-300 border border-rose-800 rounded px-1.5 py-0.5 font-mono">
                {c}
              </span>
            ))}
          </div>
          <p className="text-[11px] text-gray-500 mt-2">{data.adaptation.summary}</p>
        </div>
      )}
    </div>
  )
}
