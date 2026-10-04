"""
Complete Frontend React Components for AI Real-Time Coding Screener
"""
import React, { useState, useEffect } from 'react'
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { MonacoEditor } from '@monaco-editor/react'
import { Play, Lightbulb, Settings, History, BarChart3 } from 'lucide-react'
import './App.css'

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
})

// Session Store (Zustand)
import { create } from 'zustand'

interface SessionState {
  currentSession: any | null
  code: string
  hints: any[]
  analyses: any[]
  isLoading: boolean

  // Actions
  setCode: (code: string) => void
  requestHint: (level: number) => Promise<void>
  runAnalysis: () => Promise<void>
}

export const useSessionStore = create<SessionState>((set, get) => ({
  currentSession: null,
  code: `# Welcome to AI Real-Time Coding Screener!
# Try writing some Python code and get intelligent hints

def fibonacci(n):
    # TODO: Implement fibonacci sequence
    pass

# Test your function
print(fibonacci(10))`,
  hints: [],
  analyses: [],
  isLoading: false,

  setCode: (code: string) => set({ code }),

  requestHint: async (level: number) => {
    set({ isLoading: true })
    try {
      const response = await fetch('/api/v1/hints/request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_token: 'demo-session',
          hint_level: level,
        }),
      })
      const hint = await response.json()
      set(state => ({
        hints: [...state.hints, hint],
        isLoading: false
      }))
    } catch (error) {
      console.error('Failed to get hint:', error)
      set({ isLoading: false })
    }
  },

  runAnalysis: async () => {
    set({ isLoading: true })
    try {
      const response = await fetch('/api/v1/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_token: 'demo-session',
          code: get().code,
        }),
      })
      const analysis = await response.json()
      set(state => ({
        analyses: [...state.analyses, analysis],
        isLoading: false
      }))
    } catch (error) {
      console.error('Failed to analyze code:', error)
      set({ isLoading: false })
    }
  },
}))

