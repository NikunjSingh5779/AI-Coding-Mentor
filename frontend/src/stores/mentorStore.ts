/**
 * Zustand store for mentor hints (Phase 4).
 * Talks to the backend hint API and keeps hint/notice state per issue.
 */

import { create } from 'zustand'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface Hint {
  id: string
  issue_id: string
  level: 1 | 2 | 3 | 4
  text: string
  source: 'llm' | 'template' | 'cache'
  category: string
  created_at: string
  latency_ms: number
  contains_solution: boolean
}

export interface MentorNotice {
  kind: string
  message: string
  issueId?: string
}

interface MentorState {
  hints: Hint[]
  notices: MentorNotice[]
  llmAvailable: boolean | null
  pendingIssueId: string | null
  /** Last shown level per issue (mirrors the backend ladder). */
  levelByIssue: Record<string, number>

  checkStatus: () => Promise<void>
  requestHint: (issueId: string, level?: number, confirmed?: boolean) => Promise<void>
  dismissNotice: (index: number) => void
  reset: () => void
}

const NOTICE_MESSAGES: Record<string, string> = {
  already_shown: 'All available hint levels for this issue are already shown.',
  h4_needs_confirmation: 'Confirm below to reveal the solution approach (H4).',
  h4_unavailable_no_llm: 'The full solution needs the AI backend, which is unavailable. The step-by-step hints above are all template-based.',
  ladder_error: 'That hint level is not available yet for this issue.',
  budget_exhausted_session: 'AI hint budget for this session is used up; hints are template-based for now.',
}

export const useMentorStore = create<MentorState>((set, get) => ({
  hints: [],
  notices: [],
  llmAvailable: null,
  pendingIssueId: null,
  levelByIssue: {},

  checkStatus: async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/hints/status`)
      if (!res.ok) throw new Error(`status ${res.status}`)
      const data = await res.json()
      set({ llmAvailable: Boolean(data.llm_enabled) })
    } catch {
      set({ llmAvailable: false })
    }
  },

  requestHint: async (issueId, level, confirmed = false) => {
    const state = get()
    const sessionToken = 'dev-session'
    set({ pendingIssueId: issueId })
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/hints/${encodeURIComponent(sessionToken)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ issue_id: issueId, level: level ?? null, confirmed }),
      })
      if (!res.ok) throw new Error(`hint request failed: ${res.status}`)
      const data = await res.json()

      if (data.hint) {
        const hint = data.hint as Hint
        set((s) => ({
          hints: [...s.hints.filter((h) => !(h.issue_id === hint.issue_id && h.level === hint.level)), hint],
          levelByIssue: { ...s.levelByIssue, [hint.issue_id]: Math.max(s.levelByIssue[hint.issue_id] ?? 0, hint.level) },
          pendingIssueId: null,
        }))
      } else {
        const kind = data.notice ?? 'unknown'
        set((s) => ({
          pendingIssueId: null,
          notices: [
            ...s.notices,
            { kind, message: NOTICE_MESSAGES[kind] ?? `Mentor: ${kind}`, issueId },
          ],
          // H4 confirmation pending: remember which issue is being confirmed
          ...(kind === 'h4_needs_confirmation' ? { pendingIssueId: issueId } : {}),
        }))
      }
    } catch (err) {
      set((s) => ({
        pendingIssueId: null,
        notices: [
          ...s.notices,
          { kind: 'mentor_unavailable', message: 'Could not reach the mentor backend.', issueId },
        ],
      }))
    }
  },

  dismissNotice: (index: number) =>
    set((s) => ({ notices: s.notices.filter((_, i) => i !== index) })),

  reset: () => set({ hints: [], notices: [], pendingIssueId: null, levelByIssue: {} }),
}))
