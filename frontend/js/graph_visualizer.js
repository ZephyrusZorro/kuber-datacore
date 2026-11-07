/**
 * Kuber Data Core (कुबेर) — Interactive Force-Directed Knowledge Graph Visualizer
 * Pure HTML5 Canvas physics engine with node dragging, pan/zoom, edge particle flow,
 * and systemic shock ripple animations.
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
    this.dragStartX = 0;
    this.dragStartY = 0;

    // Shock animation state
    this.shockRipples = [];
    this.highlightedPathNodes = new Set();

    this._setupCanvasSize();
    this._attachEventListeners();
    this._startAnimationLoop();
  }

  _setupCanvasSize() {
    if (!this.canvas || !this.canvas.parentElement) return;
    const parent = this.canvas.parentElement;
    const rect = parent.getBoundingClientRect();
    const w = rect.width > 50 ? rect.width : (parent.clientWidth || 800);
    const h = rect.height > 50 ? rect.height : (parent.clientHeight || 640);
    this.canvas.width = w;
    this.canvas.height = h;
    this.panX = w / 2;
    this.panY = h / 2;
  }

  highlightPath(pathNodeIds) {
    this.highlightedPathNodes = new Set(pathNodeIds || []);
    if (pathNodeIds && pathNodeIds.length > 0) {
      const first = this.nodeMap.get(pathNodeIds[0]);
      if (first) {
        this.panX = this.canvas.width / 2 - first.x * this.scale;
        this.panY = this.canvas.height / 2 - first.y * this.scale;
      }
    }
  }

  loadGraphData(graphView) {
    this.nodeMap.clear();
    const width = this.canvas.width;
    const height = this.canvas.height;

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
      weight: e.weight || 1.0,
      description: e.description,
      source: this.nodeMap.get(e.source),
      target: this.nodeMap.get(e.target)
    })).filter(e => e.source && e.target);
  }

  _getNodeColor(node) {
    if (node.type === "EXECUTIVE") return "#c084fc"; // Purple
    if (node.ticker === "TSM" || node.ticker === "ASML") return "#facc15"; // Gold (Foundry / Lithography)
    if (node.ticker === "NVDA" || node.ticker === "AMD" || node.ticker === "AVGO") return "#38bdf8"; // Cyan (AI Silicon)
    return "#10b981"; // Emerald (Cloud & Platforms)
  }

  triggerShockAnimation(shockSourceId, magnitudePct) {
    const src = this.nodeMap.get(shockSourceId);
    if (!src) return;

    this.shockRipples.push({
      x: src.x,
      y: src.y,
      radius: 10,
      maxRadius: 180,
      alpha: 1.0,
      color: "#f43f5e"
    });
  }

  _attachEventListeners() {
    window.addEventListener("resize", () => this._setupCanvasSize());

    this.canvas.addEventListener("mousedown", (e) => {
      const pos = this._getCanvasCoords(e);
      const clicked = this._findNodeAt(pos.x, pos.y);
      if (clicked) {
        this.dragNode = clicked;
        if (this.onNodeSelected) this.onNodeSelected(clicked);
      } else {
        this.isDragging = true;
        this.dragStartX = e.clientX - this.panX;
        this.dragStartY = e.clientY - this.panY;
      }
    });

    window.addEventListener("mousemove", (e) => {
      if (!this.dragNode && !this.isDragging) {
        const rect = this.canvas.getBoundingClientRect();
        if (e.clientX < rect.left || e.clientX > rect.right || e.clientY < rect.top || e.clientY > rect.bottom) {
          this.hoverNode = null;
          return;
        }
      }

      const pos = this._getCanvasCoords(e);
      if (this.dragNode) {
        this.dragNode.x = pos.x;
        this.dragNode.y = pos.y;
        this.dragNode.vx = 0;
        this.dragNode.vy = 0;
      } else if (this.isDragging) {
        this.panX = e.clientX - this.dragStartX;
        this.panY = e.clientY - this.dragStartY;
      } else {
        this.hoverNode = this._findNodeAt(pos.x, pos.y);
      }
    });

    window.addEventListener("mouseup", () => {
      this.dragNode = null;
      this.isDragging = false;
    });

    this.canvas.addEventListener("wheel", (e) => {
      e.preventDefault();
      const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
      this.scale = Math.min(3.0, Math.max(0.4, this.scale * zoomFactor));
    });
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

  _startAnimationLoop() {
    const step = () => {
      this._updatePhysics();
      this._render();
      requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
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
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    ctx.save();
    ctx.translate(this.panX, this.panY);
    ctx.scale(this.scale, this.scale);

    // 1. Draw Shock Ripples
    for (let i = this.shockRipples.length - 1; i >= 0; i--) {
      const rip = this.shockRipples[i];
      ctx.beginPath();
      ctx.arc(rip.x, rip.y, rip.radius, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(244, 63, 94, ${rip.alpha})`;
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
        ctx.strokeStyle = "#facc15";
        ctx.lineWidth = 3.5;
      } else {
        ctx.strokeStyle = e.relation === "COMPETES_WITH" ? "rgba(244, 63, 94, 0.4)" : "rgba(234, 179, 8, 0.35)";
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
        ctx.fillStyle = "rgba(250, 204, 21, 0.35)";
        ctx.fill();
      }

      // Hover / Default Glow
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.radius + 4, 0, Math.PI * 2);
      ctx.fillStyle = n === this.hoverNode ? "rgba(255, 255, 255, 0.35)" : (isPathNode ? "rgba(250, 204, 21, 0.2)" : "rgba(0, 0, 0, 0.5)");
      ctx.fill();

      // Core
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
      ctx.fillStyle = n.color;
      ctx.fill();
      ctx.strokeStyle = isPathNode ? "#facc15" : "#fff";
      ctx.lineWidth = isPathNode ? 2.5 : 1.5;
      ctx.stroke();

      // Label
      ctx.font = '600 11px ui-monospace, SFMono-Regular, "JetBrains Mono", Consolas, monospace';
      ctx.fillStyle = "#fff";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      const displayText = n.ticker || n.label.split(" ")[0];
      ctx.fillText(displayText, n.x, n.y);
    }

    ctx.restore();
  }

  resetZoom() {
    this.scale = 1.0;
    this.panX = this.canvas.width / 2;
    this.panY = this.canvas.height / 2;
  }
}
