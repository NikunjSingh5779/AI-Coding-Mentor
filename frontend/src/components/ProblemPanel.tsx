import { useEffect, useState } from 'react';
import { getProblems, runTests, type Problem, type TestResult } from '../services/api';

interface Props {
  sessionToken: string | null;
  language: string;
  code: string;
  onLoadStarter: (code: string) => void;
  onSelect: (problem: Problem | null) => void;
}

export default function ProblemPanel({ sessionToken, language, code, onLoadStarter, onSelect }: Props) {
  const [problems, setProblems] = useState<Problem[]>([]);
  const [selected, setSelected] = useState<Problem | null>(null);
  const [result, setResult] = useState<TestResult | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    void getProblems().then(setProblems).catch(() => setProblems([]));
  }, []);

  return (
    <section className="flex h-full min-h-0 flex-col gap-3 rounded-xl border border-gray-800 bg-gray-900/80 p-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-200">Problem Bank</h2>
        <span className="text-[10px] text-gray-500">{problems.length} challenges</span>
      </div>

      <select
        value={selected?.id ?? ''}
        onChange={event => {
          const problem = problems.find(item => item.id === event.target.value) ?? null;
          setSelected(problem);
          setResult(null);
          onSelect(problem);
        }}
        className="rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-gray-200 outline-none"
      >
        <option value="">Select a challenge…</option>
        {problems.map(problem => (
          <option key={problem.id} value={problem.id}>
            {problem.title} · {problem.difficulty}
          </option>
        ))}
      </select>

      {selected ? (
        <div className="min-h-0 flex-1 space-y-3 overflow-y-auto">
          <div>
            <h3 className="text-sm font-medium text-white">{selected.title}</h3>
            <p className="mt-1 whitespace-pre-wrap text-xs leading-5 text-gray-400">
              {selected.description}
            </p>
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => onLoadStarter(selected.starter_code)}
              className="rounded-lg border border-gray-700 px-3 py-2 text-xs text-gray-300 hover:bg-white/5"
            >
              Load starter
            </button>
            <button
              disabled={!sessionToken || loading}
              onClick={async () => {
                if (!sessionToken) return;
                setLoading(true);
                try {
                  setResult(await runTests(sessionToken, code, language, selected.id));
                } catch (error) {
                  setResult({
                    passed: false,
                    tests: [],
                    test_count: 0,
                    passed_count: 0,
                    error: error instanceof Error ? error.message : 'Sandbox unavailable',
                  });
                } finally {
                  setLoading(false);
                }
              }}
              className="rounded-lg bg-blue-500 px-3 py-2 text-xs font-semibold text-white hover:bg-blue-400 disabled:opacity-40"
            >
              {loading ? 'Running…' : 'Run tests'}
            </button>
          </div>

          {result && (
            <div className="rounded-lg border border-gray-800 bg-black/20 p-3">
              <div className={result.passed ? 'text-emerald-300' : 'text-red-300'}>
                {result.passed_count}/{result.test_count} tests passed
              </div>
              {result.error && <p className="mt-2 text-xs text-red-300">{result.error}</p>}
              <div className="mt-2 space-y-1">
                {result.tests.map((test, index) => (
                  <div key={index} className="flex items-center justify-between rounded bg-white/[0.03] px-2 py-1 text-[11px]">
                    <span className="truncate text-gray-400">{test.description}</span>
                    <span className={test.passed ? 'text-emerald-300' : 'text-red-300'}>
                      {test.passed ? 'PASS' : 'FAIL'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <p className="text-xs text-gray-500">
          Select a challenge to load a starter and run verified tests.
        </p>
      )}
    </section>
  );
}
