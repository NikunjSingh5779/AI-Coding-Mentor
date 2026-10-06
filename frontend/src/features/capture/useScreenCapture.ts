/**
 * Screen capture (PH7): getDisplayMedia lifecycle, consent, frame sampling
 * and manual fallback UI. Frames are sent only after consent and settle.
 */

import { useCallback, useEffect, useRef, useState } from 'react'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

type CaptureState = 'idle' | 'consent' | 'capturing' | 'paused' | 'error'

interface FrameResponse {
  status: string
  tracking_state?: string
  region_confidence?: number
  ocr_confidence?: number
  notice?: string
  code_length?: number
  language?: string
  frame_hash?: string
}

export function useScreenCapture(sessionToken = 'dev-session') {
  const [state, setState] = useState<CaptureState>('idle')
  const [trackingState, setTrackingState] = useState('idle')
  const [lastNotice, setLastNotice] = useState<string | null>(null)
  const [consentGiven, setConsentGiven] = useState(false)

  const videoRef = useRef<HTMLVideoElement | null>(null)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const timerRef = useRef<number | null>(null)

  const SAMPLE_MS = 1500

  const sendFrame = useCallback(async () => {
    const video = videoRef.current
    const canvas = canvasRef.current
    if (!video || !canvas || video.videoWidth === 0) return

    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.drawImage(video, 0, 0)
    const frameB64 = canvas.toDataURL('image/jpeg', 0.7).split(',')[1]

    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/capture/${encodeURIComponent(sessionToken)}/frame`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ frame_b64: frameB64, consent: true }),
      })
      const data: FrameResponse = await res.json()
      setTrackingState(data.tracking_state ?? 'unknown')
      if (data.notice) setLastNotice(data.notice)
      else setLastNotice(null)
    } catch {
      setLastNotice('Could not reach the analysis backend.')
    }
  }, [sessionToken])

  const startSampling = useCallback(() => {
    if (timerRef.current) window.clearInterval(timerRef.current)
    timerRef.current = window.setInterval(sendFrame, SAMPLE_MS)
  }, [sendFrame])

  const stop = useCallback(() => {
    if (timerRef.current) window.clearInterval(timerRef.current)
    timerRef.current = null
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
    setState('idle')
    setTrackingState('idle')
  }, [])

  const start = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getDisplayMedia({ video: true })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
      }
      stream.getVideoTracks()[0].addEventListener('ended', () => {
        stop()
      })
      setConsentGiven(true)
      setState('capturing')
      startSampling()
    } catch {
      setState('error')
      setLastNotice('Screen share was cancelled or denied.')
    }
  }, [startSampling, stop])

  const pause = useCallback(() => {
    if (timerRef.current) window.clearInterval(timerRef.current)
    timerRef.current = null
    setState('paused')
  }, [])

  // Always stop tracks on unmount (no capture leaks after the component goes away).
  useEffect(() => {
    return () => {
      if (timerRef.current) window.clearInterval(timerRef.current)
      streamRef.current?.getTracks().forEach((t) => t.stop())
    }
  }, [])

  return { state, trackingState, lastNotice, consentGiven, videoRef, canvasRef, start, pause, stop, sendFrame }
}
