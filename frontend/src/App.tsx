import { useEffect, useMemo, useState } from 'react';
import CodeEditor from './components/CodeEditor';
import DiagnosticPanel from './components/DiagnosticPanel';
import FloatingMentor from './components/FloatingMentor';
import ProblemPanel from './components/ProblemPanel';
import AnalyticsPanel from './components/AnalyticsPanel';
import ScreenCapturePanel from './components/ScreenCapturePanel';
import { useAnalysisStore } from './stores/analysisStore';
import { createSession, getSession, runCode, type Problem, type ExecutionResult } from './services/api';
import type { Diagnostic } from './types/analysis';
import './App.css';

const STARTER = `# AI Coding Mentor
# The mentor will analyze this code as you type.

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

print(fibonacci(10))
`;

const LANGUAGES = [
  { value: 'python', label: 'Python' },
  { value: 'javascript', label: 'JavaScript' },
  { value: 'cpp', label: 'C++' },
  { value: 'java', label: 'Java' },
] as const;

function App() {
  const [code, setCode] = useState(STARTER);
  const [language, setLanguage] = useState('python');
  const [sessionToken, setSessionToken] = useState<string | null>(null);
  const [problem, setProblem] = useState<Problem | null>(null);
  const [output, setOutput] = useState<ExecutionResult | null>(null);
  const [running, setRunning] = useState(false);
  const [screenDiagnostics, setScreenDiagnostics] = useState<Diagnostic[]>([]);
  const [screenCode, setScreenCode] = useState('');
  const [tab, setTab] = useState<'problems' | 'analytics' | 'screen'>('problems');
  const [theme, setTheme] = useState<'vs-dark' | 'vs-light'>('vs-dark');

  const {
    connect,
    disconnect,
    connectionStatus,
    diagnostics,
    lastAnalysisTime,
    analysisCount,
    averageAnalysisTime,
  } = useAnalysisStore();

  useEffect(() => {
    let cancelled = false;

    const bootstrap = async () => {
      const stored = localStorage.getItem('ai-coding-mentor-session-token');
      let token = stored;
      if (stored) {
        try {
          await getSession(stored);
        } catch {
          token = null;
          localStorage.removeItem('ai-coding-mentor-session-token');
        }
      }

      if (!token) {
        const created = await createSession('local-user', language);
        token = created.session_token;
        localStorage.setItem('ai-coding-mentor-session-token', token);
      }

      if (!cancelled) {
        setSessionToken(token);
        connect(token);
      }
    };

    void bootstrap().catch(() => {
      if (!cancelled) setSessionToken(null);
    });

    return () => {
      cancelled = true;
      disconnect();
    };
  }, [connect, disconnect]);

  const combinedDiagnostics = useMemo(
    () => [...diagnostics, ...screenDiagnostics],
    [diagnostics, screenDiagnostics],
  );

  const execute = async () => {
    if (!sessionToken) return;
    setRunning(true);
    try {
      setOutput(await runCode(sessionToken, code, language));
    } catch (error) {
      setOutput({
        success: false,
        stdout: '',
        stderr: error instanceof Error ? error.message : 'Execution failed',
        exit_code: -1,
        execution_time_ms: 0,
        error_type: 'CLIENT_ERROR',
      });
    } finally {
      setRunning(false);
    }
  };

  const loadStarter = (value: string) => {
    setCode(value);
    setOutput(null);
  };

  const handleScreen = (screenText: string, findings: Diagnostic[]) => {
    setScreenCode(screenText);
    setScreenDiagnostics(findings);
  };

  const effectiveCode = screenCode || code;

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <header className="sticky top-0 z-40 border-b border-gray-800 bg-gray-950/95 backdrop-blur">
        <div className="flex h-14 items-center justify-between px-4">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 text-xs font-bold">AI</div>
            <div>
              <div className="text-sm font-semibold">AI Coding Mentor</div>
              <div className="text-[10px] text-gray-500">Real-time analysis · sandbox · progressive mentoring</div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <select
              value={language}
              onChange={event => {
                setLanguage(event.target.value);
                setOutput(null);
                setScreenDiagnostics([]);
                setScreenCode('');
              }}
              className="rounded-lg border border-gray-700 bg-gray-900 px-2 py-1.5 text-xs text-gray-200"
            >
              {LANGUAGES.map(item => <option key={item.value} value={item.value}>{item.label}</option>)}
            </select>
            <span className="rounded-full border border-white/10 px-2 py-1 text-[10px] text-gray-500">
              {connectionStatus}
            </span>
            <button onClick={() => setTheme(theme === 'vs-dark' ? 'vs-light' : 'vs-dark')} className="rounded-lg border border-white/10 px-2 py-1 text-xs hover:bg-white/5">
              {theme === 'vs-dark' ? '☀' : '☾'}
            </button>
            <button onClick={execute} disabled={!sessionToken || running} className="rounded-lg bg-emerald-500 px-3 py-1.5 text-xs font-semibold text-gray-950 disabled:opacity-40">
              {running ? 'Running…' : 'Run code'}
            </button>
          </div>
        </div>
      </header>

      <main className="grid min-h-[calc(100vh-56px)] grid-cols-[minmax(0,1fr)_400px]">
        <section className="min-w-0 border-r border-gray-800 p-3">
          <div className="mb-3 flex items-center justify-between">
            <div className="text-xs text-gray-500">
              {diagnostics.length} active issue{diagnostics.length === 1 ? '' : 's'}
              {lastAnalysisTime !== null ? ' · ' + Math.round(lastAnalysisTime) + 'ms' : ''}
              {analysisCount > 0 ? ' · avg ' + averageAnalysisTime + 'ms' : ''}
            </div>
            {problem && <div className="text-[10px] text-blue-300">{problem.title}</div>}
          </div>

          <CodeEditor
            initialCode={code}
            language={language}
            theme={theme}
            height="calc(100vh - 150px)"
            onCodeChange={setCode}
          />

          <div className="mt-3 rounded-xl border border-gray-800 bg-gray-900/70 p-3">
            <div className="mb-2 text-xs font-semibold text-gray-300">Execution</div>
            {output ? (
              <div className="space-y-2 text-xs">
                <div className={output.success ? 'text-emerald-300' : 'text-red-300'}>
                  {output.success ? 'Execution completed' : 'Execution failed'}
                  {' · ' + output.execution_time_ms + 'ms'}
                </div>
                <pre className="max-h-36 overflow-auto rounded-lg bg-black/30 p-2 text-gray-300">{output.stdout || '(no stdout)'}</pre>
                {output.stderr && <pre className="max-h-36 overflow-auto rounded-lg bg-red-950/20 p-2 text-red-200">{output.stderr}</pre>}
              </div>
            ) : (
              <p className="text-xs text-gray-600">Run the current program in the isolated sandbox.</p>
            )}
          </div>
        </section>

        <aside className="min-w-0 space-y-3 overflow-y-auto bg-gray-950 p-3">
          <div className="flex rounded-xl border border-gray-800 bg-gray-900/70 p-1">
            {[
              ['problems', 'Problems'],
              ['analytics', 'Analytics'],
              ['screen', 'Screen'],
            ].map(([value, label]) => (
              <button key={value} onClick={() => setTab(value as typeof tab)} className={'flex-1 rounded-lg px-2 py-2 text-xs ' + (tab === value ? 'bg-white/10 text-white' : 'text-gray-500 hover:text-gray-200')}>
                {label}
              </button>
            ))}
          </div>

          <DiagnosticPanel />
          {tab === 'problems' && sessionToken && (
            <div className="h-[360px]">
              <ProblemPanel
                sessionToken={sessionToken}
                language={language}
                code={code}
                onLoadStarter={loadStarter}
                onSelect={setProblem}
              />
            </div>
          )}
          {tab === 'analytics' && <AnalyticsPanel sessionToken={sessionToken} />}
          {tab === 'screen' && (
            <ScreenCapturePanel
              sessionToken={sessionToken}
              language={language}
              enabled={((import.meta as { env?: { VITE_SCREEN_SOURCE_ENABLED?: string } }).env?.VITE_SCREEN_SOURCE_ENABLED ?? 'false') === 'true'}
              onDetected={handleScreen}
            />
          )}

          {screenCode && (
            <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-3">
              <div className="mb-1 text-[10px] uppercase tracking-wide text-emerald-300">Screen snapshot</div>
              <pre className="max-h-32 overflow-auto whitespace-pre-wrap text-[10px] text-gray-400">{effectiveCode}</pre>
            </div>
          )}
        </aside>
      </main>

      <FloatingMentor
        sessionToken={sessionToken}
        code={screenCode || code}
        diagnostics={combinedDiagnostics}
      />
    </div>
  );
}

export default App;
