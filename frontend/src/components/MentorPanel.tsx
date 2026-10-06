/**
 * MentorPanel (Phase 4): issues list with progressive hint ladder controls.
 * Renders hints with sanitised text (no HTML injection), feedback buttons,
 * and a confirmed H4 reveal flow.
 */

import { useEffect, useState } from 'react'
import { useAnalysisStore } from '../stores/analysisStore'
import { useMentorStore } from '../stores/mentorStore'
import { Lightbulb, ChevronRight, AlertTriangle, Sparkles, X } from 'lucide-react'

const LEVEL_LABELS: Record<number, string> = {
  1: 'Orient',
  2: 'Concept',
  3: 'Direction',
  4: 'Solution',
}

const LEVEL_COLORS: Record<number, string> = {
  1: 'bg-blue-950 text-blue-300 border-blue-800',
  2: 'bg-indigo-950 text-indigo-300 border-indigo-800',
  3: 'bg-purple-950 text-purple-300 border-purple-800',
  4: 'bg-rose-950 text-rose-300 border-rose-800',
}

export function MentorPanel({ code = '' }: { code?: string }) {
  const { diagnostics } = useAnalysisStore()
  const {
    hints,
    notices,
    llmAvailable,
    pendingIssueId,
    levelByIssue,
    requestHint,
    dismissNotice,
    checkStatus,
  } = useMentorStore()

  const [confirmingH4, setConfirmingH4] = useState<string | null>(null)

  useEffect(() => {
    checkStatus()
  }, [checkStatus])

  const issueIds = diagnostics
    .map((d) => (d as unknown as { fingerprint?: string }).fingerprint ?? `${d.category}:${d.line}:${d.column}`)
    .filter((id, i, arr) => arr.indexOf(id) === i)

  const nextLevelFor = (issueId: string): number => {
    const shown = levelByIssue[issueId] ?? 0
    return Math.min(shown + 1, 3)
  }

  const snapshotDiagnostics = () => diagnostics as unknown as Array<Record<string, unknown>>

  const handleNextHint = (issueId: string) => {
    const shown = levelByIssue[issueId] ?? 0
    if (shown >= 3) {
      setConfirmingH4(confirmingH4 === issueId ? null : issueId)
    } else {
      requestHint(issueId, undefined, false, code, snapshotDiagnostics())
    }
  }

  const handleConfirmH4 = (issueId: string) => {
    requestHint(issueId, 4, true, code, snapshotDiagnostics())
    setConfirmingH4(null)
  }

  return (
    <div className="flex flex-col gap-3 h-full overflow-y-auto text-sm">
      {/* LLM availability banner */}
      {llmAvailable === false && (
        <div className="flex items-center gap-2 text-xs bg-amber-950/60 border border-amber-800 text-amber-300 rounded p-2">
          <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
          <span>AI backend offline — hints are template-based (still useful, no code leaks).</span>
        </div>
      )}

      {/* Notices */}
      {notices.map((n, i) => (
        <div
          key={`${n.kind}-${i}`}
          className="flex items-start gap-2 text-xs bg-gray-900 border border-gray-700 text-gray-300 rounded p-2"
        >
          <Sparkles className="w-3.5 h-3.5 mt-0.5 shrink-0 text-gray-500" />
          <span className="flex-1">{n.message}</span>
          <button onClick={() => dismissNotice(i)} className="text-gray-500 hover:text-gray-300" aria-label="Dismiss notice">
            <X className="w-3 h-3" />
          </button>
        </div>
      ))}

      {/* Issues list */}
      {issueIds.length === 0 ? (
        <div className="text-xs text-gray-500 p-3 text-center">
          No issues right now. Keep coding — the mentor will chime in when it spots something verified.
        </div>
      ) : (
        issueIds.map((issueId) => {
          const issueHints = hints.filter((h) => h.issue_id === issueId)
          const maxShown = levelByIssue[issueId] ?? 0
          return (
            <div key={issueId} className="border border-gray-800 rounded-lg bg-gray-900/60 overflow-hidden">
              {/* Issue header */}
              <div className="px-3 py-2 flex items-center justify-between gap-2 bg-gray-900">
                <span className="text-xs font-medium text-gray-300 truncate">
                  Issue · {issueId.slice(0, 12)}
                </span>
                <button
                  onClick={() => handleNextHint(issueId)}
                  disabled={pendingIssueId === issueId}
                  className="flex items-center gap-1 text-xs bg-blue-700 hover:bg-blue-600 disabled:opacity-50 text-white rounded px-2 py-1 transition-colors whitespace-nowrap"
                >
                  <Lightbulb className="w-3 h-3" />
                  {maxShown === 0 ? 'Get hint' : maxShown >= 3 ? 'Reveal?' : 'More help'}
                  <ChevronRight className="w-3 h-3" />
                </button>
              </div>

              {/* Hints */}
              <div className="flex flex-col gap-2 p-3">
                {issueHints.map((h) => (
                  <div key={h.id} className={`rounded border p-2.5 ${LEVEL_COLORS[h.level]}`}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10px] font-bold uppercase tracking-wide">
                        H{h.level} · {LEVEL_LABELS[h.level]}
                      </span>
                      <span className="text-[10px] opacity-70">
                        {h.source === 'llm' ? 'AI' : h.source === 'cache' ? 'AI (cached)' : 'template'}
                      </span>
                    </div>
                    {/* Text rendered as plain text — never dangerouslySetInnerHTML */}
                    <p className="text-xs leading-relaxed whitespace-pre-wrap">{h.text}</p>
                  </div>
                ))}

                {/* H4 confirmation */}
                {confirmingH4 === issueId && (
                  <div className="rounded border border-rose-800 bg-rose-950/40 p-2.5 text-xs text-rose-200">
                    <p className="mb-2">
                      This reveals the solution approach (H4). Are you sure? Try the H3 direction first —
                      it sticks better.
                    </p>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleConfirmH4(issueId)}
                        className="bg-rose-700 hover:bg-rose-600 text-white rounded px-2 py-1 text-xs"
                      >
                        Yes, reveal
                      </button>
                      <button
                        onClick={() => setConfirmingH4(null)}
                        className="bg-gray-800 hover:bg-gray-700 text-gray-300 rounded px-2 py-1 text-xs"
                      >
                        Not yet
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )
        })
      )}
    </div>
  )
}
