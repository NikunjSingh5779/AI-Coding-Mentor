import React, { useState } from 'react';
import { useExecutionStore } from '../../stores/executionStore';
import { useProblemStore } from '../../stores/problemStore';
import { TestResults } from './TestResults';

interface RunPanelProps {
  code: string;
  language?: string;
  className?: string;
}

export const RunPanel: React.FC<RunPanelProps> = ({
  code,
  language = 'python',
  className = '',
}) => {
  const {
    isRunning,
    isSubmitting,
    runResult,
    customStdin,
    setCustomStdin,
    runCode,
    submitSolution,
    clearRunResult,
  } = useExecutionStore();

  const { selectedProblem } = useProblemStore();
  const [activeTab, setActiveTab] = useState<'output' | 'tests' | 'stdin'>('output');

  const handleRun = async () => {
    setActiveTab('output');
    await runCode(code, language);
  };

  const handleSubmit = async () => {
    if (!selectedProblem) return;
    setActiveTab('tests');
    await submitSolution(selectedProblem.id, code, language);
  };

  return (
    <div className={`flex flex-col bg-gray-900 border border-gray-800 rounded-lg overflow-hidden ${className}`}>
      {/* Run Controls Bar */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-gray-950 border-b border-gray-800">
        <div className="flex items-center space-x-2">
          {/* Tab buttons */}
          <button
            onClick={() => setActiveTab('output')}
            className={`px-3 py-1 text-xs font-medium rounded transition-colors ${
              activeTab === 'output'
                ? 'bg-gray-800 text-gray-100'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            Output
          </button>
          <button
            onClick={() => setActiveTab('stdin')}
            className={`px-3 py-1 text-xs font-medium rounded transition-colors ${
              activeTab === 'stdin'
                ? 'bg-gray-800 text-gray-100'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            Custom Input
            {customStdin.trim() && <span className="ml-1 w-1.5 h-1.5 inline-block bg-blue-400 rounded-full" />}
          </button>
          {selectedProblem && (
            <button
              onClick={() => setActiveTab('tests')}
              className={`px-3 py-1 text-xs font-medium rounded transition-colors ${
                activeTab === 'tests'
                  ? 'bg-gray-800 text-gray-100'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              Test Suite
              {runResult?.test_results && (
                <span className="ml-1.5 text-[10px] px-1.5 py-0.2 rounded bg-gray-700 font-mono">
                  {runResult.test_results.filter((t) => t.passed).length}/{runResult.test_results.length}
                </span>
              )}
            </button>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-2">
          {runResult && (
            <button
              onClick={clearRunResult}
              className="text-xs text-gray-500 hover:text-gray-300 px-2 py-1 transition-colors"
              title="Clear output"
            >
              Clear
            </button>
          )}

          {/* Run Code Button */}
          <button
            onClick={handleRun}
            disabled={isRunning || isSubmitting}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 disabled:opacity-50 text-gray-200 text-xs font-medium rounded border border-gray-700 transition-colors"
          >
            <span>{isRunning ? '⏳' : '▶'}</span>
            <span>{isRunning ? 'Running...' : 'Run Code'}</span>
          </button>

          {/* Submit Solution Button (if problem selected) */}
          {selectedProblem && (
            <button
              onClick={handleSubmit}
              disabled={isRunning || isSubmitting}
              className="flex items-center space-x-1.5 px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-medium rounded transition-colors shadow-sm"
            >
              <span>{isSubmitting ? '⏳' : '🚀'}</span>
              <span>{isSubmitting ? 'Evaluating...' : 'Submit'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Main Panel Content */}
      <div className="flex-1 p-3 overflow-y-auto font-mono text-xs">
        {/* Output Tab */}
        {activeTab === 'output' && (
          <div>
            {!runResult && !isRunning && (
              <div className="text-gray-500 text-center py-8 font-sans">
                Click <span className="font-semibold text-gray-400">Run Code</span> to execute your program in the isolated sandbox.
              </div>
            )}

            {isRunning && (
              <div className="flex items-center justify-center space-x-2 py-8 text-blue-400 font-sans">
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-ping" />
                <span>Executing in sandbox container...</span>
              </div>
            )}

            {runResult && !isRunning && (
              <div className="space-y-3">
                {/* Status Bar */}
                <div className="flex items-center justify-between pb-2 border-b border-gray-800 text-[11px] text-gray-400">
                  <div className="flex items-center space-x-2">
                    <span
                      className={`inline-block w-2 h-2 rounded-full ${
                        runResult.status === 'success' && runResult.exit_code === 0
                          ? 'bg-emerald-400'
                          : runResult.status === 'timeout'
                          ? 'bg-amber-400'
                          : 'bg-rose-400'
                      }`}
                    />
                    <span className="capitalize font-semibold text-gray-300">
                      {runResult.status} (exit: {runResult.exit_code})
                    </span>
                    {runResult.truncated && (
                      <span className="text-amber-400 bg-amber-950 px-1.5 py-0.5 rounded text-[10px]">
                        Truncated (64 KB cap)
                      </span>
                    )}
                  </div>
                  <span>{runResult.duration_ms} ms</span>
                </div>

                {/* Stdout display */}
                {runResult.stdout && (
                  <div>
                    <span className="text-gray-500 text-[10px] block mb-1 font-sans">Standard Output:</span>
                    <pre className="p-2.5 bg-gray-950 rounded border border-gray-800 text-gray-200 whitespace-pre-wrap overflow-x-auto">
                      {runResult.stdout}
                    </pre>
                  </div>
                )}

                {/* Stderr display */}
                {runResult.stderr && (
                  <div>
                    <span className="text-rose-400 text-[10px] block mb-1 font-sans">Standard Error:</span>
                    <pre className="p-2.5 bg-rose-950/30 rounded border border-rose-900/50 text-rose-300 whitespace-pre-wrap overflow-x-auto">
                      {runResult.stderr}
                    </pre>
                  </div>
                )}

                {!runResult.stdout && !runResult.stderr && (
                  <div className="text-gray-500 italic py-2">Process completed with no output.</div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Custom Stdin Tab */}
        {activeTab === 'stdin' && (
          <div className="space-y-2">
            <label className="text-gray-400 text-[11px] block font-sans">
              Provide input to feed into standard input (stdin):
            </label>
            <textarea
              value={customStdin}
              onChange={(e) => setCustomStdin(e.target.value)}
              placeholder="e.g. 10&#10;20 30"
              rows={5}
              className="w-full bg-gray-950 border border-gray-800 rounded p-2 text-gray-200 font-mono text-xs focus:outline-none focus:border-blue-500"
            />
            <div className="text-[10px] text-gray-500 font-sans">
              Standard input is piped into your program upon clicking "Run Code".
            </div>
          </div>
        )}

        {/* Test Suite Results Tab */}
        {activeTab === 'tests' && (
          <div>
            {isSubmitting && (
              <div className="flex items-center justify-center space-x-2 py-8 text-emerald-400 font-sans">
                <div className="w-2 h-2 bg-emerald-400 rounded-full animate-ping" />
                <span>Running test suite in sandbox...</span>
              </div>
            )}

            {!isSubmitting && runResult?.test_results && (
              <TestResults
                results={runResult.test_results}
                durationMs={runResult.duration_ms}
              />
            )}

            {!isSubmitting && !runResult?.test_results && (
              <div className="text-gray-500 text-center py-8 font-sans">
                Click <span className="font-semibold text-emerald-400">Submit</span> to evaluate your code against all test cases.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default RunPanel;
