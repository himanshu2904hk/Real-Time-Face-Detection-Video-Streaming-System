import React, { useEffect, useRef, useState } from 'react';
import VideoFeed from './components/VideoFeed.jsx';
import RoiPanel from './components/RoiPanel.jsx';

const HTTP_BASE = import.meta.env.VITE_BACKEND_HTTP || 'http://localhost:8000';
const WS_BASE = import.meta.env.VITE_BACKEND_WS || 'ws://localhost:8000';
const CAPTURE_FPS = 10;
const JPEG_QUALITY = 0.7;

export default function App() {
  const [session, setSession] = useState(null);
  const [status, setStatus] = useState('idle');
  const [errorMsg, setErrorMsg] = useState('');
  const [latestRoi, setLatestRoi] = useState(null);
  const [history, setHistory] = useState([]);
  const [frameCount, setFrameCount] = useState(0);
  const [faceCount, setFaceCount] = useState(0);
  const [uptime, setUptime] = useState(0);
  const [wsState, setWsState] = useState('Disconnected');

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const ingestWsRef = useRef(null);
  const captureTimerRef = useRef(null);
  const streamImgRef = useRef(null);
  const streamUrlRef = useRef(null);
  const startTimeRef = useRef(null);
  const uptimeTimerRef = useRef(null);

  const start = async () => {
    setErrorMsg('');
    setStatus('connecting');
    setFrameCount(0);
    setFaceCount(0);
    setUptime(0);
    setHistory([]);
    setWsState('Connecting…');
    try {
      const res = await fetch(`${HTTP_BASE}/api/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ label: 'webcam' }),
      });
      if (!res.ok) throw new Error(`Session create failed: ${res.status}`);
      const s = await res.json();
      setSession(s);

      const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 }, audio: false });
      videoRef.current.srcObject = stream;
      await videoRef.current.play();

      const ingestWs = new WebSocket(`${WS_BASE}/ws/ingest/${s.id}`);
      ingestWs.binaryType = 'arraybuffer';
      ingestWs.onopen = () => {
        setStatus('live');
        setWsState('Connected');
        startTimeRef.current = Date.now();
        uptimeTimerRef.current = setInterval(() => setUptime(Math.floor((Date.now() - startTimeRef.current) / 1000)), 1000);
        startCapture(ingestWs);
      };
      ingestWs.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data);
          if (data.error) { console.warn('server:', data.error); return; }
          setFrameCount((n) => n + 1);
          if (data.detection) {
            const roi = { ...data.detection, frame_index: data.frame_index, t: Date.now() };
            setLatestRoi(roi);
            setFaceCount((n) => n + 1);
            setHistory((h) => [roi, ...h].slice(0, 50));
          } else {
            setLatestRoi(null);
          }
        } catch (_) {}
      };
      ingestWs.onerror = () => { setStatus('error'); setErrorMsg('WebSocket connection failed'); setWsState('Error'); };
      ingestWs.onclose = () => {
        clearInterval(captureTimerRef.current);
        clearInterval(uptimeTimerRef.current);
        setWsState('Disconnected');
        setStatus((cur) => (cur === 'error' ? cur : 'idle'));
      };
      ingestWsRef.current = ingestWs;

      const streamWs = new WebSocket(`${WS_BASE}/ws/stream/${s.id}`);
      streamWs.binaryType = 'blob';
      streamWs.onmessage = (ev) => {
        if (streamUrlRef.current) URL.revokeObjectURL(streamUrlRef.current);
        const url = URL.createObjectURL(ev.data);
        streamUrlRef.current = url;
        if (streamImgRef.current) streamImgRef.current.src = url;
      };
    } catch (err) {
      setStatus('error');
      setErrorMsg(err.message || 'Failed to start');
      setWsState('Error');
    }
  };

  const stop = () => {
    clearInterval(captureTimerRef.current);
    clearInterval(uptimeTimerRef.current);
    if (ingestWsRef.current) ingestWsRef.current.close();
    if (videoRef.current?.srcObject) { videoRef.current.srcObject.getTracks().forEach((t) => t.stop()); videoRef.current.srcObject = null; }
    if (streamImgRef.current) streamImgRef.current.src = '';
    if (streamUrlRef.current) { URL.revokeObjectURL(streamUrlRef.current); streamUrlRef.current = null; }
    setLatestRoi(null);
    setStatus('idle');
  };

  const startCapture = (ws) => {
    captureTimerRef.current = setInterval(() => {
      if (!videoRef.current || ws.readyState !== WebSocket.OPEN) return;
      const v = videoRef.current;
      if (v.videoWidth === 0) return;
      const canvas = canvasRef.current;
      canvas.width = v.videoWidth; canvas.height = v.videoHeight;
      canvas.getContext('2d').drawImage(v, 0, 0);
      canvas.toBlob(
        (blob) => { if (blob && ws.readyState === WebSocket.OPEN) blob.arrayBuffer().then((buf) => ws.send(buf)); },
        'image/jpeg', JPEG_QUALITY,
      );
    }, Math.round(1000 / CAPTURE_FPS));
  };

  useEffect(() => () => stop(), []);

  const reset = () => {
    if (status === 'live' || status === 'error') stop();
    setFrameCount(0);
    setFaceCount(0);
    setUptime(0);
    setHistory([]);
    setLatestRoi(null);
    setErrorMsg('');
  };

  const fmtUptime = (s) => `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m ${s % 60}s`;
  const detRate = frameCount > 0 ? Math.round((faceCount / frameCount) * 100) : 0;

  const wsColor = wsState === 'Connected' ? 'green' : wsState === 'Error' ? 'red' : wsState === 'Connecting…' ? 'amber' : 'red';

  return (
    <>
      <nav className="navbar">
        <div className="navbar-brand">
          <div className="brand-icon">🎯</div>
          <span className="brand-name">Real-Time Face Detection System</span>
        </div>
        <div className="navbar-right">
          <span className="nav-pill">FastAPI · PostgreSQL · WebSocket</span>
          <span className={`status-pill ${status}`}>
            <span className="status-dot" />
            {status === 'live' ? `Live · ${session?.id?.slice(0, 8)}` :
             status === 'connecting' ? 'Connecting…' :
             status === 'error' ? 'Error' : 'Idle'}
          </span>
        </div>
      </nav>

      <div className="page">
        {errorMsg && <div className="error-banner">{errorMsg}</div>}

        <div className="three-col">
          {/* ── Left col ── */}
          <div className="left-col">
            <div className="card">
              <div className="card-header"><span className="card-title">Control &amp; Configuration</span></div>
              <div className="control-body">
                <button className="btn btn-start" onClick={start} disabled={status === 'live' || status === 'connecting'}>
                  {status === 'connecting' ? '⟳ Connecting…' : '▶ Start Live Stream'}
                </button>
                <button className="btn btn-stop" onClick={stop} disabled={status !== 'live'}>
                  ■ Stop
                </button>
                <button className="btn btn-reset" onClick={reset} disabled={status === 'connecting'}>
                  ↺ Reset Stats
                </button>
              </div>
            </div>

            <div className="card">
              <div className="card-header"><span className="card-title">Session Stats</span></div>
              <div className="stats-grid">
                <div className="stat-cell">
                  <div className="stat-label">Frames</div>
                  <div className="stat-value">{frameCount.toLocaleString()}</div>
                  <div className="stat-sub">processed</div>
                </div>
                <div className="stat-cell">
                  <div className="stat-label">Det. Rate</div>
                  <div className={`stat-value${faceCount > 0 ? ' green' : ''}`}>{detRate}%</div>
                  <div className="stat-sub">{faceCount} frames</div>
                </div>
                <div className="stat-cell" style={{ gridColumn: '1 / -1' }}>
                  <div className="stat-label">Uptime</div>
                  <div className="stat-value" style={{ fontSize: 15 }}>{fmtUptime(uptime)}</div>
                  <div className="stat-sub">session duration</div>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="card-header"><span className="card-title">System Health</span></div>
              <div className="health-body">
                <div className="health-item">
                  <div className={`health-dot ${wsColor}`} />
                  <div>
                    <div className="health-key">WebSocket</div>
                    <div className="health-val">{wsState} · {WS_BASE}/ws/ingest</div>
                  </div>
                </div>
                <div className="health-item">
                  <div className="health-dot green" />
                  <div>
                    <div className="health-key">Database: PostgreSQL</div>
                    <div className="health-val">Table: detected_faces · writing ROI</div>
                  </div>
                </div>
                <div className="health-item">
                  <div className="health-dot green" />
                  <div>
                    <div className="health-key">Face Model: MediaPipe</div>
                    <div className="health-val">Active · Non-OpenCV overlay</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* ── Center col ── */}
          <VideoFeed imgRef={streamImgRef} isLive={status === 'live'} latestRoi={latestRoi} className="fill" />

          {/* ── Right col ── */}
          <div className="right-col">
            <RoiPanel session={session} latestRoi={latestRoi} history={history} />
          </div>
        </div>

      </div>

      <video ref={videoRef} style={{ display: 'none' }} muted playsInline />
      <canvas ref={canvasRef} style={{ display: 'none' }} />
    </>
  );
}
