/**
 * DRAW & DECEIVE - Real-Time HTML5 Canvas Engine
 * High-DPI, Pointer Events, Multi-tool Drawing with Coordinate Normalization.
 */

class DrawingEngine {
  constructor(canvasElement, socket, options = {}) {
    this.canvas = canvasElement;
    this.ctx = canvasElement.getContext('2d');
    this.socket = socket;

    // Logical dimensions (consistent across all devices)
    this.LOGICAL_WIDTH = 800;
    this.LOGICAL_HEIGHT = 600;

    // Drawing state
    this.isDrawing = false;
    this.canDraw = options.canDraw || false;
    this.currentTool = 'brush';       // brush, eraser, line, rect, circle
    this.currentColor = '#000000';
    this.brushSize = 4;

    // Current stroke being drawn locally
    this.currentStroke = null;
    this.strokeBuffer = [];
    this.batchTimer = null;

    // Stroke history for replay & undo
    this.strokes = []; // Array of stroke objects

    // Preview canvas / snapshot for shape tools (line, rect, circle)
    this.previewSnapshot = null;

    this.initCanvasResolution();
    this.bindEvents();

    window.addEventListener('resize', () => this.handleResize());
  }

  setCanDraw(canDraw) {
    this.canDraw = canDraw;
    if (canDraw) {
      this.canvas.classList.remove('disabled');
    } else {
      this.canvas.classList.add('disabled');
      this.isDrawing = false;
    }
  }

  initCanvasResolution() {
    const dpr = window.devicePixelRatio || 1;
    this.canvas.width = this.LOGICAL_WIDTH * dpr;
    this.canvas.height = this.LOGICAL_HEIGHT * dpr;
    this.ctx.scale(dpr, dpr);
    this.ctx.lineCap = 'round';
    this.ctx.lineJoin = 'round';
    this.redrawAll();
  }

  handleResize() {
    // Re-verify canvas display bounds without changing logical scale
  }

  getLogicalCoords(e) {
    const rect = this.canvas.getBoundingClientRect();
    const scaleX = this.LOGICAL_WIDTH / rect.width;
    const scaleY = this.LOGICAL_HEIGHT / rect.height;
    return {
      x: Math.round((e.clientX - rect.left) * scaleX),
      y: Math.round((e.clientY - rect.top) * scaleY),
    };
  }

