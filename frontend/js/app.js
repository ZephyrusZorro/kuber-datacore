/**
 * Kuber Data Core (कुबेर) — Main Frontend Workstation Controller
 * Manages Workspaces, Graph Visualizer, Autonomous DAG Runner, Crawl4AI DOM Pruner,
 * EDI Natural Language SQL Console, and Quantitative Valuation Matrix.
 */

// Global State
const state = {
  currentTab: "ws-graph",
  graphView: null,
  visualizer: null,
  selectedNode: null,
  activePipelineId: "financial-cortex-e2e",
  selectedTicker: "NVDA"
};

// DOM Element Registry
const el = {};

document.addEventListener("DOMContentLoaded", () => {
  initElementRegistry();
  initNavigationTabs();
  initMarketTickerTape();
  initGraphWorkspace();
  initDAGWorkspace();
  initCrawlerWorkspace();
  initEDIWorkspace();
  initValuationWorkspace();
});

function initElementRegistry() {
  el.tabBtns = document.querySelectorAll(".ws-tab-btn");
  el.panels = document.querySelectorAll(".workspace-panel");
  el.tickerTapeTrack = document.getElementById("tickerTapeTrack");

  // Graph Elements
  el.graphNodeDetail = document.getElementById("graphNodeDetail");
  el.pathSourceSelect = document.getElementById("pathSourceSelect");
  el.pathTargetSelect = document.getElementById("pathTargetSelect");
  el.btnFindPath = document.getElementById("btnFindPath");
  el.pathResultBox = document.getElementById("pathResultBox");
  el.shockSourceSelect = document.getElementById("shockSourceSelect");
  el.shockMagnitudeSlider = document.getElementById("shockMagnitudeSlider");
  el.shockMagnitudeVal = document.getElementById("shockMagnitudeVal");
  el.btnSimulateShock = document.getElementById("btnSimulateShock");
  el.shockResultBox = document.getElementById("shockResultBox");
  el.btnResetZoom = document.getElementById("btnResetZoom");

  // DAG Elements
  el.dagPipelineSelect = document.getElementById("dagPipelineSelect");
  el.btnRunDAG = document.getElementById("btnRunDAG");
  el.dagFlowSteps = document.getElementById("dagFlowSteps");
  el.dagLogStream = document.getElementById("dagLogStream");
  el.dagExecutiveBrief = document.getElementById("dagExecutiveBrief");

  // Crawler Elements
  el.crawlUrlInput = document.getElementById("crawlUrlInput");
  el.pruneStrategySelect = document.getElementById("pruneStrategySelect");
  el.btnExecuteCrawl = document.getElementById("btnExecuteCrawl");
  el.crawlRawChars = document.getElementById("crawlRawChars");
  el.crawlCleanChars = document.getElementById("crawlCleanChars");
  el.crawlCompressionBadge = document.getElementById("crawlCompressionBadge");
  el.crawlMarkdownPreview = document.getElementById("crawlMarkdownPreview");

  // EDI Elements
  el.ediQueryInput = document.getElementById("ediQueryInput");
  el.btnRunEDI = document.getElementById("btnRunEDI");
  el.ediAnswerText = document.getElementById("ediAnswerText");
  el.ediSqlCode = document.getElementById("ediSqlCode");
  el.ediCypherCode = document.getElementById("ediCypherCode");
  el.ediLatencyBadge = document.getElementById("ediLatencyBadge");
  el.ediTableHead = document.getElementById("ediTableHead");
  el.ediTableBody = document.getElementById("ediTableBody");
  el.quickPromptChips = document.querySelectorAll(".quick-prompt-chip");

  // Valuation Elements
  el.valTickerSelect = document.getElementById("valTickerSelect");
  el.valHealthGrade = document.getElementById("valHealthGrade");
  el.valAltmanScore = document.getElementById("valAltmanScore");
  el.valAltmanZone = document.getElementById("valAltmanZone");
  el.valAltmanPointer = document.getElementById("valAltmanPointer");
  el.valAltmanInterp = document.getElementById("valAltmanInterp");
  el.valBeneishScore = document.getElementById("valBeneishScore");
  el.valBeneishRisk = document.getElementById("valBeneishRisk");
  el.valGrossMargin = document.getElementById("valGrossMargin");
  el.valOperatingMargin = document.getElementById("valOperatingMargin");
  el.valCurrentRatio = document.getElementById("valCurrentRatio");
  el.valDebtEquity = document.getElementById("valDebtEquity");
  el.valPeRatio = document.getElementById("valPeRatio");
}

