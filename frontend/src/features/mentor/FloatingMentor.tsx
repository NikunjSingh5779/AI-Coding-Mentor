/**
 * FloatingMentor (PH4/PH7): the floating mentor surface. Draggable and
 * dismissible, positioned near the affected code without obscuring it.
 */

import { useCallback, useRef, useState } from 'react'
import { placeOverlay, type Rect } from './overlayPosition'

export function FloatingMentor({
  codeRegion,
  hintText,
  onDismiss,
}: {
  codeRegion: Rect | null
  hintText: string
  onDismiss: () => void
}) {
  const viewport = { w: window.innerWidth, h: window.innerHeight }
  const initial = codeRegion
    ? placeOverlay(codeRegion, viewport)
    : { x: viewport.w - 380, y: 80, side: 'right' as const }

  const [pos, setPos] = useState({ x: initial.x, y: initial.y })
  const dragRef = useRef<{ dx: number; dy: number } | null>(null)

  const onPointerDown = useCallback(
    (e: React.PointerEvent) => {
      dragRef.current = { dx: e.clientX - pos.x, dy: e.clientY - pos.y }
      ;(e.target as HTMLElement).setPointerCapture(e.pointerId)
    },
    [pos.x, pos.y],
  )

  const onPointerMove = useCallback((e: React.PointerEvent) => {
    if (!dragRef.current) return
    setPos({ x: e.clientX - dragRef.current.dx, y: e.clientY - dragRef.current.dy })
  }, [])

  const onPointerUp = useCallback(() => {
    dragRef.current = null
  }, [])

  return (
    <div
      className="fixed z-50 w-[340px] rounded-lg border border-gray-700 bg-gray-900/95 shadow-xl backdrop-blur"
      style={{ left: pos.x, top: pos.y }}
      role="dialog"
      aria-label="AI mentor"
    >
      <div
        className="flex items-center justify-between px-3 py-2 cursor-move border-b border-gray-800"
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
      >
        <span className="text-xs font-semibold text-gray-200">🧭 Mentor</span>
        <button onClick={onDismiss} className="text-gray-500 hover:text-gray-300 text-xs" aria-label="Dismiss mentor">
          ✕
        </button>
      </div>
      <p className="p-3 text-xs text-gray-200 leading-relaxed whitespace-pre-wrap max-h-64 overflow-y-auto">
        {hintText}
      </p>
    </div>
  )
}
