import { useCallback, useEffect, useRef, useState } from 'react';
import Viewport from './Viewport.jsx';
import { StreamSocket } from './ws.js';

const HEARTBEAT_MS = 5000;

const CONNECTION_LABEL = {
  connecting: 'Connecting…',
  connected: 'Connected',
  reconnecting: 'Reconnecting…',
  disconnected: 'Disconnected',
  busy: 'Session open in another tab',
};

const SESSION_LABEL = {
  idle: 'Blender not running',
  launching: 'Launching Blender…',
  running: 'Blender running',
  draining: 'Blender running',
  shutting_down: 'Blender shutting down…',
};

export default function App() {
  const [connection, setConnection] = useState('connecting');
  const [sessionState, setSessionState] = useState('idle');
  const [error, setError] = useState(null);
  const [fps, setFps] = useState(0);
  const [blenderExited, setBlenderExited] = useState(false);

  const socketRef = useRef(null);
  const viewportRef = useRef(null);
  const containerRef = useRef(null);
  const inputEnabled = useRef(false);

  const send = useCallback((msg) => socketRef.current?.send(msg), []);

  useEffect(() => {
    if (!('VideoDecoder' in window)) {
      setError('This browser lacks WebCodecs (VideoDecoder). Use Chrome, Arc, Edge, or Safari 16.4+.');
      return;
    }

    const socket = new StreamSocket({
      onFrame: (payload, keyframe, ptsUs) => {
        viewportRef.current?.pushFrame(payload, keyframe, ptsUs);
      },
      onJson: (msg) => {
        switch (msg.type) {
          case 'status':
            setSessionState(msg.state);
            if (msg.state === 'running') setBlenderExited(false);
            break;
          case 'stream_restart':
            viewportRef.current?.resetStream();
            break;
          case 'blender_exited':
            setBlenderExited(true);
            break;
          case 'error':
            setError(msg.message);
            break;
          default:
            break;
        }
      },
      onConnectionChange: setConnection,
    });
    socketRef.current = socket;
    socket.connect();

    const heartbeat = setInterval(() => socket.send({ type: 'ping' }), HEARTBEAT_MS);
    return () => {
      clearInterval(heartbeat);
      socket.close();
    };
  }, []);

  useEffect(() => {
    inputEnabled.current = connection === 'connected' && sessionState === 'running';
  }, [connection, sessionState]);

  const enterFullscreen = async () => {
    try {
      await containerRef.current?.requestFullscreen();
      // Keyboard lock (Chromium, fullscreen only) lets us capture browser
      // reserved shortcuts like Cmd+W so they reach Blender instead.
      await navigator.keyboard?.lock?.();
    } catch {
      /* unsupported browsers still get plain fullscreen */
    }
  };

  useEffect(() => {
    const onFsChange = () => {
      if (!document.fullscreenElement) navigator.keyboard?.unlock?.();
    };
    document.addEventListener('fullscreenchange', onFsChange);
    return () => document.removeEventListener('fullscreenchange', onFsChange);
  }, []);

  const relaunch = () => {
    setBlenderExited(false);
    setError(null);
    send({ type: 'launch' });
  };

  const showOverlay = blenderExited || error || connection !== 'connected' || sessionState !== 'running';

  return (
    <div className="app" ref={containerRef}>
      <header className="statusbar">
        <span className={`dot dot-${connection}`} />
        <span className="status-text">{CONNECTION_LABEL[connection] ?? connection}</span>
        <span className="divider">·</span>
        <span className="status-text">{SESSION_LABEL[sessionState] ?? sessionState}</span>
        <span className="spacer" />
        {fps > 0 && sessionState === 'running' && <span className="fps">{fps} fps</span>}
        <button className="btn" onClick={enterFullscreen} title="Fullscreen + capture all shortcuts (incl. Cmd+W)">
          Fullscreen
        </button>
      </header>

      <main className="stage">
        <Viewport ref={viewportRef} send={send} inputEnabled={inputEnabled} onStats={({ fps }) => setFps(fps)} />

        {showOverlay && (
          <div className="overlay">
            {error ? (
              <>
                <p className="overlay-title">Something went wrong</p>
                <p className="overlay-text">{error}</p>
                <button className="btn btn-primary" onClick={relaunch}>Retry</button>
              </>
            ) : blenderExited ? (
              <>
                <p className="overlay-title">Blender closed</p>
                <p className="overlay-text">The Blender session has ended.</p>
                <button className="btn btn-primary" onClick={relaunch}>Launch Blender</button>
              </>
            ) : sessionState === 'launching' ? (
              <>
                <div className="spinner" />
                <p className="overlay-text">Launching Blender…</p>
              </>
            ) : connection !== 'connected' ? (
              <>
                <div className="spinner" />
                <p className="overlay-text">{CONNECTION_LABEL[connection]}</p>
              </>
            ) : (
              <>
                <div className="spinner" />
                <p className="overlay-text">{SESSION_LABEL[sessionState]}</p>
              </>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