/* --- Navigation --- */
function initNavigationTabs() {
  el.tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetId = btn.dataset.tab;
      el.tabBtns.forEach(b => b.classList.remove("active"));
      el.panels.forEach(p => p.classList.remove("active"));

      btn.classList.add("active");
      const targetPanel = document.getElementById(targetId);
      if (targetPanel) targetPanel.classList.add("active");
      state.currentTab = targetId;

      if (targetId === "ws-graph" && state.visualizer) {
        setTimeout(() => state.visualizer._setupCanvasSize(), 50);
      }
    });
  });
}

/* --- Live Market Ticker Tape --- */
async function initMarketTickerTape() {
  try {
    const res = await fetch("/api/financials/tickers");
    if (!res.ok) return;
    const tickers = await res.json();

    const tickerHTML = tickers.map(t => {
      const isUp = t.change_dollar >= 0;
      const sign = isUp ? "+" : "";
      const cssClass = isUp ? "ticker-up" : "ticker-down";
      return `
        <div class="ticker-item">
          <span class="ticker-symbol">${t.ticker}</span>
          <span class="ticker-price">$${t.price.toFixed(2)}</span>
          <span class="${cssClass}">${sign}${t.change_pct.toFixed(2)}%</span>
        </div>
      `;
    }).join("");

    // Duplicate for smooth seamless loop
    el.tickerTapeTrack.innerHTML = tickerHTML + tickerHTML;
  } catch (err) {
    console.error("Ticker tape fetch failed:", err);
  }
}

/* --- Workspace 1: Knowledge Graph & Contagion --- */
async function initGraphWorkspace() {
  state.visualizer = new KuberGraphVisualizer("graphCanvas", (node) => {
    renderNodeDetail(node);
  });

  if (el.btnResetZoom) {
    el.btnResetZoom.addEventListener("click", () => state.visualizer.resetZoom());
  }

  // Load Graph Data
  await refreshGraphData();

  // Shortest Path Button
  if (el.btnFindPath) {
    el.btnFindPath.addEventListener("click", executeShortestPath);
  }

  // Shock Magnitude Slider
  if (el.shockMagnitudeSlider) {
    el.shockMagnitudeSlider.addEventListener("input", (e) => {
      el.shockMagnitudeVal.textContent = `${e.target.value}%`;
    });
  }

  // Simulate Shock Button
  if (el.btnSimulateShock) {
    el.btnSimulateShock.addEventListener("click", executeContagionSimulation);
  }
}

async function refreshGraphData() {
  try {
    const res = await fetch("/api/graph/view");
    if (!res.ok) return;
    const data = await res.json();
    state.graphView = data;
    state.visualizer.loadGraphData(data);

    // Populate selectors
    const companyNodes = data.nodes.filter(n => n.type === "COMPANY");
    const optionsHTML = companyNodes.map(n => `<option value="${n.id}">${n.label} (${n.ticker || n.id})</option>`).join("");

    if (el.pathSourceSelect) el.pathSourceSelect.innerHTML = optionsHTML;
    if (el.pathTargetSelect) {
      el.pathTargetSelect.innerHTML = optionsHTML;
      if (companyNodes.length > 1) el.pathTargetSelect.selectedIndex = 1;
    }
    if (el.shockSourceSelect) {
      el.shockSourceSelect.innerHTML = optionsHTML;
      // Default to TSMC
      const tsmIdx = companyNodes.findIndex(n => n.ticker === "TSM");
      if (tsmIdx !== -1) el.shockSourceSelect.selectedIndex = tsmIdx;
    }

    if (companyNodes.length > 0) {
      renderNodeDetail(companyNodes[0]);
    }
  } catch (err) {
    console.error("Graph view load error:", err);
  }
}

