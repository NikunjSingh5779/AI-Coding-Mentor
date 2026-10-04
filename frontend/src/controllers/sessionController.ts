/**
 * Session Controller - Client-side state management for coding sessions
 * Following MVC pattern: Controllers manage application state and business logic
 */
import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import type { SessionModel, CreateSessionRequest } from '../models/SessionModel'
import { sessionApi } from '../services/api'

interface SessionState {
  // Current session state
  currentSession: SessionModel | null
  sessions: SessionModel[]
  isLoading: boolean
  error: string | null

  // Actions
  createSession: (request: CreateSessionRequest) => Promise<void>
  loadSession: (sessionToken: string) => Promise<void>
  updateSession: (sessionToken: string, updates: Partial<SessionModel>) => Promise<void>
  updateCode: (code: string) => void
  endSession: () => Promise<void>
  clearError: () => void
}

export const useSessionStore = create<SessionState>()(
  devtools(
    (set, get) => ({
      // Initial state
      currentSession: null,
      sessions: [],
      isLoading: false,
      error: null,

      // Create new session
      createSession: async (request: CreateSessionRequest) => {
        set({ isLoading: true, error: null })
        try {
          const session = await sessionApi.createSession(request)
          set({
            currentSession: session,
            sessions: [session, ...get().sessions],
            isLoading: false
          })
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to create session',
            isLoading: false
          })
        }
      },

      // Load existing session
      loadSession: async (sessionToken: string) => {
        set({ isLoading: true, error: null })
        try {
          const session = await sessionApi.getSession(sessionToken)
          set({ currentSession: session, isLoading: false })
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to load session',
            isLoading: false
          })
        }
      },

      // Update session details
      updateSession: async (sessionToken: string, updates: Partial<SessionModel>) => {
        try {
          const updatedSession = await sessionApi.updateSession(sessionToken, updates)
          set(state => ({
            currentSession: state.currentSession?.session_token === sessionToken
              ? updatedSession
              : state.currentSession,
            sessions: state.sessions.map(s =>
              s.session_token === sessionToken ? updatedSession : s
            )
          }))
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to update session'
          })
        }
      },

      // Update code in current session (optimistic update)
      updateCode: (code: string) => {
        const { currentSession } = get()
        if (currentSession) {
          set({
            currentSession: {
              ...currentSession,
              current_code: code,
              updated_at: new Date().toISOString()
            }
          })

          // Debounced API call to persist code
          // TODO: Implement debounced persistence
        }
      },

      // End current session
      endSession: async () => {
        const { currentSession } = get()
        if (!currentSession) return

        try {
          await sessionApi.updateSession(currentSession.session_token, {
            is_active: false
          })
          set({ currentSession: null })
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to end session'
          })
        }
      },

      // Clear error state
      clearError: () => set({ error: null })
    }),
    {
      name: 'session-store',
      partialize: (state) => ({
        // Persist only essential data
        currentSession: state.currentSession,
        sessions: state.sessions.slice(0, 10) // Keep recent sessions
      })
    }
  )
)