import { forwardRef, useEffect, useImperativeHandle, useRef } from 'react';
import { attachInput } from './input';

// Renders the H.264 stream via WebCodecs (hardware decode) onto a canvas and
// forwards input. The stream is Annex B with in-band SPS/PPS, so the decoder
// needs no out-of-band description.

const Viewport = forwardRef(function Viewport({ send, inputEnabled, onStats }, ref) {
  const canvasRef = useRef(null);
  const ctxRef = useRef(null);
  const decoderRef = useRef(null);
  const waitingForKeyRef = useRef(true);
  const statsRef = useRef({ frames: 0, last: performance.now() });

  const resetDecoder = () => {
    const dec = decoderRef.current;
    decoderRef.current = null;
    waitingForKeyRef.current = true;
    if (dec && dec.state !== 'closed') {
      try {
        dec.close();
      } catch {
        /* already closed */
      }
    }
  };

  const ensureDecoder = () => {
    if (decoderRef.current && decoderRef.current.state === 'configured') {
      return decoderRef.current;
    }
    resetDecoder();
    const decoder = new VideoDecoder({
      output: (frame) => {
        const canvas = canvasRef.current;
        if (canvas) {
          if (canvas.width !== frame.displayWidth || canvas.height !== frame.displayHeight) {
            canvas.width = frame.displayWidth;
            canvas.height = frame.displayHeight;
            canvas.style.aspectRatio = `${frame.displayWidth} / ${frame.displayHeight}`;
            ctxRef.current = canvas.getContext('2d');
          }
          if (!ctxRef.current) ctxRef.current = canvas.getContext('2d');
          ctxRef.current.drawImage(frame, 0, 0);
        }
        frame.close();

        const stats = statsRef.current;
        stats.frames += 1;
        const now = performance.now();
        if (now - stats.last >= 1000) {
          onStats?.({ fps: Math.round((stats.frames * 1000) / (now - stats.last)) });
          stats.frames = 0;
          stats.last = now;
        }
      },
      error: (e) => {
        console.warn('decoder error, resetting:', e);
        resetDecoder();
        send({ type: 'request_keyframe' });
      },
    });
    decoder.configure({
      codec: 'avc1.640028', // H.264 High; Annex B in-band params override details
      optimizeForLatency: true,
      hardwareAcceleration: 'prefer-hardware',
    });
    decoderRef.current = decoder;
    waitingForKeyRef.current = true;
    return decoder;
  };

  useImperativeHandle(ref, () => ({
    pushFrame(payload, keyframe, ptsUs) {
      const decoder = ensureDecoder();
      if (waitingForKeyRef.current) {
        if (!keyframe) return;
        waitingForKeyRef.current = false;
      }
      try {
        decoder.decode(
          new EncodedVideoChunk({
            type: keyframe ? 'key' : 'delta',
            timestamp: ptsUs,
            data: payload,
          })
        );
      } catch (e) {
        console.warn('decode failed, resetting:', e);
        resetDecoder();
        send({ type: 'request_keyframe' });
      }
    },
    resetStream() {
      resetDecoder();
    },
  }));

  useEffect(() => {
    const canvas = canvasRef.current;
    const detach = attachInput(canvas, send, () => inputEnabled.current);
    return () => {
      detach();
      resetDecoder();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return <canvas ref={canvasRef} className="viewport" tabIndex={0} width={1280} height={720} />;
});

export default Viewport;
