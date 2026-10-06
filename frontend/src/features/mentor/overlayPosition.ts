/**
 * Geometry-based placement for the floating mentor overlay (PH7).
 *
 * The overlay must sit near the code it refers to without covering it.
 * Strategy: place it in the largest free rectangle adjacent to the code
 * region — right side first, then below, then left — clamping to the viewport.
 */

export interface Rect {
  x: number
  y: number
  w: number
  h: number
}

export interface OverlayPlacement {
  x: number
  y: number
  side: 'right' | 'left' | 'below'
}

const OVERLAY_W = 340
const OVERLAY_H = 220
const GAP = 16
/** Max fraction of the code region the overlay may cover (P-17). */
export const MAX_COVERAGE = 0.25

export function coverageOf(code: Rect, overlay: Rect): number {
  const ix = Math.max(0, Math.min(code.x + code.w, overlay.x + overlay.w) - Math.max(code.x, overlay.x))
  const iy = Math.max(0, Math.min(code.y + code.h, overlay.y + overlay.h) - Math.max(code.y, overlay.y))
  const area = code.w * code.h
  return area > 0 ? (ix * iy) / area : 0
}

export function placeOverlay(code: Rect, viewport: { w: number; h: number }): OverlayPlacement {
  const rightSpace = viewport.w - (code.x + code.w)

  if (rightSpace >= OVERLAY_W + GAP) {
    return {
      x: code.x + code.w + GAP,
      y: clamp(code.y, 0, Math.max(0, viewport.h - OVERLAY_H)),
      side: 'right',
    }
  }

  const belowSpace = viewport.h - (code.y + code.h)
  if (belowSpace >= OVERLAY_H + GAP) {
    return {
      x: clamp(code.x, 0, Math.max(0, viewport.w - OVERLAY_W)),
      y: code.y + code.h + GAP,
      side: 'below',
    }
  }

  // Fall back to the left edge, or clamp inside the viewport if there is no room.
  return {
    x: clamp(code.x - OVERLAY_W - GAP, 0, Math.max(0, viewport.w - OVERLAY_W)),
    y: clamp(code.y, 0, Math.max(0, viewport.h - OVERLAY_H)),
    side: 'left',
  }
}

function clamp(v: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, v))
}
