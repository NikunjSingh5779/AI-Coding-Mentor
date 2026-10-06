import { beforeEach, describe, expect, it } from 'vitest';

import { useAnalysisStore } from '../stores/analysisStore';

describe('analysis store', () => {
  beforeEach(() => {
    useAnalysisStore.setState({
      diagnostics: [],
      sequenceNumber: 0,
      analysisCount: 0,
      averageAnalysisTime: 0,
      lastAnalysisTime: null,
      lastError: null,
    });
  });

  it('normalizes canonical diagnostics and rejects stale results', () => {
    useAnalysisStore.getState()._handleMessage({
      type: 'analysis_result',
      sequence: 2,
      session_token: 'test-session',
      diagnostics: [
        {
          id: 'd1',
          seq: 2,
          origin: 'parser',
          rule: 'E999',
          category: 'SYNTAX_MISSING_TOKEN',
          severity: 'error',
          message: "Expected ':'",
          range: {
            start: { line: 3, column: 5 },
            end: { line: 3, column: 5 },
          },
          fingerprint: 'abc',
          confidence: 1,
        },
      ],
      analysis_time_ms: 12,
      lines_of_code: 3,
      has_syntax_errors: true,
      performance: { within_budget: true, diagnostic_count: 1 },
      timestamp: Date.now(),
      language: 'python',
    });

    expect(useAnalysisStore.getState().diagnostics[0]).toMatchObject({
      line: 3,
      column: 4,
      severity: 'error',
      code: 'E999',
      source: 'parser',
    });

    useAnalysisStore.getState()._handleMessage({
      type: 'analysis_result',
      sequence: 1,
      session_token: 'test-session',
      diagnostics: [],
      analysis_time_ms: 50,
      lines_of_code: 1,
      has_syntax_errors: false,
      performance: { within_budget: true, diagnostic_count: 0 },
      timestamp: Date.now(),
      language: 'python',
    });

    expect(useAnalysisStore.getState().diagnostics).toHaveLength(1);
    expect(useAnalysisStore.getState().sequenceNumber).toBe(2);
  });
});
