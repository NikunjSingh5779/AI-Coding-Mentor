import { useEffect, useRef, useState } from 'react';
import type { Diagnostic } from '../types/analysis';
import { requestHint, sendHintFeedback, type Hint } from '../services/api';

interface FloatingMentorProps { sessionToken: string | null; code: string; diagnostics: Diagnostic[]; enabled?: boolean; }

export default function FloatingMentor({ sessionToken, code, diagnostics, enabled = true }: FloatingMentorProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [pinned, setPinned] = useState(true);
  const [busy, setBusy] = useState(false);
  const [level, setLevel] = useState(1);
  const [hint, setHint] = useState<Hint | null>(null);
  const [position, setPosition] = useState({ x: 0, y: 90 });
  const dragRef = useRef<{ dx: number; dy: number } | null>(null);
  const cardRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!pinned || !cardRef.current) return;
    const width = cardRef.current.offsetWidth || 360;
    setPosition({ x: Math.max(8, window.innerWidth - width - 24), y: 90 });
  }, [pinned]);

  useEffect(() => { if (!diagnostics.length) setHint(null); }, [diagnostics.length]);
  if (!enabled) return null;
  const primary = diagnostics[0];

  const ask = async (requestedLevel: number, allowSolution = false) => {
    if (!sessionToken) return;
    setBusy(true);
    try {
      const result = await requestHint(sessionToken, code, diagnostics, requestedLevel, allowSolution);
      setHint(result);
      setLevel(result.hint_level);
    } catch (error) {
      setHint({
        id: -1, hint_level: requestedLevel, hint_category: 'error',
        hint_text: error instanceof Error ? error.message : 'Mentor request failed',
        hint_type: 'suggestion', provider: 'error', model: 'error',
        generation_time_ms: null, safety_approved: false, contains_solution: false, created_at: null,
      });
    } finally { setBusy(false); }
  };

  const onPointerDown = (event: React.PointerEvent) => {
    const rect = cardRef.current?.getBoundingClientRect();
    if (!rect) return;
    dragRef.current = { dx: event.clientX - rect.left, dy: event.clientY - rect.top };
    (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
  };
  const onPointerMove = (event: React.PointerEvent) => {
    if (!dragRef.current) return;
    setPinned(false);
    setPosition({ x: Math.max(8, event.clientX - dragRef.current.dx), y: Math.max(52, event.clientY - dragRef.current.dy) });
  };
  const onPointerUp = () => { dragRef.current = null; };

  const anchorStyle = pinned ? { right: 24, top: 86 } : { left: position.x, top: position.y };

  return (
    <div ref={cardRef} className="fixed z-[100] w-[360px] max-w-[calc(100vw-16px)] overflow-hidden rounded-2xl border border-white/10 bg-gray-950/95 shadow-2xl backdrop-blur-xl" style={anchorStyle}>
      <div className="flex cursor-move items-center justify-between border-b border-white/10 px-3 py-2" onPointerDown={onPointerDown} onPointerMove={onPointerMove} onPointerUp={onPointerUp}>
        <div className="flex items-center gap-2"><div className="h-2 w-2 rounded-full bg-emerald-400" /><span className="text-xs font-semibold tracking-[0.16em] text-gray-300">AI MENTOR</span></div>
        <div className="flex items-center gap-1">
          <button className="rounded px-2 py-1 text-[10px] text-gray-500 hover:bg-white/10 hover:text-white" onClick={() => setPinned(!pinned)}>{pinned ? 'PIN' : 'FLOAT'}</button>
          <button className="rounded px-2 py-1 text-gray-400 hover:bg-white/10 hover:text-white" onClick={() => setCollapsed(!collapsed)}>{collapsed ? '＋' : '−'}</button>
        </div>
      </div>
      {!collapsed && <div className="space-y-3 p-4">
        <div className="rounded-xl border border-white/5 bg-white/[0.03] p-3">
          <div className="mb-1 flex items-center justify-between"><span className="text-xs font-medium uppercase tracking-wide text-gray-500">Current finding</span>{primary && <span className="rounded-full bg-red-500/15 px-2 py-0.5 text-[10px] text-red-300">{primary.severity}</span>}</div>
          {primary ? <><p className="text-sm leading-5 text-gray-200">{primary.message}</p><p className="mt-1 text-[11px] text-gray-500">Line {primary.line}:{primary.column + 1}{primary.code ? ' · ' + primary.code : ''}</p></> : <p className="text-sm text-emerald-300">No active problem. Keep going.</p>}
        </div>
        <div className="flex items-center gap-2">
          {[1, 2, 3].map(item => <button key={item} disabled={!sessionToken || !diagnostics.length || busy} onClick={() => { setLevel(item); void ask(item); }} className={'flex-1 rounded-lg border px-2 py-2 text-xs ' + (level === item ? 'border-emerald-400/40 bg-emerald-400/10 text-emerald-200' : 'border-white/10 text-gray-400')}>H{item}</button>)}
          <button disabled={!sessionToken || !diagnostics.length || busy} onClick={() => { if (window.confirm('H4 can reveal the solution. Continue?')) void ask(4, true); }} className="flex-1 rounded-lg border border-amber-400/20 bg-amber-400/5 px-2 py-2 text-xs text-amber-200 disabled:opacity-50">H4</button>
        </div>
        <button disabled={!sessionToken || !diagnostics.length || busy} onClick={() => void ask(level)} className="w-full rounded-xl bg-emerald-500 px-3 py-2 text-sm font-semibold text-gray-950 disabled:opacity-40">{busy ? 'Thinking…' : 'Give me H' + level}</button>
        {hint && <div className="rounded-xl border border-white/10 bg-black/20 p-3"><div className="flex items-center justify-between"><span className="text-xs font-semibold text-emerald-300">H{hint.hint_level} · {hint.provider}</span><span className="text-[10px] text-gray-500">{hint.generation_time_ms ?? 0}ms</span></div><p className="mt-2 text-sm leading-5 text-gray-200">{hint.hint_text}</p>{hint.id > 0 && sessionToken && <div className="mt-3 flex gap-2"><button onClick={() => void sendHintFeedback(sessionToken, hint.id, true, 'helpful')} className="rounded-md border border-white/10 px-2 py-1 text-[10px] text-gray-400">Helpful</button><button onClick={() => void sendHintFeedback(sessionToken, hint.id, false, 'confusing')} className="rounded-md border border-white/10 px-2 py-1 text-[10px] text-gray-400">Confusing</button></div>}</div>}
        <div className="text-[10px] text-gray-600">Grounded in verified diagnostics. H1–H3 avoid full solutions.</div>
      </div>}
    </div>
  );
}
