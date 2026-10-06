import type { BackendDiagnostic, Diagnostic } from '../types/analysis';

const API_BASE = (
  (import.meta as { env?: { VITE_API_URL?: string } }).env?.VITE_API_URL ||
  window.location.protocol + '//' + window.location.hostname + ':8000'
).replace(/\/$/, '');

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(API_BASE + path, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
  });
  if (!response.ok) throw new Error((await response.text()) || response.statusText);
  return response.json() as Promise<T>;
}

export interface Problem { id: string; title: string; description: string; difficulty: string; category: string; starter_code: string; test_cases?: Array<{ input: Record<string, unknown>; expected: unknown; description: string }>; }
export interface Hint { id: number; hint_level: number; hint_category: string; hint_text: string; hint_type: string; provider: string; model: string; generation_time_ms: number | null; safety_approved: boolean; contains_solution: boolean; created_at: string | null; }
export interface ExecutionResult { success: boolean; stdout: string; stderr: string; exit_code: number; execution_time_ms: number; error_type?: string | null; }
export interface TestResult { passed: boolean; tests: Array<{ description: string; expected: unknown; actual: unknown; passed: boolean; stdout: string; stderr: string; error_type?: string | null }>; test_count: number; passed_count: number; error?: string; }
export interface Analytics { analyses: number; hints: number; errors_detected: number; errors_fixed: number; execution_runs: number; tests_passed: number; tests_total: number; avg_analysis_ms: number; avg_execution_ms: number; top_categories: Array<{ category: string; count: number }>; }

export async function getSession(sessionToken: string) {
  return request<{ id: number; session_token: string; user_id: string; language: string; problem_id: string | null; is_active: boolean }>('/api/v1/sessions/' + encodeURIComponent(sessionToken));
}

export async function createSession(userId = 'local-user', language = 'python', problemId?: string) {
  return request<{ id: number; session_token: string; user_id: string; language: string; problem_id: string | null; is_active: boolean }>('/api/v1/sessions', { method: 'POST', body: JSON.stringify({ user_id: userId, language, problem_id: problemId ?? null }) });
}
export async function getProblems(): Promise<Problem[]> { return request<Problem[]>('/api/v1/problems'); }
export async function getProblem(problemId: string): Promise<Problem> { return request<Problem>('/api/v1/problems/' + encodeURIComponent(problemId)); }
export async function runCode(sessionToken: string, code: string, language: string, stdin = ''): Promise<ExecutionResult> {
  return request<ExecutionResult>('/api/v1/execution/run', { method: 'POST', body: JSON.stringify({ session_token: sessionToken, code, language, stdin }) });
}
export async function runTests(sessionToken: string, code: string, language: string, problemId: string): Promise<TestResult> {
  return request<TestResult>('/api/v1/execution/test', { method: 'POST', body: JSON.stringify({ session_token: sessionToken, code, language, problem_id: problemId }) });
}
export async function requestHint(sessionToken: string, code: string, diagnostics: Diagnostic[], hintLevel?: number, allowSolution = false): Promise<Hint> {
  const payloadDiagnostics = diagnostics.map(diagnostic => ({\n    id: diagnostic.id,\n    seq: diagnostic.seq ?? 0,\n    origin: diagnostic.source,\n    rule: diagnostic.code ?? null,\n    category: diagnostic.category,\n    severity: diagnostic.severity,\n    message_raw: diagnostic.message,\n    range: {\n      start: { line: diagnostic.line, col: diagnostic.column + 1 },\n      end: { line: diagnostic.end_line ?? diagnostic.line, col: (diagnostic.end_column ?? diagnostic.column) + 1 },\n    },\n    fingerprint: diagnostic.fingerprint ?? 'frontend',\n    confidence: diagnostic.confidence ?? 0.8,\n  }));\n  return request<Hint>('/api/v1/mentor/hint', { method: 'POST', body: JSON.stringify({ session_token: sessionToken, code, diagnostics: payloadDiagnostics, hint_level: hintLevel ?? null, allow_solution: allowSolution }) });
}
export async function sendHintFeedback(sessionToken: string, hintId: number, wasHelpful: boolean, reaction?: string) {
  return request<{ recorded: boolean }>('/api/v1/mentor/hint/' + hintId + '/feedback', { method: 'POST', body: JSON.stringify({ session_token: sessionToken, was_helpful: wasHelpful, reaction: reaction ?? null }) });
}
export async function getAnalytics(sessionToken: string): Promise<Analytics> { return request<Analytics>('/api/v1/analytics/' + encodeURIComponent(sessionToken)); }
export async function analyzeScreen(sessionToken: string, blob: Blob, language = 'python', region?: { left: number; top: number; width: number; height: number }) {
  const form = new FormData();
  form.append('frame', blob, 'screen.jpg');
  if (region) {
    form.append('region_left', String(region.left));
    form.append('region_top', String(region.top));
    form.append('region_width', String(region.width));
    form.append('region_height', String(region.height));
  }
  const url = API_BASE + '/api/v1/screen/analyze?session_token=' + encodeURIComponent(sessionToken) + '&language=' + encodeURIComponent(language);
  const response = await fetch(url, { method: 'POST', body: form });
  if (!response.ok) throw new Error((await response.text()) || 'Screen analysis failed');
  const body = await response.json() as { detected: boolean; confidence: number; region: { left: number; top: number; width: number; height: number } | null; code: string; diagnostics: BackendDiagnostic[]; notice?: string | null };\n  const diagnostics: Diagnostic[] = body.diagnostics.map(item => ({\n    id: item.id, seq: item.seq ?? 0,\n    line: item.range?.start?.line ?? 1,\n    column: (item.range?.start?.column ?? item.range?.start?.col ?? 1) - 1,\n    end_line: item.range?.end?.line ?? item.range?.start?.line ?? 1,\n    end_column: (item.range?.end?.column ?? item.range?.end?.col ?? item.range?.start?.col ?? 1) - 1,\n    message: item.message ?? item.message_raw ?? 'Analysis finding',\n    severity: item.severity ?? 'info', source: item.origin ?? 'screen',\n    category: item.category ?? 'unknown', code: item.rule ?? null,\n    fingerprint: item.fingerprint, confidence: item.confidence,\n  }));\n  return { ...body, diagnostics };
}
