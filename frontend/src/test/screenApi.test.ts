import { describe, expect, it, vi } from 'vitest';

import { analyzeScreen } from '../services/api';

describe('screen API normalization', () => {
  it('converts backend ranges to Monaco-style zero-based columns', async () => {
    const response = {
      ok: true,
      json: vi.fn().mockResolvedValue({
        detected: true,
        confidence: 0.9,
        region: { left: 0, top: 0, width: 100, height: 100 },
        code: 'x = 1',
        diagnostics: [{
          id: 'x',
          seq: 1,
          origin: 'parser',
          rule: 'E999',
          category: 'SYNTAX_UNEXPECTED_TOKEN',
          severity: 'error',
          message: 'bad syntax',
          range: {
            start: { line: 2, column: 4 },
            end: { line: 2, column: 7 },
          },
        }],
      }),
    };
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response));

    const result = await analyzeScreen('session', new Blob(['x']));
    expect(result.diagnostics[0]).toMatchObject({
      line: 2,
      column: 3,
      end_line: 2,
      end_column: 6,
      code: 'E999',
    });
  });
});
