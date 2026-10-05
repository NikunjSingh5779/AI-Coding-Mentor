import React from 'react';
import { TestCaseResult } from '../../types/execution';

interface TestResultsProps {
  results: TestCaseResult[];
  durationMs?: number;
  className?: string;
}

export const TestResults: React.FC<TestResultsProps> = ({
  results,
  durationMs,
  className = '',
}) => {
  const passedCount = results.filter((r) => r.passed).length;
  const totalCount = results.length;
  const allPassed = passedCount === totalCount && totalCount > 0;

  return (
    <div className={`space-y-3 ${className}`}>
      {/* Summary Banner */}
      <div
        className={`p-3 rounded-lg border flex items-center justify-between ${
          allPassed
            ? 'bg-emerald-950/60 border-emerald-800 text-emerald-300'
            : 'bg-rose-950/60 border-rose-800 text-rose-300'
        }`}
      >
        <div className="flex items-center space-x-2">
          <span className="text-base">{allPassed ? '✅' : '❌'}</span>
          <div>
            <div className="text-sm font-bold">
              {allPassed ? 'All Test Cases Passed!' : `${passedCount} of ${totalCount} Tests Passed`}
            </div>
            {durationMs !== undefined && (
              <div className="text-[11px] opacity-80">Total execution time: {durationMs} ms</div>
            )}
          </div>
        </div>
        <span className="text-xs font-mono font-bold px-2 py-1 rounded bg-black/30">
          {Math.round((passedCount / totalCount) * 100)}%
        </span>
      </div>

      {/* Individual Test Cases */}
      <div className="space-y-2">
        {results.map((test, index) => (
          <div
            key={test.id}
            className={`p-3 rounded-lg border text-xs ${
              test.passed
                ? 'bg-gray-900/60 border-gray-800 hover:border-emerald-800/60'
                : 'bg-rose-950/20 border-rose-900/60'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                <span className={test.passed ? 'text-emerald-400' : 'text-rose-400'}>
                  {test.passed ? '✓' : '✗'}
                </span>
                <span className="font-semibold text-gray-200">
                  {test.is_hidden ? `Hidden Test Case #${index + 1}` : `Test Case #${index + 1}`}
                </span>
                {test.is_hidden && (
                  <span className="text-[10px] bg-purple-950 text-purple-400 border border-purple-800 px-1.5 py-0.5 rounded">
                    Hidden
                  </span>
                )}
              </div>
              <span className="text-gray-500 font-mono text-[11px]">{test.duration_ms} ms</span>
            </div>

            {/* Error message or stderr */}
            {test.stderr && (
              <div className="mt-2 p-2 bg-rose-950/40 border border-rose-900/50 rounded font-mono text-[11px] text-rose-300 whitespace-pre-wrap">
                {test.stderr}
              </div>
            )}

            {/* Public Test Output */}
            {!test.is_hidden && test.stdout && (
              <div className="mt-2 font-mono text-[11px] bg-gray-950 p-2 rounded border border-gray-800">
                <span className="text-gray-500 block text-[10px] mb-0.5">Program Output:</span>
                <span className="text-gray-300 whitespace-pre-wrap">{test.stdout}</span>
              </div>
            )}

            {/* Hidden Test Case Mask */}
            {test.is_hidden && !test.passed && (
              <div className="mt-1 text-[11px] text-gray-400 italic">
                Input and expected output are hidden for verification cases.
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default TestResults;