// Code Editor Component
const CodeEditor: React.FC = () => {
  const { code, setCode, hints, runAnalysis, isLoading } = useSessionStore()

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Main Editor */}
      <div className="flex-1 flex flex-col">
        <div className="bg-white border-b border-gray-200 p-4 flex justify-between items-center">
          <h1 className="text-xl font-semibold text-gray-800">
            AI Real-Time Coding Screener
          </h1>
          <button
            onClick={runAnalysis}
            disabled={isLoading}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            <Play className="w-4 h-4" />
            {isLoading ? 'Analyzing...' : 'Run Analysis'}
          </button>
        </div>

        <div className="flex-1">
          <MonacoEditor
            height="100%"
            defaultLanguage="python"
            value={code}
            onChange={(value) => setCode(value || '')}
            options={{
              minimap: { enabled: false },
              fontSize: 14,
              lineNumbers: 'on',
              roundedSelection: false,
              scrollBeyondLastLine: false,
              readOnly: false,
              theme: 'vs-dark'
            }}
          />
        </div>
      </div>

      {/* Mentor Panel */}
      <div className="w-80 bg-white border-l border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-yellow-500" />
            AI Mentor
          </h2>
        </div>

        {/* Hint Levels */}
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-sm font-medium text-gray-600 mb-3">Request Hint</h3>
          <div className="grid grid-cols-2 gap-2">
            {[1, 2, 3, 4].map((level) => (
              <HintButton key={level} level={level} />
            ))}
          </div>
        </div>

        {/* Hints Display */}
        <div className="flex-1 overflow-y-auto">
          {hints.length === 0 ? (
            <div className="p-4 text-center text-gray-500">
              <Lightbulb className="w-8 h-8 mx-auto mb-2 text-gray-300" />
              <p className="text-sm">No hints yet. Write some code and click "Run Analysis" to get started!</p>
            </div>
          ) : (
            <div className="p-4 space-y-4">
              {hints.map((hint, index) => (
                <HintCard key={index} hint={hint} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// Hint Button Component
const HintButton: React.FC<{ level: number }> = ({ level }) => {
  const { requestHint, isLoading } = useSessionStore()

  const colors = {
    1: 'bg-green-100 text-green-700 hover:bg-green-200',
    2: 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200',
    3: 'bg-orange-100 text-orange-700 hover:bg-orange-200',
    4: 'bg-red-100 text-red-700 hover:bg-red-200',
  }

  const labels = {
    1: 'H1: General',
    2: 'H2: Specific',
    3: 'H3: Detailed',
    4: 'H4: Solution',
  }

  return (
    <button
      onClick={() => requestHint(level)}
      disabled={isLoading}
      className={`p-2 text-xs font-medium rounded-lg transition-colors disabled:opacity-50 ${colors[level as keyof typeof colors]}`}
    >
      {labels[level as keyof typeof labels]}
    </button>
  )
}

// Hint Card Component
const HintCard: React.FC<{ hint: any }> = ({ hint }) => {
  const levelColors = {
    1: 'border-green-200 bg-green-50',
    2: 'border-yellow-200 bg-yellow-50',
    3: 'border-orange-200 bg-orange-50',
    4: 'border-red-200 bg-red-50',
  }

  return (
    <div className={`p-3 rounded-lg border-l-4 ${levelColors[hint.hint_level as keyof typeof levelColors]}`}>
      <div className="flex justify-between items-start mb-2">
        <span className="text-xs font-medium text-gray-500">
          H{hint.hint_level} Hint
        </span>
        <span className="text-xs text-gray-400">
          {hint.provider || 'AI'}
        </span>
      </div>
      <p className="text-sm text-gray-700 leading-relaxed">
        {hint.hint_text}
      </p>
      {hint.generation_time_ms && (
        <div className="mt-2 text-xs text-gray-400">
          Generated in {hint.generation_time_ms}ms
        </div>
      )}
    </div>
  )
}

// Navigation Component
const Navigation: React.FC = () => {
  const navigate = useNavigate()

  const navItems = [
    { icon: Play, label: 'Workspace', path: '/workspace' },
    { icon: History, label: 'History', path: '/history' },
    { icon: BarChart3, label: 'Progress', path: '/progress' },
    { icon: Settings, label: 'Settings', path: '/settings' },
  ]

  return (
    <nav className="bg-gray-900 text-white w-16 flex flex-col items-center py-4">
      {navItems.map((item) => (
        <button
          key={item.path}
          onClick={() => navigate(item.path)}
          className="p-3 rounded-lg hover:bg-gray-700 transition-colors mb-2"
          title={item.label}
        >
          <item.icon className="w-5 h-5" />
        </button>
      ))}
    </nav>
  )
}

// Settings Component
const Settings: React.FC = () => {
  const [providers, setProviders] = useState<any[]>([])
  const [currentProvider, setCurrentProvider] = useState<any>(null)

  useEffect(() => {
    fetch('/api/v1/providers')
      .then(res => res.json())
      .then(data => {
        setProviders(data.available || [])
        setCurrentProvider(data.current)
      })
      .catch(console.error)
  }, [])

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="max-w-4xl mx-auto p-6">
        <h1 className="text-2xl font-bold text-gray-800 mb-6">Settings</h1>

        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">AI Provider Status</h2>

          {currentProvider && (
            <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span className="font-medium">Current Provider: {currentProvider.provider}</span>
              </div>
              <p className="text-sm text-gray-600">
                Model: {currentProvider.model} |
                Max Tokens: {currentProvider.max_tokens} |
                Temperature: {currentProvider.temperature}
              </p>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {providers.map((provider) => (
              <div key={provider} className="p-4 border border-gray-200 rounded-lg">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  <span className="font-medium capitalize">{provider.replace('_', ' ')}</span>
                </div>
                <p className="text-sm text-gray-500 mt-1">Available</p>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Hint Preferences</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Default Hint Level
              </label>
              <select className="w-full p-2 border border-gray-300 rounded-lg">
                <option value="1">H1 - General guidance</option>
                <option value="2">H2 - Specific direction</option>
                <option value="3">H3 - Detailed approach</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <input type="checkbox" id="autoAnalysis" className="rounded" />
              <label htmlFor="autoAnalysis" className="text-sm text-gray-700">
                Enable automatic code analysis
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Main App Component
function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="flex h-screen bg-gray-100">
        <Navigation />
        <div className="flex-1">
          <Routes>
            <Route path="/" element={<Navigate to="/workspace" replace />} />
            <Route path="/workspace" element={<CodeEditor />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/history" element={<div className="p-8"><h1 className="text-2xl">History - Coming Soon</h1></div>} />
            <Route path="/progress" element={<div className="p-8"><h1 className="text-2xl">Progress - Coming Soon</h1></div>} />
            <Route path="*" element={<Navigate to="/workspace" replace />} />
          </Routes>
        </div>
      </div>
      <Toaster position="top-right" />
    </QueryClientProvider>
  )
}

export default App