  bindEvents() {
    this.canvas.addEventListener('pointerdown', (e) => this.onPointerDown(e));
    this.canvas.addEventListener('pointermove', (e) => this.onPointerMove(e));
    this.canvas.addEventListener('pointerup', (e) => this.onPointerUp(e));
    this.canvas.addEventListener('pointercancel', (e) => this.onPointerUp(e));

    // Keyboard shortcuts
    window.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z') {
        if (this.canDraw) {
          e.preventDefault();
          this.triggerUndo();
        }
      }
    });
  }

  onPointerDown(e) {
    if (!this.canDraw) return;
    this.canvas.setPointerCapture(e.pointerId);

    const coords = this.getLogicalCoords(e);
    this.isDrawing = true;

    const strokeId = 's_' + Date.now() + '_' + Math.random().toString(36).substring(2, 7);

    this.currentStroke = {
      stroke_id: strokeId,
      tool_type: this.currentTool,
      color: this.currentTool === 'eraser' ? '#ffffff' : this.currentColor,
      brush_size: this.brushSize,
      points: [coords],
    };

    // Save snapshot for shapes preview
    if (['line', 'rect', 'circle'].includes(this.currentTool)) {
      this.previewSnapshot = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
    }

    // Begin local draw
    this.ctx.beginPath();
    this.ctx.strokeStyle = this.currentStroke.color;
    this.ctx.lineWidth = this.currentStroke.brush_size;

    if (this.currentTool === 'brush' || this.currentTool === 'eraser') {
      this.ctx.moveTo(coords.x, coords.y);
      this.ctx.lineTo(coords.x + 0.1, coords.y + 0.1);
      this.ctx.stroke();
    }

    this.strokeBuffer = [coords];
    this.startBatching(strokeId);
  }

  onPointerMove(e) {
    if (!this.isDrawing || !this.canDraw || !this.currentStroke) return;

    const coords = this.getLogicalCoords(e);
    const pts = this.currentStroke.points;
    const lastPoint = pts[pts.length - 1];

    // Distance check to avoid zero-delta points
    const dist = Math.hypot(coords.x - lastPoint.x, coords.y - lastPoint.y);
    if (dist < 1.5 && this.currentTool !== 'line' && this.currentTool !== 'rect' && this.currentTool !== 'circle') {
      return;
    }

    if (this.currentTool === 'brush' || this.currentTool === 'eraser') {
      this.ctx.beginPath();
      this.ctx.moveTo(lastPoint.x, lastPoint.y);
      this.ctx.lineTo(coords.x, coords.y);
      this.ctx.stroke();

      pts.push(coords);
      this.strokeBuffer.push(coords);
    } else if (['line', 'rect', 'circle'].includes(this.currentTool)) {
      // Restore snapshot then draw preview shape
      if (this.previewSnapshot) {
        this.ctx.putImageData(this.previewSnapshot, 0, 0);
      }
      this.drawShape(this.currentTool, pts[0], coords, this.currentStroke.color, this.currentStroke.brush_size);
      // Keep only start & current point
      this.currentStroke.points = [pts[0], coords];
    }
  }

  onPointerUp(e) {
    if (!this.isDrawing) return;
    this.isDrawing = false;

    if (e.pointerId && this.canvas.hasPointerCapture(e.pointerId)) {
      this.canvas.releasePointerCapture(e.pointerId);
    }

    if (this.currentStroke) {
      this.flushBatch(this.currentStroke.stroke_id);
      this.strokes.push(this.currentStroke);

      // Play soft feedback sound
      if (window.soundFx) {
        window.soundFx.playPop();
      }
    }

    this.currentStroke = null;
    this.previewSnapshot = null;
    this.stopBatching();
  }

  startBatching(strokeId) {
    this.stopBatching();
    this.batchTimer = setInterval(() => {
      this.flushBatch(strokeId);
    }, 28); // ~35 updates/sec batching
  }

  stopBatching() {
    if (this.batchTimer) {
      clearInterval(this.batchTimer);
      this.batchTimer = null;
    }
  }

  flushBatch(strokeId) {
    if (!this.currentStroke) return;

    let pointsToSend = [];
    if (['line', 'rect', 'circle'].includes(this.currentTool)) {
      pointsToSend = this.currentStroke.points;
    } else if (this.strokeBuffer.length > 0) {
      pointsToSend = [...this.strokeBuffer];
      this.strokeBuffer = [];
    }

    if (pointsToSend.length > 0 && this.socket) {
      this.socket.send('drawing.stroke', {
        stroke_id: strokeId,
        tool_type: this.currentStroke.tool_type,
        color: this.currentStroke.color,
        brush_size: this.currentStroke.brush_size,
        points: pointsToSend,
      });
    }
  }

  drawShape(tool, start, end, color, size) {
    this.ctx.beginPath();
    this.ctx.strokeStyle = color;
    this.ctx.lineWidth = size;

    if (tool === 'line') {
      this.ctx.moveTo(start.x, start.y);
      this.ctx.lineTo(end.x, end.y);
      this.ctx.stroke();
    } else if (tool === 'rect') {
      const x = Math.min(start.x, end.x);
      const y = Math.min(start.y, end.y);
      const w = Math.abs(end.x - start.x);
      const h = Math.abs(end.y - start.y);
      this.ctx.strokeRect(x, y, w, h);
    } else if (tool === 'circle') {
      const rx = Math.abs(end.x - start.x) / 2;
      const ry = Math.abs(end.y - start.y) / 2;
      const cx = Math.min(start.x, end.x) + rx;
      const cy = Math.min(start.y, end.y) + ry;
      this.ctx.beginPath();
      this.ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2);
      this.ctx.stroke();
    }
  }

  // Render a stroke received from a remote drawer
  renderRemoteStroke(strokeData) {
    const { stroke_id, tool_type, color, brush_size, points } = strokeData;
    if (!points || points.length === 0) return;

    let existing = this.strokes.find((s) => s.stroke_id === stroke_id);
    if (!existing) {
      existing = {
        stroke_id,
        tool_type,
        color,
        brush_size,
        points: [],
      };
      this.strokes.push(existing);
    }

    if (['line', 'rect', 'circle'].includes(tool_type)) {
      existing.points = points;
      this.redrawAll();
      return;
    }

    // Incremental segment draw for brush/eraser
    this.ctx.beginPath();
    this.ctx.strokeStyle = color;
    this.ctx.lineWidth = brush_size;

    const startIndex = existing.points.length;
    existing.points.push(...points);

    if (startIndex === 0) {
      this.ctx.moveTo(points[0].x, points[0].y);
      this.ctx.lineTo(points[0].x + 0.1, points[0].y + 0.1);
      this.ctx.stroke();
    } else {
      const prev = existing.points[startIndex - 1];
      this.ctx.moveTo(prev.x, prev.y);
      for (const p of points) {
        this.ctx.lineTo(p.x, p.y);
      }
      this.ctx.stroke();
    }
  }

  redrawAll() {
    // Clear surface to crisp white
    this.ctx.fillStyle = '#ffffff';
    this.ctx.fillRect(0, 0, this.LOGICAL_WIDTH, this.LOGICAL_HEIGHT);

    // Draw all active strokes
    for (const stroke of this.strokes) {
      if (stroke.is_undone) continue;
      const { tool_type, color, brush_size, points } = stroke;
      if (!points || points.length === 0) continue;

      if (['line', 'rect', 'circle'].includes(tool_type)) {
        if (points.length >= 2) {
          this.drawShape(tool_type, points[0], points[1], color, brush_size);
        }
      } else {
        this.ctx.beginPath();
        this.ctx.strokeStyle = color;
        this.ctx.lineWidth = brush_size;
        this.ctx.moveTo(points[0].x, points[0].y);

        if (points.length === 1) {
          this.ctx.lineTo(points[0].x + 0.1, points[0].y + 0.1);
        } else {
          for (let i = 1; i < points.length; i++) {
            this.ctx.lineTo(points[i].x, points[i].y);
          }
        }
        this.ctx.stroke();
      }
    }
  }

  loadStrokes(strokeList) {
    this.strokes = strokeList || [];
    this.redrawAll();
  }

  triggerUndo() {
    if (!this.canDraw) return;
    this.socket.send('drawing.undo', {});
  }

  undoStroke(strokeId) {
    const stroke = this.strokes.find((s) => s.stroke_id === strokeId);
    if (stroke) {
      stroke.is_undone = true;
    } else if (this.strokes.length > 0) {
      // Find last active
      for (let i = this.strokes.length - 1; i >= 0; i--) {
        if (!this.strokes[i].is_undone) {
          this.strokes[i].is_undone = true;
          break;
        }
      }
    }
    this.redrawAll();
  }

  triggerClear() {
    if (!this.canDraw) return;
    if (confirm("Clear the entire canvas? This cannot be undone.")) {
      this.socket.send('drawing.clear', {});
      this.clearCanvas();
    }
  }

  clearCanvas() {
    this.strokes = [];
    this.ctx.fillStyle = '#ffffff';
    this.ctx.fillRect(0, 0, this.LOGICAL_WIDTH, this.LOGICAL_HEIGHT);
  }
}

window.DrawingEngine = DrawingEngine;
