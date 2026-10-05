/**
 * AI Real-Time Coding Screener - Main Application
 *
 * Phase 3: Fast Static Analysis + Isolated Container Execution + Problem Bank
 */

import React, { useEffect, useState } from 'react';
import CodeEditor from './components/CodeEditor';
import DiagnosticPanel from './components/DiagnosticPanel';
import { ProblemPanel } from './features/problems/ProblemPanel';
import { RunPanel } from './features/run/RunPanel';
import { useAnalysisStore } from './stores/analysisStore';
import { useProblemStore } from './stores/problemStore';
import { Diagnostic } from './types/analysis';
import { Problem } from './types/execution';
import './App.css';

function App() {
  const {
    connectionStatus,
    connect,
    disconnect,
    diagnostics,
    lastAnalysisTime,
    analysisCount,
    averageAnalysisTime,
    sessionToken,
  } = useAnalysisStore();

  const { selectedProblem } = useProblemStore();

  const [code, setCode] = useState(
    `# Welcome to AI Real-Time Coding Screener
# Type Python code below to see real-time analysis, or pick a problem from the Problem Bank!

def calculate_fibonacci(n):
    """Calculate fibonacci number using recursion."""
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

def main():
    number = 10
    result = calculate_fibonacci(number)
    print(f"Fibonacci of {number} is {result}")

if __name__ == "__main__":
    main()
`
  );

  const [selectedDiagnostic, setSelectedDiagnostic] = useState<Diagnostic | null>(null);
  const [theme, setTheme] = useState<'vs-dark' | 'vs-light'>('vs-dark');
  const [sidebarTab, setSidebarTab] = useState<'problems' | 'diagnostics' | 'run'>('problems');

  // Auto-connect WebSocket on mount
  useEffect(() => {
    if (connectionStatus === 'disconnected') {
      connect('phase3-demo-session');
    }
  }, [connectionStatus, connect]);

  // When a problem is selected, populate starter code
  const handleProblemSelect = (problem: Problem) => {
    if (problem.starter_code) {
      setCode(problem.starter_code);
    }
    setSidebarTab('run');
  };

  const handleDiagnosticClick = (diagnostic: Diagnostic) => {
    setSelectedDiagnostic(diagnostic);
  };

  const getConnectionStatusStyle = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'text-green-400 bg-green-900/60 border border-green-700';
      case 'connecting':
        return 'text-yellow-400 bg-yellow-900/60 border border-yellow-700 animate-pulse';
      case 'disconnected':
        return 'text-gray-400 bg-gray-800 border border-gray-700';
      case 'error':
        return 'text-red-400 bg-red-900/60 border border-red-700';
      default:
        return 'text-gray-400 bg-gray-800';
    }
  };

  const errorCount = diagnostics.filter((d) => d.severity === 'error').length;
  const warningCount = diagnostics.filter((d) => d.severity === 'warning').length;

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col font-sans">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            {/* Title & Brand */}
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center shadow-md">
                <span className="text-white font-bold text-sm">AI</span>
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h1 className="text-base font-bold text-gray-100">AI Coding Screener & Mentor</h1>
                  <span className="text-[10px] bg-blue-950 text-blue-400 border border-blue-800 px-2 py-0.5 rounded font-mono">
                    Phase 3
                  </span>
                </div>
                <p className="text-xs text-gray-400">Real-time analysis & sandbox container execution</p>
              </div>
            </div>

            {/* Performance Stats & Controls */}
            <div className="flex items-center space-x-4">
              {analysisCount > 0 && (
                <div className="text-xs text-gray-400 font-mono">
                  {analysisCount} analyses • avg <span className="text-emerald-400">{averageAnalysisTime}ms</span>
                </div>
              )}

              {/* Connection Status Badge */}
              <div className={`px-2.5 py-1 rounded-full text-xs font-medium ${getConnectionStatusStyle()}`}>
                <div className="flex items-center space-x-1.5">
                  <div className="w-2 h-2 bg-current rounded-full" />
                  <span className="capitalize">{connectionStatus}</span>
                </div>
              </div>

              {/* Theme Toggle */}
              <button
                onClick={() => setTheme(theme === 'vs-dark' ? 'vs-light' : 'vs-dark')}
                className="px-2.5 py-1 bg-gray-800 hover:bg-gray-700 rounded text-xs transition-colors border border-gray-700"
              >
                {theme === 'vs-dark' ? '☀️' : '🌙'}
              </button>

              {/* Reconnect button */}
              {connectionStatus === 'disconnected' ? (
                <button
                  onClick={() => connect('phase3-demo-session')}
                  className="px-3 py-1 bg-emerald-700 hover:bg-emerald-600 rounded text-xs font-medium transition-colors"
                >
                  Connect WS
                </button>
              ) : (
                <button
                  onClick={disconnect}
                  className="px-2.5 py-1 bg-gray-800 hover:bg-red-900/60 hover:text-red-300 text-gray-400 rounded text-xs transition-colors border border-gray-700"
                >
                  Disconnect
                </button>
              )}
            </div>
          </div>

          {/* Quick Metrics Bar */}
          <div className="mt-2.5 flex items-center justify-between text-xs border-t border-gray-800/80 pt-2">
            <div className="flex items-center space-x-5">
              <div className="flex items-center space-x-2">
                <span className="text-gray-400">Static Issues:</span>
                {errorCount > 0 && <span className="text-rose-400 font-bold">{errorCount} errors</span>}
                {warningCount > 0 && <span className="text-amber-400 font-bold">{warningCount} warnings</span>}
                {diagnostics.length === 0 && <span className="text-emerald-400 font-medium">Clean ✓</span>}
              </div>

              {selectedProblem && (
                <div className="flex items-center space-x-2">
                  <span className="text-gray-400">Active Challenge:</span>
                  <span className="text-blue-400 font-medium">{selectedProblem.title}</span>
                </div>
              )}
            </div>

            {lastAnalysisTime !== null && (
              <div className="text-gray-400">
                Last static pass: <span className="font-mono text-emerald-400 font-bold">{lastAnalysisTime}ms</span>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Workspace Body */}
      <main className="flex-1 flex overflow-hidden">
        {/* Left / Center: Monaco Editor & Output Execution split */}
        <div className="flex-1 flex flex-col border-r border-gray-800">
          <div className="flex-1 p-3 min-h-[300px]">
            <CodeEditor
              initialCode={code}
              language="python"
              theme={theme}
              height="100%"
              onCodeChange={setCode}
              readOnly={false}
            />
          </div>

          {/* Bottom Panel: Execution and Sandbox Output */}
          <div className="h-64 p-3 pt-0">
            <RunPanel code={code} language="python" className="h-full" />
          </div>
        </div>

        {/* Right Sidebar: Problem Bank & Diagnostics Tabs */}
        <div className="w-96 flex flex-col bg-gray-950">
          {/* Sidebar Tab Header */}
          <div className="flex border-b border-gray-800 bg-gray-900">
            <button
              onClick={() => setSidebarTab('problems')}
              className={`flex-1 py-2.5 text-xs font-semibold transition-colors flex items-center justify-center space-x-1.5 ${
                sidebarTab === 'problems'
                  ? 'border-b-2 border-blue-500 text-blue-400 bg-gray-950'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              <span>📚</span>
              <span>Problems</span>
            </button>
            <button
              onClick={() => setSidebarTab('diagnostics')}
              className={`flex-1 py-2.5 text-xs font-semibold transition-colors flex items-center justify-center space-x-1.5 ${
                sidebarTab === 'diagnostics'
                  ? 'border-b-2 border-blue-500 text-blue-400 bg-gray-950'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              <span>🔍</span>
              <span>Diagnostics</span>
              {diagnostics.length > 0 && (
                <span className="text-[10px] bg-red-950 text-red-400 border border-red-800 px-1.5 rounded-full font-mono">
                  {diagnostics.length}
                </span>
              )}
            </button>
          </div>

          {/* Sidebar Tab Content */}
          <div className="flex-1 overflow-hidden flex flex-col">
            {sidebarTab === 'problems' && (
              <ProblemPanel
                onSelectProblem={handleProblemSelect}
                className="h-full border-none rounded-none"
              />
            )}

            {sidebarTab === 'diagnostics' && (
              <div className="flex-1 flex flex-col overflow-hidden">
                <DiagnosticPanel
                  onDiagnosticClick={handleDiagnosticClick}
                  className="flex-1 border-none rounded-none"
                />

                {/* Selected Diagnostic Detail */}
                {selectedDiagnostic && (
                  <div className="border-t border-gray-800 bg-gray-900 p-3 text-xs">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="font-semibold text-gray-200">Selected Finding</span>
                      <button
                        onClick={() => setSelectedDiagnostic(null)}
                        className="text-gray-500 hover:text-gray-300"
                      >
                        ✕
                      </button>
                    </div>
                    <div className="font-mono text-[11px] text-gray-400 mb-1">
                      Line {selectedDiagnostic.line}:{selectedDiagnostic.column + 1}
                      {selectedDiagnostic.category && ` • ${selectedDiagnostic.category}`}
                    </div>
                    <div className="text-gray-300 mb-2">{selectedDiagnostic.message}</div>
                    {selectedDiagnostic.fix_suggestion && (
                      <div className="p-2 bg-emerald-950/40 border border-emerald-900/60 rounded text-emerald-300">
                        💡 {selectedDiagnostic.fix_suggestion}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
