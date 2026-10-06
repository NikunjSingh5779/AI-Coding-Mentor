import { useEffect, useRef, useState } from 'react';
import { analyzeScreen } from '../services/api';
import type { Diagnostic } from '../types/analysis';

interface Props {
  sessionToken: string | null;
  language: string;
  enabled?: boolean;
  onDetected: (code: string, diagnostics: Diagnostic[]) => void;
}

interface Region {
  left: number;
  top: number;
  width: number;
  height: number;
}

export default function ScreenCapturePanel({
  sessionToken,
  language,
  enabled = false,
  onDetected,
}: Props) {
  const [capturing, setCapturing] = useState(false);
  const [manualMode, setManualMode] = useState(false);
  const [status, setStatus] = useState('Screen source is off');
  const [confidence, setConfidence] = useState(0);
  const [region, setRegion] = useState<Region>({
    left: 0,
    top: 0,
    width: 1280,
    height: 720,
  });
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<number | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const busyRef = useRef(false);

  useEffect(() => {
    return () => {
      streamRef.current?.getTracks().forEach(track => track.stop());
      if (timerRef.current) window.clearInterval(timerRef.current);
    };
  }, []);

  if (!enabled) {
    return (
      <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-3 text-xs text-gray-500">
        Screen mode is disabled. Set FEATURE_SCREEN_SOURCE=true to enable it.
      </div>
    );
  }

  const stop = () => {
    streamRef.current?.getTracks().forEach(track => track.stop());
    streamRef.current = null;
    if (timerRef.current) window.clearInterval(timerRef.current);
    timerRef.current = null;
    setCapturing(false);
    setConfidence(0);
    setStatus('Capture stopped.');
  };

  const start = async () => {
    if (!sessionToken || capturing) return;
    if (!navigator.mediaDevices?.getDisplayMedia) {
      setStatus('Screen sharing is not supported by this browser.');
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getDisplayMedia({
        video: { frameRate: 3 },
        audio: false,
      });
      streamRef.current = stream;

      const video = videoRef.current || document.createElement('video');
      videoRef.current = video;
      video.srcObject = stream;
      video.muted = true;
      video.playsInline = true;
      await video.play();

      stream.getVideoTracks()[0]?.addEventListener('ended', stop, { once: true });
      setCapturing(true);
      setStatus('Capturing shared screen…');

      const capture = async () => {
        if (!videoRef.current || busyRef.current) return;
        busyRef.current = true;
        try {
          const canvas = document.createElement('canvas');
          canvas.width = videoRef.current.videoWidth || 1280;
          canvas.height = videoRef.current.videoHeight || 720;
          const context = canvas.getContext('2d');
          if (!context) return;

          context.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
          const blob = await new Promise<Blob | null>(resolve =>
            canvas.toBlob(resolve, 'image/jpeg', 0.65),
          );
          if (!blob) return;

          const result = await analyzeScreen(
            sessionToken,
            blob,
            language,
            manualMode ? region : undefined,
          );
          setConfidence(result.confidence);
          setStatus(
            result.detected
              ? 'Code region detected · ' + Math.round(result.confidence * 100) + '% confidence'
              : result.notice || 'No code region detected.',
          );
          if (result.detected) onDetected(result.code, result.diagnostics);
        } catch (error) {
          setStatus(error instanceof Error ? error.message : 'Screen analysis failed.');
        } finally {
          busyRef.current = false;
        }
      };

      await capture();
      timerRef.current = window.setInterval(() => void capture(), 1500);
    } catch {
      setStatus('Screen sharing was cancelled or blocked.');
    }
  };

  return (
    <section className="rounded-xl border border-gray-800 bg-gray-900/80 p-3">
      <video ref={videoRef} className="hidden" muted playsInline />

      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-gray-200">Screen Source</h2>
          <p className="mt-1 text-[10px] text-gray-500">{status}</p>
        </div>
        <button
          onClick={() => void (capturing ? Promise.resolve(stop()) : start())}
          className={
            capturing
              ? 'rounded-lg bg-red-500 px-3 py-2 text-xs font-semibold text-white'
              : 'rounded-lg border border-white/10 px-3 py-2 text-xs text-gray-200 hover:bg-white/5'
          }
        >
          {capturing ? 'Stop' : 'Share screen'}
        </button>
      </div>

      <div className="mt-3 flex items-center gap-2">
        <button
          onClick={() => setManualMode(!manualMode)}
          className={
            'rounded-lg border px-2 py-1 text-[10px] ' +
            (manualMode
              ? 'border-emerald-400/30 bg-emerald-400/10 text-emerald-200'
              : 'border-white/10 text-gray-500')
          }
        >
          {manualMode ? 'Manual region ON' : 'Manual fallback'}
        </button>
        <span className="text-[10px] text-gray-600">
          {manualMode ? 'Coordinates use the shared frame pixels.' : 'Automatic detection is safer by default.'}
        </span>
      </div>

      {manualMode && (
        <div className="mt-2 grid grid-cols-4 gap-2">
          {(['left', 'top', 'width', 'height'] as const).map(field => (
            <label key={field} className="text-[9px] text-gray-500">
              {field}
              <input
                type="number"
                min={0}
                value={region[field]}
                onChange={event =>
                  setRegion(prev => ({
                    ...prev,
                    [field]: Number(event.target.value) || 0,
                  }))
                }
                className="mt-1 w-full rounded border border-gray-700 bg-black/20 px-2 py-1 text-xs text-gray-200"
              />
            </label>
          ))}
        </div>
      )}

      {capturing && (
        <div className="mt-3 h-1 overflow-hidden rounded-full bg-gray-800">
          <div
            className="h-full bg-emerald-400 transition-all"
            style={{ width: Math.round(confidence * 100) + '%' }}
          />
        </div>
      )}
    </section>
  );
}
