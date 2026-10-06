/**
 * Diagnostic Panel Component
 *
 * Displays code analysis results, syntax errors, linting warnings,
 * and code quality suggestions in an organized, filterable view.
 */

import React, { useState } from 'react';
import { Diagnostic } from '../types/analysis';
import { useAnalysisStore } from '../stores/analysisStore';

interface DiagnosticPanelProps {
  onDiagnosticClick?: (diagnostic: Diagnostic) => void;
  className?: string;
}

export const DiagnosticPanel: React.FC<DiagnosticPanelProps> = ({
  onDiagnosticClick,
  className = '',
}) => {
  const { diagnostics, lastAnalysisTime, analysisCount, averageAnalysisTime } = useAnalysisStore();
  const [filter, setFilter] = useState<'all' | 'error' | 'warning' | 'info' | 'suspicion'>('all');
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Filter diagnostics based on selected severity
  const filteredDiagnostics = diagnostics.filter(diagnostic => {
    if (filter === 'all') return true;
    return diagnostic.severity === filter;
  });

  // Count diagnostics by severity
  const counts = {
    error: diagnostics.filter(d => d.severity === 'error').length,
    warning: diagnostics.filter(d => d.severity === 'warning').length,
    info: diagnostics.filter(d => d.severity === 'info').length,
    suspicion: diagnostics.filter(d => d.severity === 'suspicion').length,
    hint: diagnostics.filter(d => d.severity === 'hint').length,
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'error':
        return <span className="px-2 py-0.5 text-xs bg-red-900 text-red-200 rounded">Error</span>;
      case 'warning':
        return <span className="px-2 py-0.5 text-xs bg-yellow-900 text-yellow-200 rounded">Warning</span>;
      case 'info':
        return <span className="px-2 py-0.5 text-xs bg-blue-900 text-blue-200 rounded">Info</span>;
      case 'hint':
        return <span className="px-2 py-0.5 text-xs bg-purple-900 text-purple-200 rounded">Hint</span>;
      default:
        return null;
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'error':
        return <span className="text-red-400">●</span>;
      case 'warning':
        return <span className="text-yellow-400">▲</span>;
      case 'info':
        return <span className="text-blue-400">ℹ</span>;
      case 'hint':
        return <span className="text-purple-400">💡</span>;
      default:
        return null;
    }
  };

  return (
    <div className={`bg-gray-900 border border-gray-800 rounded-lg overflow-hidden ${className}`}>
      {/* Panel Header */}
      <div className="flex items-center justify-between p-3 bg-gray-850 border-b border-gray-800">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="text-gray-400 hover:text-white transition-colors"
          >
            {isCollapsed ? '▶' : '▼'}
          </button>
          <h3 className="font-medium text-sm text-gray-200">
            Problems & Diagnostics ({diagnostics.length})
          </h3>
          {lastAnalysisTime !== null && (
            <span className="text-xs text-gray-500">
              ({lastAnalysisTime}ms)
            </span>
          )}
        </div>

        {/* Severity Filters */}
        <div className="flex items-center space-x-1">
          <button
            onClick={() => setFilter('all')}
            className={`px-2 py-1 text-xs rounded transition-colors ${
              filter === 'all'
                ? 'bg-gray-700 text-white'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            All ({diagnostics.length})
          </button>
          {counts.error > 0 && (
            <button
              onClick={() => setFilter('error')}
              className={`px-2 py-1 text-xs rounded transition-colors ${
                filter === 'error'
                  ? 'bg-red-900 text-red-200'
                  : 'text-red-400 hover:text-red-200'
              }`}
            >
              Errors ({counts.error})
            </button>
          )}
          {counts.warning > 0 && (
            <button
              onClick={() => setFilter('warning')}
              className={`px-2 py-1 text-xs rounded transition-colors ${
                filter === 'warning'
                  ? 'bg-yellow-900 text-yellow-200'
                  : 'text-yellow-400 hover:text-yellow-200'
              }`}
            >
              Warnings ({counts.warning})
            </button>
          )}
          {counts.info > 0 && (
            <button
              onClick={() => setFilter('info')}
              className={`px-2 py-1 text-xs rounded transition-colors ${
                filter === 'info'
                  ? 'bg-blue-900 text-blue-200'
                  : 'text-blue-400 hover:text-blue-200'
              }`}
            >
              Info ({counts.info})
            </button>
          )}
          {counts.suspicion > 0 && (
            <button
              onClick={() => setFilter('suspicion')}
              className={`px-2 py-1 text-xs rounded transition-colors ${
                filter === 'suspicion'
                  ? 'bg-orange-900 text-orange-200'
                  : 'text-orange-400 hover:text-orange-200'
              }`}
            >
              Suspicions ({counts.suspicion})
            </button>
          )}
        </div>
      </div>

      {/* Panel Content */}
      {!isCollapsed && (
        <div>
          {/* Diagnostics List */}
          {filteredDiagnostics.length > 0 ? (
            <div className="max-h-60 overflow-y-auto divide-y divide-gray-800">
              {filteredDiagnostics.map((diagnostic, index) => (
                <div
                  key={`${diagnostic.line}-${diagnostic.column}-${index}`}
                  onClick={() => onDiagnosticClick?.(diagnostic)}
                  className="p-3 hover:bg-gray-800 cursor-pointer transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-2 flex-1">
                      <span className="mt-0.5">
                        {getSeverityIcon(diagnostic.severity)}
                      </span>
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <span className="font-mono text-xs text-gray-400">
                            Line {diagnostic.line}:{diagnostic.column + 1}
                          </span>
                          {getSeverityBadge(diagnostic.severity)}
                          {diagnostic.code && (
                            <span className="text-xs text-gray-500 font-mono">
                              {diagnostic.code}
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-300 mt-1">
                          {diagnostic.message}
                        </p>
                        {diagnostic.fix_suggestion && (
                          <p className="text-xs text-green-400 mt-1 flex items-center space-x-1">
                            <span>💡</span>
                            <span>{diagnostic.fix_suggestion}</span>
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-6 text-center text-gray-500 text-sm">
              {diagnostics.length === 0 ? (
                <div>
                  <div className="text-green-400 text-lg mb-1">✓</div>
                  <div>No problems detected</div>
                  <div className="text-xs text-gray-600 mt-1">
                    Your code is clean and follows best practices
                  </div>
                </div>
              ) : (
                <div>No {filter}s found</div>
              )}
            </div>
          )}

          {/* Performance Footer */}
          <div className="flex items-center justify-between p-2 bg-gray-850 border-t border-gray-800 text-xs text-gray-500">
            <div>
              {analysisCount > 0 && (
                <span>
                  {analysisCount} analyses completed • Avg: {averageAnalysisTime}ms
                </span>
              )}
            </div>
            <div>
              {lastAnalysisTime !== null && (
                <span className={lastAnalysisTime > 100 ? 'text-yellow-500' : 'text-green-500'}>
                  Analysis: {lastAnalysisTime}ms
                </span>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DiagnosticPanel;