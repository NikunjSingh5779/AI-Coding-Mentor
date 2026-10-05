import { create } from 'zustand';
import { Problem, ProblemSummary } from '../types/execution';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface ProblemState {
  problems: ProblemSummary[];
  selectedProblem: Problem | null;
  isLoading: boolean;
  error: string | null;

  fetchProblems: () => Promise<void>;
  selectProblem: (problemId: string) => Promise<Problem | null>;
  clearSelectedProblem: () => void;
}

export const useProblemStore = create<ProblemState>((set, get) => ({
  problems: [],
  selectedProblem: null,
  isLoading: false,
  error: null,

  fetchProblems: async () => {
    set({ isLoading: true, error: null });
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/problems`);
      if (!res.ok) {
        throw new Error(`Failed to fetch problems: HTTP ${res.status}`);
      }
      const data: ProblemSummary[] = await res.json();
      set({ problems: data, isLoading: false });
    } catch (err: any) {
      set({ error: err.message || 'Error fetching problems', isLoading: false });
    }
  },

  selectProblem: async (problemId: string) => {
    set({ isLoading: true, error: null });
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/problems/${problemId}`);
      if (!res.ok) {
        throw new Error(`Failed to fetch problem ${problemId}: HTTP ${res.status}`);
      }
      const problem: Problem = await res.json();
      set({ selectedProblem: problem, isLoading: false });
      return problem;
    } catch (err: any) {
      set({ error: err.message || 'Error loading problem details', isLoading: false });
      return null;
    }
  },

  clearSelectedProblem: () => {
    set({ selectedProblem: null });
  },
}));
