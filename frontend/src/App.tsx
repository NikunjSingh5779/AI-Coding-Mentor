/**
 * AI Real-Time Coding Screener - Main Application
 *
 * Phase 1: Real-time analysis pipeline with Monaco editor integration
 */

import React, { useEffect, useState } from 'react';
import CodeEditor from './components/CodeEditor';
import DiagnosticPanel from './components/DiagnosticPanel';
import { useAnalysisStore } from './stores/analysisStore';
import { Diagnostic } from './types/analysis';
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
    sessionToken
  } = useAnalysisStore();

  const [code, setCode] = useState(
    `# Welcome to AI Real-Time Coding Screener
# Type Python code below to see real-time analysis

def calculate_fibonacci(n):
    """Calculate fibonacci number using recursion."""
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

def main():
    # Test the fibonacci function
    number = 10
    result = calculate_fibonacci(number)
    print(f"Fibonacci of {number} is {result}")

if __name__ == "__main__":
    main()
`
  );

  const [selectedDiagnostic, setSelectedDiagnostic] = useState<Diagnostic | null>(null);
  const [theme, setTheme] = useState<'vs-dark' | 'vs-light'>('vs-dark');

  // Each browser tab gets its own session token so users never evict each other's sockets.
  const getSessionToken = (): string => {
    const key = 'ai-coding-mentor-session-token';
    const existing = sessionStorage.getItem(key);
    if (existing) return existing;

    const token =
      typeof crypto !== 'undefined' && 'randomUUID' in crypto
        ? crypto.randomUUID()
        : `session-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    sessionStorage.setItem(key, token);
    return token;
  };

  // Connect once when the app mounts. Manual disconnects stay disconnected.
  useEffect(() => {
    const token = getSessionToken();
    connect(token);
    return () => disconnect();
  }, [connect, disconnect]);

  // Analyze the current editor contents as soon as the socket becomes ready.
  useEffect(() => {
    if (connectionStatus === 'connected' && code.trim()) {
      useAnalysisStore.getState().sendCodeUpdate(code, 'python');
    }
  }, [connectionStatus, code]);

  // Handle diagnostic selection from panel
  const handleDiagnosticClick = (diagnostic: Diagnostic) => {
    setSelectedDiagnostic(diagnostic);
    // TODO: Jump to line in editor when Monaco ref is available
    console.log('Selected diagnostic:', diagnostic);
  };

  // Connection status styles
  const getConnectionStatusStyle = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'text-green-400 bg-green-900';
      case 'connecting':
        return 'text-yellow-400 bg-yellow-900 animate-pulse';
      case 'disconnected':
        return 'text-gray-400 bg-gray-700';
      case 'error':
        return 'text-red-400 bg-red-900';
      default:
        return 'text-gray-400 bg-gray-700';
    }
  };

  // Summary statistics
  const errorCount = diagnostics.filter(d => d.severity === 'error').length;
  const warningCount = diagnostics.filter(d => d.severity === 'warning').length;
  const infoCount = diagnostics.filter(d => d.severity === 'info').length;

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            {/* Title */}
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">AI</span>
              </div>
              <div>
                <h1 className="text-xl font-semibold">Real-Time Coding Screener</h1>
                <p className="text-sm text-gray-400">Live Static Analysis</p>
              </div>
            </div>

            {/* Status & Controls */}
            <div className="flex items-center space-x-4">
              {/* Performance Stats */}
              <div className="text-sm text-gray-400">
                {analysisCount > 0 && (
                  <span>
                    {analysisCount} analyses • Avg: {averageAnalysisTime}ms
                  </span>
                )}
              </div>

              {/* Connection Status */}
              <div className={`px-3 py-1 rounded-full text-xs font-medium ${getConnectionStatusStyle()}`}>
                <div className="flex items-center space-x-1">
                  <div className="w-2 h-2 bg-current rounded-full"></div>
                  <span className="capitalize">{connectionStatus}</span>
                </div>
              </div>

              {/* Theme Toggle */}
              <button
                onClick={() => setTheme(theme === 'vs-dark' ? 'vs-light' : 'vs-dark')}
                className="px-3 py-1 bg-gray-800 hover:bg-gray-700 rounded text-sm transition-colors"
              >
                {theme === 'vs-dark' ? '☀️' : '🌙'}
              </button>

              {/* Connection Controls */}
              <div className="flex items-center space-x-2">
                {connectionStatus === 'disconnected' ? (
                  <button
                    onClick={() => connect(getSessionToken())}
                    className="px-3 py-1 bg-green-700 hover:bg-green-600 rounded text-sm transition-colors"
                  >
                    Connect
                  </button>
                ) : (
                  <button
                    onClick={disconnect}
                    className="px-3 py-1 bg-red-700 hover:bg-red-600 rounded text-sm transition-colors"
                  >
                    Disconnect
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Quick Stats Bar */}
          <div className="mt-4 flex items-center space-x-6 text-sm">
            <div className="flex items-center space-x-2">
              <span className="text-gray-400">Problems:</span>
              <div className="flex items-center space-x-3">
                {errorCount > 0 && (
                  <span className="text-red-400">
                    {errorCount} error{errorCount !== 1 ? 's' : ''}
                  </span>
                )}
                {warningCount > 0 && (
                  <span className="text-yellow-400">
                    {warningCount} warning{warningCount !== 1 ? 's' : ''}
                  </span>
                )}
                {infoCount > 0 && (
                  <span className="text-blue-400">
                    {infoCount} suggestion{infoCount !== 1 ? 's' : ''}
                  </span>
                )}
                {diagnostics.length === 0 && (
                  <span className="text-green-400">All good ✓</span>
                )}
              </div>
            </div>

            {lastAnalysisTime !== null && (
              <div className="flex items-center space-x-2">
                <span className="text-gray-400">Last analysis:</span>
                <span className={`font-mono ${lastAnalysisTime > 100 ? 'text-yellow-400' : 'text-green-400'}`}>
                  {lastAnalysisTime}ms
                </span>
              </div>
            )}

            <div className="flex items-center space-x-2">
              <span className="text-gray-400">Session:</span>
              <span className="font-mono text-gray-300 text-xs">
                {sessionToken?.substring(0, 8)}...
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex h-screen">
        {/* Editor Section */}
        <div className="flex-1 flex flex-col">
          <div className="flex-1 p-4">
            <CodeEditor
              initialCode={code}
              language="python"
              theme={theme}
              height="calc(100vh - 200px)"
              onCodeChange={setCode}
              readOnly={false}
            />
          </div>
        </div>

        {/* Diagnostics Sidebar */}
        <div className="w-96 border-l border-gray-800 flex flex-col">
          <DiagnosticPanel
            onDiagnosticClick={handleDiagnosticClick}
            className="flex-1"
          />

          {/* Selected Diagnostic Detail */}
          {selectedDiagnostic && (
            <div className="border-t border-gray-800 bg-gray-900 p-4">
              <div className="mb-2">
                <h4 className="text-sm font-medium text-gray-200">Selected Problem</h4>
              </div>
              <div className="space-y-2">
                <div className="text-xs text-gray-400 font-mono">
                  Line {selectedDiagnostic.line}:{selectedDiagnostic.column + 1}
                  {selectedDiagnostic.code && ` • ${selectedDiagnostic.code}`}
                </div>
                <div className="text-sm text-gray-300">
                  {selectedDiagnostic.message}
                </div>
                {selectedDiagnostic.fix_suggestion && (
                  <div className="text-sm text-green-400 bg-green-900/20 p-2 rounded">
                    <div className="flex items-center space-x-1 mb-1">
                      <span>💡</span>
                      <span className="font-medium">Suggestion</span>
                    </div>
                    <div>{selectedDiagnostic.fix_suggestion}</div>
                  </div>
                )}
                <button
                  onClick={() => setSelectedDiagnostic(null)}
                  className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
                >
                  Clear selection
                </button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;