function renderNodeDetail(node) {
  state.selectedNode = node;
  el.graphNodeDetail.innerHTML = `
    <div style="font-weight: 800; font-size: 16px; color: #fff; margin-bottom: 6px;">
      ${node.label} ${node.ticker ? `<span style="color: var(--kuber-gold); font-family: var(--font-mono);">(${node.ticker})</span>` : ""}
    </div>
    <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 12px;">${node.sector || "Strategic Entity"}</div>
    
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-family: var(--font-mono); font-size: 12px;">
      <div style="background: rgba(255,255,255,0.03); padding: 8px; border-radius: 6px;">
        <span style="color: var(--text-dim); display: block; font-size: 10px;">MARKET CAP</span>
        <strong style="color: #fff;">${node.market_cap_b ? `$${node.market_cap_b}B` : "N/A"}</strong>
      </div>
      <div style="background: rgba(255,255,255,0.03); padding: 8px; border-radius: 6px;">
        <span style="color: var(--text-dim); display: block; font-size: 10px;">PAGERANK</span>
        <strong style="color: var(--kuber-gold);">${node.pagerank || 0}</strong>
      </div>
      <div style="background: rgba(255,255,255,0.03); padding: 8px; border-radius: 6px;">
        <span style="color: var(--text-dim); display: block; font-size: 10px;">GRAPH DEGREE</span>
        <strong style="color: var(--cyber-cyan);">${node.degree || 0} edges</strong>
      </div>
      <div style="background: rgba(255,255,255,0.03); padding: 8px; border-radius: 6px;">
        <span style="color: var(--text-dim); display: block; font-size: 10px;">ENTITY TYPE</span>
        <strong style="color: var(--market-emerald);">${node.type}</strong>
      </div>
    </div>
  `;
}

async function executeShortestPath() {
  const src = el.pathSourceSelect.value;
  const tgt = el.pathTargetSelect.value;
  if (!src || !tgt) return;

  try {
    el.pathResultBox.innerHTML = '<span style="color: var(--kuber-gold);">Calculating relational pathway...</span>';
    const res = await fetch("/api/graph/shortest-path", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source_id: src, target_id: tgt })
    });
    if (!res.ok) return;
    const data = await res.json();

    if (data.found) {
      el.pathResultBox.innerHTML = `
        <div style="font-weight: 700; color: var(--kuber-gold); font-size: 12px; margin-bottom: 4px;">
          ✓ Shortest Path Found (${data.path_distance} Hops)
        </div>
        <div style="font-size: 12px; color: #fff;">${data.strategic_summary}</div>
      `;
    } else {
      el.pathResultBox.innerHTML = `<span style="color: var(--contagion-rose);">${data.strategic_summary}</span>`;
    }
  } catch (err) {
    console.error("Path error:", err);
  }
}

async function executeContagionSimulation() {
  const src = el.shockSourceSelect.value;
  const mag = parseFloat(el.shockMagnitudeSlider.value);
  if (!src) return;

  try {
    el.shockResultBox.innerHTML = '<span style="color: var(--contagion-rose);">Simulating systemic shock cascade...</span>';
    state.visualizer.triggerShockAnimation(src, mag);

    const res = await fetch("/api/graph/simulate-contagion", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ shock_source_id: src, shock_magnitude_pct: mag })
    });
    if (!res.ok) return;
    const data = await res.json();

    el.shockResultBox.innerHTML = `
      <div style="border-left: 3px solid var(--contagion-rose); padding-left: 10px; margin-bottom: 8px;">
        <div style="font-weight: 800; color: var(--contagion-rose); font-size: 12px;">
          ⚠️ ${data.systemic_risk_level} — $${data.total_market_cap_at_risk_b}B AT RISK
        </div>
        <div style="font-size: 12px; color: #e2e8f0; margin-top: 4px;">${data.narrative_assessment}</div>
      </div>
      <div style="font-family: var(--font-mono); font-size: 11px; color: var(--text-muted);">
        Downstream Exposed: ${data.affected_nodes.map(n => `<span style="color: #fff;">${n.label} (-${n.shock_intensity_pct}%)</span>`).join(", ")}
      </div>
    `;
  } catch (err) {
    console.error("Shock simulation error:", err);
  }
}

/* --- Workspace 2: Autonomous DAG Orchestrator --- */
async function initDAGWorkspace() {
  // Load Pipelines
  try {
    const res = await fetch("/api/dag/pipelines");
    if (res.ok) {
      const pipelines = await res.json();
      el.dagPipelineSelect.innerHTML = pipelines.map(p => `
        <option value="${p.pipeline_id}">${p.title}</option>
      `).join("");
      renderDAGFlowSteps(pipelines[0]);
    }
  } catch (err) {
    console.error("DAG load error:", err);
  }

  el.dagPipelineSelect.addEventListener("change", async (e) => {
    state.activePipelineId = e.target.value;
    const res = await fetch("/api/dag/pipelines");
    const pipelines = await res.json();
    const sel = pipelines.find(p => p.pipeline_id === state.activePipelineId);
    if (sel) renderDAGFlowSteps(sel);
  });

  el.btnRunDAG.addEventListener("click", executeDAGRun);
}

