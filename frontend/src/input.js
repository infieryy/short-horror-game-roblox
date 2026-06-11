// Captures browser input over the stream canvas and forwards it 1:1 to the
// session manager, which injects it into Blender's process. Keyboard events
// use `code` (physical key), so Blender's native keymap applies unchanged.

function modifiers(e) {
  return { shift: e.shiftKey, ctrl: e.ctrlKey, alt: e.altKey, meta: e.metaKey };
}

function normCoords(el, e) {
  const rect = el.getBoundingClientRect();
  return {
    x: Math.min(Math.max((e.clientX - rect.left) / rect.width, 0), 1),
    y: Math.min(Math.max((e.clientY - rect.top) / rect.height, 0), 1),
  };
}

export function attachInput(canvas, send, isEnabled) {
  let pendingMove = null;
  let moveScheduled = false;

  const flushMove = () => {
    moveScheduled = false;
    if (pendingMove) {
      send(pendingMove);
      pendingMove = null;
    }
  };

  const onPointerMove = (e) => {
    if (!isEnabled()) return;
    // Coalesce to one mouse_move per animation frame.
    pendingMove = { type: 'mouse_move', ...normCoords(canvas, e), modifiers: modifiers(e) };
    if (!moveScheduled) {
      moveScheduled = true;
      requestAnimationFrame(flushMove);
    }
  };

  const onPointerDown = (e) => {
    if (!isEnabled()) return;
    e.preventDefault();
    canvas.focus();
    // Keep receiving move/up events even when the pointer leaves the canvas
    // mid-drag (essential for Blender's drag-heavy interactions).
    canvas.setPointerCapture(e.pointerId);
    send({ type: 'mouse_down', button: e.button, ...normCoords(canvas, e), modifiers: modifiers(e) });
  };

  const onPointerUp = (e) => {
    if (!isEnabled()) return;
    e.preventDefault();
    send({ type: 'mouse_up', button: e.button, ...normCoords(canvas, e), modifiers: modifiers(e) });
  };

  const onWheel = (e) => {
    if (!isEnabled()) return;
    e.preventDefault();
    send({
      type: 'wheel',
      dx: e.deltaX,
      dy: e.deltaY,
      ...normCoords(canvas, e),
      modifiers: modifiers(e),
    });
  };

  const isUiTarget = (e) =>
    e.target instanceof HTMLInputElement ||
    e.target instanceof HTMLTextAreaElement ||
    e.target instanceof HTMLSelectElement;

  const onKeyDown = (e) => {
    if (!isEnabled() || isUiTarget(e)) return;
    // Block browser shortcuts (Cmd+S, Ctrl+R, space scrolling, ...). Browser
    // reserved combos (Cmd+W/T/N/Q) can only be captured in fullscreen with
    // keyboard lock -- see the fullscreen button.
    e.preventDefault();
    if (e.repeat) return; // Blender's OS-level key repeat handles this side
    send({ type: 'key_down', code: e.code, key: e.key, modifiers: modifiers(e) });
  };

  const onKeyUp = (e) => {
    if (!isEnabled() || isUiTarget(e)) return;
    e.preventDefault();
    send({ type: 'key_up', code: e.code, key: e.key, modifiers: modifiers(e) });
  };

  const onContextMenu = (e) => {
    if (isEnabled()) e.preventDefault();
  };

  canvas.addEventListener('pointermove', onPointerMove);
  canvas.addEventListener('pointerdown', onPointerDown);
  canvas.addEventListener('pointerup', onPointerUp);
  canvas.addEventListener('wheel', onWheel, { passive: false });
  canvas.addEventListener('contextmenu', onContextMenu);
  window.addEventListener('keydown', onKeyDown);
  window.addEventListener('keyup', onKeyUp);

  return () => {
    canvas.removeEventListener('pointermove', onPointerMove);
    canvas.removeEventListener('pointerdown', onPointerDown);
    canvas.removeEventListener('pointerup', onPointerUp);
    canvas.removeEventListener('wheel', onWheel);
    canvas.removeEventListener('contextmenu', onContextMenu);
    window.removeEventListener('keydown', onKeyDown);
    window.removeEventListener('keyup', onKeyUp);
  };
}
