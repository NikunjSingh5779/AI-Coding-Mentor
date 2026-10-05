/**
 * Types for Problem Bank and Code Execution features
 */

import { Diagnostic } from './analysis';

export interface TestCase {
  id: string;
  stdin: string;
  expected_output: string;
  is_hidden: boolean;
  description?: string | null;
}

export interface ProblemSummary {
  id: string;
  title: string;
  difficulty: 'easy' | 'medium' | 'hard';
  category: string;
  tags: string[];
  public_test_count: number;
  total_test_count: number;
}

export interface Problem {
  id: string;
  title: string;
  difficulty: 'easy' | 'medium' | 'hard';
  category: string;
  description: string;
  starter_code: string;
  timeout_seconds: number;
  tags: string[];
  test_cases: TestCase[];
}

export interface TestCaseResult {
  id: string;
  passed: boolean;
  stdout: string;
  stderr: string;
  exit_code: number;
  duration_ms: number;
  is_hidden: boolean;
  error_type?: string | null;
}

export interface RunResult {
  status: 'success' | 'error' | 'timeout' | 'memory_limit' | 'busy' | 'disabled';
  exit_code: number;
  stdout: string;
  stderr: string;
  duration_ms: number;
  truncated: boolean;
  diagnostics: Diagnostic[];
  test_results?: TestCaseResult[] | null;
  all_passed?: boolean | null;
}
