import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useSessionStore } from './controllers/sessionController'
import Layout from './views/Layout'
import CodeEditor from './views/CodeEditor'
import Dashboard from './views/Dashboard'
import ProblemBank from './views/ProblemBank'
import './App.css'

/**
 * Main App Component - Following MVC Pattern
 * Routes to different views and manages global application state
 */
function App() {
  const { currentSession, isLoading } = useSessionStore()

  if (isLoading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner"></div>
        <p>Loading AI Coding Screener...</p>
      </div>
    )
  }

  return (
    <div className="App">
      <Routes>
        {/* Main layout wrapper for authenticated sessions */}
        <Route path="/" element={<Layout />}>
          {/* Dashboard - Session overview and metrics */}
          <Route index element={<Dashboard />} />

          {/* Code Editor - Main coding interface */}
          <Route path="editor" element={<CodeEditor />} />
          <Route path="editor/:sessionToken" element={<CodeEditor />} />

          {/* Problem Bank - Browse and select coding problems */}
          <Route path="problems" element={<ProblemBank />} />
          <Route path="problems/:problemId" element={<CodeEditor />} />

          {/* Redirect unknown routes to dashboard */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </div>
  )
}

export default App