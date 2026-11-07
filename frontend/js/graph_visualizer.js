/**
 * Kuber Data Core (कुबेर) — Interactive Force-Directed Knowledge Graph Visualizer
 * Canvas graph with node dragging, pan, zoom, and shock ripples.
 */

class KuberGraphVisualizer {
  constructor(canvasId, onNodeSelected) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext("2d");
    this.onNodeSelected = onNodeSelected;

    this.nodes = [];
    this.edges = [];
    this.nodeMap = new Map();

    // Pan & Zoom state
    this.scale = 1.0;
    this.panX = 0;
    this.panY = 0;
    this.isDragging = false;
    this.dragNode = null;
    this.hoverNode = null;
    this.width = 0;
    this.height = 0;
    this.motion = window.matchMedia("(prefers-reduced-motion: reduce)");
    this.dragStartX = 0;
    this.dragStartY = 0;

    // Shock animation state
    this.shockRipples = [];
    this.highlightedPathNodes = new Set();
    this.renderFrame = null;
    this.physicsTicks = 0;

    this._setupCanvasSize();
    this._attachEventListeners();
  }

  _setupCanvasSize() {
    const width = this.canvas.clientWidth;
    const height = this.canvas.clientHeight;
    if (!width || !height) return;

    const fitView = this.scale === this._fitScale();
    this.panX += (width - this.width) / 2;
    this.panY += (height - this.height) / 2;
    this.width = width;
    this.height = height;
    if (fitView) this.scale = this._fitScale();
    const pixelRatio = Math.min(2, window.devicePixelRatio || 1);
    this.canvas.width = Math.round(width * pixelRatio);
    this.canvas.height = Math.round(height * pixelRatio);
    this.ctx.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
    this._render();
    if (this.physicsTicks || this.shockRipples.length) this._queueRender();
  }

  highlightPath(pathNodeIds) {
    this.highlightedPathNodes = new Set(pathNodeIds || []);
    if (pathNodeIds && pathNodeIds.length > 0) {
      const first = this.nodeMap.get(pathNodeIds[0]);
      if (first) {
        this.panX = this.width / 2 - first.x * this.scale;
        this.panY = this.height / 2 - first.y * this.scale;
      }
    }
    this._queueRender();
  }

  loadGraphData(graphView) {
    this.nodeMap.clear();

    // Arrange nodes in radial force circle initially
    const count = graphView.nodes.length;
    this.nodes = graphView.nodes.map((n, i) => {
      const angle = (i / count) * Math.PI * 2;
      const radius = 180 + (i % 2 === 0 ? 40 : -40);
      const nodeObj = {
        id: n.id,
        label: n.label,
        type: n.type,
        ticker: n.ticker,
        sector: n.sector,
        market_cap_b: n.market_cap_b,
        pagerank: n.pagerank,
        degree: n.degree,
        x: Math.cos(angle) * radius,
        y: Math.sin(angle) * radius,
        vx: 0,
        vy: 0,
        radius: Math.max(14, Math.min(32, Math.sqrt(n.market_cap_b || 100) * 0.45)),
        color: this._getNodeColor(n)
      };
      this.nodeMap.set(n.id, nodeObj);
      return nodeObj;
    });

    this.edges = graphView.edges.map(e => ({
      id: e.id,
      sourceId: e.source,
      targetId: e.target,
      relation: e.relation,
      weight: e.weight ?? 1.0,
      description: e.description,
      source: this.nodeMap.get(e.source),
      target: this.nodeMap.get(e.target)
    })).filter(e => e.source && e.target);
    if (this.motion.matches) {
      for (let frame = 0; frame < 100; frame++) this._updatePhysics();
    }
    this._queueRender(this.motion.matches ? 0 : 160);
  }

  _getNodeColor(node) {
    if (node.type === "EXECUTIVE") return "#bbb0d1";
    if (node.ticker === "TSM" || node.ticker === "ASML") return "#e1ad88";
    if (node.ticker === "NVDA" || node.ticker === "AMD" || node.ticker === "AVGO") return "#a7c5b3";
    return "#d4b6af";
  }

  triggerShockAnimation(shockSourceId) {
    const src = this.nodeMap.get(shockSourceId);
    if (!src || this.motion.matches) return;

    this.shockRipples.push({
      x: src.x,
      y: src.y,
      radius: 10,
      alpha: 1.0
    });
    this._queueRender();
  }

  _attachEventListeners() {
    window.addEventListener("resize", () => this._setupCanvasSize());
    this.motion.addEventListener("change", () => this._queueRender());
    document.addEventListener("visibilitychange", () => {
      if (this.physicsTicks || this.shockRipples.length) this._queueRender();
    });

    this.canvas.addEventListener("pointerdown", event => {
      if (!event.isPrimary || event.button !== 0) return;
      this.canvas.setPointerCapture(event.pointerId);
      const point = this._getCanvasCoords(event);
      const node = this._findNodeAt(point.x, point.y);
      if (node) {
        this.dragNode = node;
        this.onNodeSelected?.(node);
      } else {
        this.isDragging = true;
        this.dragStartX = event.clientX - this.panX;
        this.dragStartY = event.clientY - this.panY;
      }
    });

    this.canvas.addEventListener("pointermove", event => {
      if (!event.isPrimary) return;
      const point = this._getCanvasCoords(event);
      if (this.dragNode) {
        this.dragNode.x = point.x;
        this.dragNode.y = point.y;
        this.dragNode.vx = 0;
        this.dragNode.vy = 0;
      } else if (this.isDragging) {
        this.panX = event.clientX - this.dragStartX;
        this.panY = event.clientY - this.dragStartY;
      } else {
        const hovered = this._findNodeAt(point.x, point.y);
        if (hovered === this.hoverNode) return;
        this.hoverNode = hovered;
      }
      this._queueRender();
    });

    this.canvas.addEventListener("pointerleave", () => {
      if (this.hoverNode) {
        this.hoverNode = null;
        this._queueRender();
      }
    });
    this.canvas.addEventListener("lostpointercapture", event => {
      if (!event.isPrimary) return;
      const movedNode = this.dragNode;
      this.dragNode = null;
      this.isDragging = false;
      if (movedNode) this._queueRender(120);
    });

    this.canvas.addEventListener("wheel", event => {
      if (!event.ctrlKey && !event.metaKey) return;
      event.preventDefault();
      this.zoomBy(event.deltaY < 0 ? 1.1 : 0.9, this._getCanvasCoords(event));
    }, { passive: false });
  }

  _getCanvasCoords(e) {
    const rect = this.canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    return {
      x: (mouseX - this.panX) / this.scale,
      y: (mouseY - this.panY) / this.scale
    };
  }

  _findNodeAt(x, y) {
    for (let i = this.nodes.length - 1; i >= 0; i--) {
      const n = this.nodes[i];
      const dist = Math.hypot(n.x - x, n.y - y);
      if (dist <= n.radius + 6) return n;
    }
    return null;
  }

  _queueRender(physicsTicks = 0) {
    this.physicsTicks = Math.max(this.physicsTicks, physicsTicks);
    if (this.renderFrame !== null || document.hidden || !this.canvas.clientWidth) return;

    this.renderFrame = requestAnimationFrame(() => {
      this.renderFrame = null;
      if (document.hidden || !this.canvas.clientWidth) return;

      if (this.motion.matches) {
        this.physicsTicks = 0;
        this.shockRipples.length = 0;
      } else if (this.physicsTicks > 0) {
        this._updatePhysics();
        this.physicsTicks--;
      }
      this._render();
      if (this.physicsTicks || this.shockRipples.length) this._queueRender();
    });
  }

  _updatePhysics() {
    // Basic force repulsion & spring attraction
    const repulsion = 1200;
    const springLength = 140;
    const springK = 0.003;
    const damping = 0.88;

    for (let i = 0; i < this.nodes.length; i++) {
      const n1 = this.nodes[i];
      if (n1 === this.dragNode) continue;

      // Center gravity
      n1.vx -= n1.x * 0.0006;
      n1.vy -= n1.y * 0.0006;

      for (let j = i + 1; j < this.nodes.length; j++) {
        const n2 = this.nodes[j];
        const dx = n2.x - n1.x;
        const dy = n2.y - n1.y;
        const dist = Math.hypot(dx, dy) || 1;
        if (dist < 400) {
          const force = repulsion / (dist * dist);
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          n1.vx -= fx;
          n1.vy -= fy;
          n2.vx += fx;
          n2.vy += fy;
        }
      }
    }

    // Springs along edges
    for (const e of this.edges) {
      const dx = e.target.x - e.source.x;
      const dy = e.target.y - e.source.y;
      const dist = Math.hypot(dx, dy) || 1;
      const displacement = dist - springLength;
      const force = displacement * springK;
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;

      if (e.source !== this.dragNode) {
        e.source.vx += fx;
        e.source.vy += fy;
      }
      if (e.target !== this.dragNode) {
        e.target.vx -= fx;
        e.target.vy -= fy;
      }
    }

    // Apply velocities
    for (const n of this.nodes) {
      if (n === this.dragNode) continue;
      n.vx *= damping;
      n.vy *= damping;
      n.x += n.vx;
      n.y += n.vy;
    }
  }

  _render() {
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.width, this.height);

    ctx.save();
    ctx.translate(this.panX, this.panY);
    ctx.scale(this.scale, this.scale);

    // 1. Draw Shock Ripples
    for (let i = this.shockRipples.length - 1; i >= 0; i--) {
      const rip = this.shockRipples[i];
      ctx.beginPath();
      ctx.arc(rip.x, rip.y, rip.radius, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(225, 131, 133, ${rip.alpha})`;
      ctx.lineWidth = 3;
      ctx.stroke();

      rip.radius += 2.5;
      rip.alpha -= 0.015;
      if (rip.alpha <= 0) {
        this.shockRipples.splice(i, 1);
      }
    }

    // 2. Draw Edges
    for (const e of this.edges) {
      const isPathEdge = this.highlightedPathNodes.has(e.source.id) && this.highlightedPathNodes.has(e.target.id);

      ctx.beginPath();
      ctx.moveTo(e.source.x, e.source.y);
      ctx.lineTo(e.target.x, e.target.y);

      if (isPathEdge) {
        ctx.strokeStyle = "#f2bf99";
        ctx.lineWidth = 3.5;
      } else {
        ctx.strokeStyle = e.relation === "COMPETES_WITH" ? "rgba(225, 131, 133, 0.4)" : "rgba(216, 176, 157, 0.38)";
        ctx.lineWidth = Math.max(1, e.weight * 2);
      }
      ctx.stroke();

      // Arrow indicator
      const midX = (e.source.x + e.target.x) / 2;
      const midY = (e.source.y + e.target.y) / 2;
      const angle = Math.atan2(e.target.y - e.source.y, e.target.x - e.source.x);
      ctx.save();
      ctx.translate(midX, midY);
      ctx.rotate(angle);
      ctx.beginPath();
      ctx.moveTo(-7, -4.5);
      ctx.lineTo(5, 0);
      ctx.lineTo(-7, 4.5);
      ctx.fillStyle = ctx.strokeStyle;
      ctx.fill();
      ctx.restore();
    }

    // 3. Draw Nodes
    for (const n of this.nodes) {
      const isPathNode = this.highlightedPathNodes.has(n.id);

      // Path highlight aura
      if (isPathNode) {
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius + 10, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(242, 191, 153, 0.35)";
        ctx.fill();
      }

      // Hover / Default Glow
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.radius + 4, 0, Math.PI * 2);
      ctx.fillStyle = n === this.hoverNode ? "rgba(255, 255, 255, 0.35)" : (isPathNode ? "rgba(242, 191, 153, 0.2)" : "rgba(0, 0, 0, 0.5)");
      ctx.fill();

      // Core
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
      ctx.fillStyle = n.color;
      ctx.fill();
      ctx.strokeStyle = isPathNode ? "#f2bf99" : "#fff";
      ctx.lineWidth = isPathNode ? 2.5 : 1.5;
      ctx.stroke();

      // Label
      ctx.font = '600 11px ui-monospace, SFMono-Regular, "JetBrains Mono", Consolas, monospace';
      ctx.fillStyle = "#2b202a";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      const displayText = n.ticker || n.label.split(" ")[0];
      ctx.fillText(displayText, n.x, n.y, n.radius * 1.72);
    }

    ctx.restore();
  }

  zoomBy(factor, point = {
    x: (this.width / 2 - this.panX) / this.scale,
    y: (this.height / 2 - this.panY) / this.scale,
  }) {
    const scale = Math.min(3, Math.max(0.4, this.scale * factor));
    this.panX += point.x * (this.scale - scale);
    this.panY += point.y * (this.scale - scale);
    this.scale = scale;
    this._queueRender();
  }

  _fitScale() {
    if (!this.width || !this.height) return 1;
    return Math.min(1, this.width / 510, this.height / 510);
  }

  resetZoom() {
    this.scale = this._fitScale();
    this.panX = this.width / 2;
    this.panY = this.height / 2;
    this._queueRender();
  }
}
