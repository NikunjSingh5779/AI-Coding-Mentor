import React, { useEffect } from 'react';
import { useProblemStore } from '../../stores/problemStore';
import { Problem, ProblemSummary } from '../../types/execution';

interface ProblemPanelProps {
  onSelectProblem?: (problem: Problem) => void;
  className?: string;
}

export const ProblemPanel: React.FC<ProblemPanelProps> = ({
  onSelectProblem,
  className = '',
}) => {
  const {
    problems,
    selectedProblem,
    isLoading,
    error,
    fetchProblems,
    selectProblem,
    clearSelectedProblem,
  } = useProblemStore();

  useEffect(() => {
    fetchProblems();
  }, [fetchProblems]);

  const handleSelect = async (problemId: string) => {
    const problem = await selectProblem(problemId);
    if (problem && onSelectProblem) {
      onSelectProblem(problem);
    }
  };

  const getDifficultyBadge = (difficulty: string) => {
    switch (difficulty.toLowerCase()) {
      case 'easy':
        return 'bg-emerald-950 text-emerald-400 border-emerald-800';
      case 'medium':
        return 'bg-amber-950 text-amber-400 border-amber-800';
      case 'hard':
        return 'bg-rose-950 text-rose-400 border-rose-800';
      default:
        return 'bg-gray-800 text-gray-300 border-gray-700';
    }
  };

  return (
    <div className={`flex flex-col bg-gray-900 border border-gray-800 rounded-lg overflow-hidden ${className}`}>
      {/* Panel Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-gray-950 border-b border-gray-800">
        <div className="flex items-center space-x-2">
          <span className="text-lg">📚</span>
          <h2 className="text-sm font-semibold text-gray-200">Problem Bank</h2>
        </div>
        {selectedProblem && (
          <button
            onClick={clearSelectedProblem}
            className="text-xs text-gray-400 hover:text-gray-200 transition-colors"
          >
            ← Back to problem list
          </button>
        )}
      </div>

      {/* Error message */}
      {error && (
        <div className="p-3 m-3 bg-red-950/50 border border-red-800 rounded text-xs text-red-300">
          {error}
        </div>
      )}

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-4">
        {isLoading && (
          <div className="flex items-center justify-center h-32 text-gray-400 text-sm animate-pulse">
            Loading problem data...
          </div>
        )}

        {!isLoading && !selectedProblem && (
          <div className="space-y-2">
            <p className="text-xs text-gray-400 mb-3">
              Select a coding challenge to test against automated test suites:
            </p>
            {problems.map((prob) => (
              <div
                key={prob.id}
                onClick={() => handleSelect(prob.id)}
                className="p-3 bg-gray-800/60 hover:bg-gray-800 border border-gray-700/60 hover:border-blue-500/50 rounded-lg cursor-pointer transition-all flex items-center justify-between group"
              >
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium text-gray-200 group-hover:text-blue-400">
                      {prob.title}
                    </span>
                    <span
                      className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full border ${getDifficultyBadge(
                        prob.difficulty
                      )}`}
                    >
                      {prob.difficulty}
                    </span>
                  </div>
                  <div className="flex items-center space-x-3 mt-1.5 text-xs text-gray-400">
                    <span className="capitalize">{prob.category}</span>
                    <span>•</span>
                    <span>{prob.total_test_count} tests ({prob.public_test_count} public)</span>
                  </div>
                </div>
                <span className="text-gray-500 group-hover:text-blue-400 transition-transform group-hover:translate-x-1">
                  →
                </span>
              </div>
            ))}
          </div>
        )}

        {!isLoading && selectedProblem && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h1 className="text-lg font-bold text-gray-100">{selectedProblem.title}</h1>
              <span
                className={`text-xs font-semibold uppercase px-2.5 py-0.5 rounded-full border ${getDifficultyBadge(
                  selectedProblem.difficulty
                )}`}
              >
                {selectedProblem.difficulty}
              </span>
            </div>

            {/* Problem Tags */}
            <div className="flex flex-wrap gap-1.5">
              {selectedProblem.tags.map((tag) => (
                <span
                  key={tag}
                  className="text-[10px] bg-gray-800 text-gray-400 px-2 py-0.5 rounded border border-gray-700"
                >
                  #{tag}
                </span>
              ))}
            </div>

            {/* Description Render */}
            <div className="prose prose-invert prose-sm max-w-none text-gray-300 space-y-2 text-xs leading-relaxed border-t border-gray-800 pt-3">
              <div
                dangerouslySetInnerHTML={{
                  __html: selectedProblem.description
                    .replace(/### (.*?)\n/g, '<h3 class="font-bold text-sm text-gray-200 mt-2 mb-1">$1</h3>')
                    .replace(/# (.*?)\n/g, '')
                    .replace(/\*\*(.*?)\*\*/g, '<strong class="text-gray-200">$1</strong>')
                    .replace(/```([\s\S]*?)```/g, '<pre class="bg-gray-950 p-2 rounded text-blue-300 font-mono text-[11px] overflow-x-auto">$1</pre>'),
                }}
              />
            </div>

            {/* Public Test Examples Preview */}
            <div className="border-t border-gray-800 pt-3 space-y-2">
              <h4 className="text-xs font-semibold text-gray-300">Public Test Cases</h4>
              {selectedProblem.test_cases
                .filter((tc) => !tc.is_hidden)
                .map((tc, idx) => (
                  <div key={tc.id} className="bg-gray-950 p-2.5 rounded border border-gray-800 text-xs">
                    <div className="text-gray-400 font-medium mb-1">
                      Example {idx + 1} {tc.description ? `(${tc.description})` : ''}
                    </div>
                    <div className="grid grid-cols-2 gap-2 font-mono text-[11px]">
                      <div>
                        <span className="text-gray-500">Input:</span>
                        <div className="text-gray-300 bg-gray-900 px-2 py-1 rounded mt-0.5 whitespace-pre-wrap">
                          {tc.stdin || '<empty>'}
                        </div>
                      </div>
                      <div>
                        <span className="text-gray-500">Expected:</span>
                        <div className="text-emerald-400 bg-gray-900 px-2 py-1 rounded mt-0.5 whitespace-pre-wrap">
                          {tc.expected_output}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProblemPanel;
