/**
 * CapturePanel (PH7): consent dialog, share/stop controls, always-visible
 * capture indicator, tracking state and manual fallback messaging.
 */

import { useScreenCapture } from './useScreenCapture'

export function CapturePanel({ sessionToken }: { sessionToken?: string }) {
  const { state, trackingState, lastNotice, consentGiven, videoRef, canvasRef, start, pause, stop } =
    useScreenCapture(sessionToken)

  const capturing = state === 'capturing'

  return (
    <div className="p-3 space-y-3 text-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {/* Always-visible capture indicator */}
          <span
            className={`w-2.5 h-2.5 rounded-full ${
              capturing ? 'bg-red-500 animate-pulse' : state === 'paused' ? 'bg-amber-400' : 'bg-gray-600'
            }`}
            aria-label={capturing ? 'Screen capture active' : 'Screen capture inactive'}
          />
          <span className="text-xs text-gray-300">
            {capturing ? 'Capturing screen' : state === 'paused' ? 'Paused' : 'Screen capture off'}
          </span>
        </div>

        <div className="flex gap-2">
          {!consentGiven && (
            <button
              onClick={start}
              className="text-xs bg-blue-700 hover:bg-blue-600 text-white rounded px-2.5 py-1"
            >
              Share screen
            </button>
          )}
          {capturing && (
            <button onClick={pause} className="text-xs bg-gray-800 hover:bg-gray-700 text-gray-200 rounded px-2.5 py-1">
              Pause
            </button>
          )}
          {state === 'paused' && (
            <button onClick={start} className="text-xs bg-blue-700 hover:bg-blue-600 text-white rounded px-2.5 py-1">
              Resume
            </button>
          )}
          {consentGiven && (
            <button onClick={stop} className="text-xs bg-red-900 hover:bg-red-800 text-red-200 rounded px-2.5 py-1">
              Stop
            </button>
          )}
        </div>
      </div>

      {/* Tracking state */}
      {consentGiven && (
        <div className="text-xs text-gray-400">
          Code region:{' '}
          <span className={trackingState === 'tracking' ? 'text-emerald-400' : 'text-amber-400'}>
            {trackingState}
          </span>
        </div>
      )}

      {/* Manual fallback / notices */}
      {lastNotice && (
        <div className="text-xs bg-amber-950/60 border border-amber-800 text-amber-300 rounded p-2">
          {lastNotice}
          <div className="text-[11px] text-amber-400/80 mt-1">
            Tip: make sure your editor window is clearly visible, or use the editor tab for exact analysis.
          </div>
        </div>
      )}

      {/* Hidden media elements: video is never displayed (privacy) */}
      <video ref={videoRef} className="hidden" autoPlay muted />
      <canvas ref={canvasRef} className="hidden" />
    </div>
  )
}
