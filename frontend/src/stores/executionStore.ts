import { create } from 'zustand';
import { RunResult } from '../types/execution';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface ExecutionState {
  isRunning: boolean;
  isSubmitting: boolean;
  runResult: RunResult | null;
  customStdin: string;
  error: string | null;

  setCustomStdin: (stdin: string) => void;
  runCode: (code: string, language?: string, stdin?: string) => Promise<RunResult | null>;
  submitSolution: (problemId: string, code: string, language?: string) => Promise<RunResult | null>;
  clearRunResult: () => void;
}

export const useExecutionStore = create<ExecutionState>((set, get) => ({
  isRunning: false,
  isSubmitting: false,
  runResult: null,
  customStdin: '',
  error: null,

  setCustomStdin: (stdin: string) => set({ customStdin: stdin }),

  runCode: async (code: string, language = 'python', stdin?: string) => {
    const inputStdin = stdin !== undefined ? stdin : get().customStdin;
    set({ isRunning: true, error: null });

    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code,
          language,
          stdin: inputStdin,
        }),
      });

      if (!res.ok) {
        throw new Error(`Execution error: HTTP ${res.status}`);
      }

      const result: RunResult = await res.json();
      set({ runResult: result, isRunning: false });
      return result;
    } catch (err: any) {
      const errorMsg = err.message || 'Execution failed';
      set({
        error: errorMsg,
        isRunning: false,
        runResult: {
          status: 'error',
          exit_code: -1,
          stdout: '',
          stderr: errorMsg,
          duration_ms: 0,
          truncated: false,
          diagnostics: [],
        },
      });
      return null;
    }
  },

  submitSolution: async (problemId: string, code: string, language = 'python') => {
    set({ isSubmitting: true, error: null });

    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/problems/${problemId}/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code,
          language,
        }),
      });

      if (!res.ok) {
        throw new Error(`Submission error: HTTP ${res.status}`);
      }

      const result: RunResult = await res.json();
      set({ runResult: result, isSubmitting: false });
      return result;
    } catch (err: any) {
      const errorMsg = err.message || 'Submission failed';
      set({
        error: errorMsg,
        isSubmitting: false,
        runResult: {
          status: 'error',
          exit_code: -1,
          stdout: '',
          stderr: errorMsg,
          duration_ms: 0,
          truncated: false,
          diagnostics: [],
        },
      });
      return null;
    }
  },

  clearRunResult: () => set({ runResult: null, error: null }),
}));