function renderDAGFlowSteps(pipeline) {
  if (!pipeline || !pipeline.nodes) return;
  el.dagFlowSteps.innerHTML = pipeline.nodes.map((n, i) => `
    <div class="dag-step-node status-PENDING" id="dagNode-${n.id}">
      <div class="dag-step-header">
        <span>STEP 0${i + 1}</span>
        <span class="step-status-tag" style="font-size: 10px;">PENDING</span>
      </div>
      <div class="dag-step-name">${n.name}</div>
      <div class="dag-step-duration" id="dagDuration-${n.id}">-- ms</div>
    </div>
    ${i < pipeline.nodes.length - 1 ? '<div class="dag-arrow">→</div>' : ""}
  `).join("");
}

async function executeDAGRun() {
  el.btnRunDAG.disabled = true;
  el.btnRunDAG.textContent = "Executing DAG...";
  el.dagLogStream.innerHTML = "<div>[INIT] Triggering distributed execution pipeline...</div>";
  el.dagExecutiveBrief.innerHTML = '<span style="color: var(--text-dim);">Awaiting pipeline completion...</span>';

  try {
    const res = await fetch(`/api/dag/execute/${state.activePipelineId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({})
    });
    if (!res.ok) throw new Error("Execution failed");
    const run = await res.json();

    // Stream logs
    el.dagLogStream.innerHTML = run.execution_logs.map(log => `<div>${log}</div>`).join("");
    el.dagLogStream.scrollTop = el.dagLogStream.scrollHeight;

    // Update node states
    for (const [nodeId, state] of Object.entries(run.nodes_state)) {
      const nodeEl = document.getElementById(`dagNode-${nodeId}`);
      const durEl = document.getElementById(`dagDuration-${nodeId}`);
      if (nodeEl) {
        nodeEl.className = `dag-step-node status-${state.status}`;
        const tag = nodeEl.querySelector(".step-status-tag");
        if (tag) tag.textContent = state.status;
      }
      if (durEl) {
        durEl.textContent = `${state.duration_ms} ms`;
      }
    }

    // Render Executive Brief if generated
    if (run.run_artifacts && run.run_artifacts.executive_brief) {
      el.dagExecutiveBrief.innerHTML = `
        <div style="border-left: 3px solid var(--kuber-gold); padding-left: 14px;">
          <h4 style="color: var(--kuber-gold); font-size: 13px; font-family: var(--font-mono); margin-bottom: 6px;">EXECUTIVE INTELLIGENCE SYNTHESIS</h4>
          <p style="color: #f1f5f9; font-size: 13px; line-height: 1.6;">${run.run_artifacts.executive_brief}</p>
        </div>
      `;
    }

    // Refresh graph view to pick up newly ingested nodes/relations
    await refreshGraphData();

  } catch (err) {
    el.dagLogStream.innerHTML += `<div style="color: var(--contagion-rose);">[ERROR] ${err.message}</div>`;
  } finally {
    el.btnRunDAG.disabled = false;
    el.btnRunDAG.textContent = "Execute Autonomous Pipeline";
  }
}

/* --- Workspace 3: Crawl4AI Scraper & DOM Pruner --- */
function initCrawlerWorkspace() {
  el.btnExecuteCrawl.addEventListener("click", async () => {
    const url = el.crawlUrlInput.value.trim();
    const strategy = el.pruneStrategySelect.value;
    if (!url) return;

    el.btnExecuteCrawl.disabled = true;
    el.btnExecuteCrawl.textContent = "Crawling & Pruning...";

    try {
      // Step 1: Crawl
      const crawlRes = await fetch("/api/crawler/crawl", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url, user_agent_mode: "desktop_chrome" })
      });
      if (!crawlRes.ok) throw new Error("Crawl failed");
      const crawlData = await crawlRes.json();

      // Step 2: Prune
      const pruneRes = await fetch("/api/crawler/prune", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          raw_html: "<html><body>Mock Ingested Content</body></html>",
          strategy: strategy
        })
      });
      const pruneData = await pruneRes.json();

      el.crawlRawChars.textContent = crawlData.raw_html_length.toLocaleString();
      el.crawlCleanChars.textContent = pruneData.cleaned_char_count.toLocaleString();
      el.crawlCompressionBadge.textContent = `${pruneData.compression_ratio_pct}% Compression`;
      el.crawlMarkdownPreview.innerText = pruneData.markdown_content;

    } catch (err) {
      alert("Crawler error: " + err.message);
    } finally {
      el.btnExecuteCrawl.disabled = false;
      el.btnExecuteCrawl.textContent = "Ingest & Prune DOM";
    }
  });
}

/* --- Workspace 4: EDI Natural Language SQL Console --- */
function initEDIWorkspace() {
  el.btnRunEDI.addEventListener("click", () => executeEDIQuery(el.ediQueryInput.value));

  el.ediQueryInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") executeEDIQuery(el.ediQueryInput.value);
  });

  el.quickPromptChips.forEach(chip => {
    chip.addEventListener("click", () => {
      const q = chip.dataset.query;
      el.ediQueryInput.value = q;
      executeEDIQuery(q);
    });
  });
}

async function executeEDIQuery(queryText) {
  if (!queryText || !queryText.trim()) return;

  el.btnRunEDI.disabled = true;
  el.btnRunEDI.textContent = "Synthesizing SQL...";

  try {
    const res = await fetch("/api/edi/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ natural_query: queryText.trim() })
    });
    if (!res.ok) throw new Error("EDI Query Failed");
    const data = await res.json();

    el.ediAnswerText.textContent = data.natural_language_answer;
    el.ediSqlCode.textContent = data.generated_sql || "-- No SQL synthesized";
    el.ediCypherCode.textContent = data.generated_cypher || "-- No Graph Cypher required";
    el.ediLatencyBadge.textContent = `${data.execution_time_ms} ms (${data.grounded_record_count} records)`;

    // Render Data Table
    if (data.column_headers.length > 0) {
      el.ediTableHead.innerHTML = `<tr>${data.column_headers.map(c => `<th>${c}</th>`).join("")}</tr>`;
      el.ediTableBody.innerHTML = data.rows.map(row => `
        <tr>${data.column_headers.map(c => `<td>${row[c] !== null && row[c] !== undefined ? row[c] : ""}</td>`).join("")}</tr>
      `).join("");
    } else {
      el.ediTableHead.innerHTML = "";
      el.ediTableBody.innerHTML = '<tr><td style="color: var(--text-dim); text-align: center; padding: 24px;">No records returned</td></tr>';
    }

  } catch (err) {
    el.ediAnswerText.textContent = "Query error: " + err.message;
  } finally {
    el.btnRunEDI.disabled = false;
    el.btnRunEDI.textContent = "Ask EDI";
  }
}

/* --- Workspace 5: Quantitative Valuation & Altman Z --- */
function initValuationWorkspace() {
  el.valTickerSelect.addEventListener("change", (e) => {
    state.selectedTicker = e.target.value;
    loadValuationReport(state.selectedTicker);
  });

  loadValuationReport(state.selectedTicker);
}

async function loadValuationReport(ticker) {
  try {
    const res = await fetch(`/api/financials/ratios/${ticker}`);
    if (!res.ok) return;
    const report = await res.json();

    el.valHealthGrade.textContent = report.health_grade;
    el.valAltmanScore.textContent = report.altman_z.z_score.toFixed(2);
    el.valAltmanZone.textContent = report.altman_z.zone.replace("_", " ");
    el.valAltmanInterp.textContent = report.altman_z.clinical_interpretation;

    // Position Altman Pointer (Z-score from 0 to 10 mapped to 0% - 100%)
    const pct = Math.min(96, Math.max(4, (report.altman_z.z_score / 8.0) * 100));
    el.valAltmanPointer.style.left = `${pct}%`;

    el.valBeneishScore.textContent = report.beneish_m.m_score.toFixed(2);
    el.valBeneishRisk.textContent = report.beneish_m.manipulation_risk;
    el.valBeneishRisk.style.color = report.beneish_m.manipulation_risk === "HIGH_RISK" ? "var(--contagion-rose)" : "var(--market-emerald)";

    el.valGrossMargin.textContent = `${report.gross_margin_pct}%`;
    el.valOperatingMargin.textContent = `${report.operating_margin_pct}%`;
    el.valCurrentRatio.textContent = report.current_ratio;
    el.valDebtEquity.textContent = report.debt_to_equity;
    el.valPeRatio.textContent = report.price_to_earnings;

  } catch (err) {
    console.error("Valuation load error:", err);
  }
}
