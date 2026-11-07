/**
 * Kuber Data Core (कुबेर) — Main Frontend Workstation Controller
 * EDI Interactive Spreadsheet & Recharts Studio, Arlo Web Scraping Automation,
 * Knowledge Graph & Contagion Shock Engine, Autonomous DAG Runner, and Valuation Matrix.
 */

// Global State
const state = {
  currentTab: "ws-edi-studio",
  activeChartType: "BAR",
  selectedCell: null,
  spreadsheetData: null,
  graphView: null,
  visualizer: null,
  selectedNode: null,
  activePipelineId: "financial-cortex-e2e",
  selectedTicker: "NVDA"
};

// DOM Element Registry
const el = {};

function showToast(message, type = "success") {
  const toast = document.getElementById("kuberToast");
  if (!toast) return;
  toast.textContent = message;
  toast.style.borderColor = type === "error" ? "var(--contagion-rose, #f43f5e)" : "var(--kuber-gold, #eab308)";
  toast.style.color = type === "error" ? "#fca5a5" : "#fef08a";
  toast.style.display = "block";
  clearTimeout(toast._timeout);
  toast._timeout = setTimeout(() => {
    toast.style.display = "none";
  }, 4500);
}

document.addEventListener("DOMContentLoaded", () => {
  initElementRegistry();
  initNavigationTabs();
  initMarketTickerTape();
  initEDIStudio();
  initArloScraperWorkspace();
  initGraphWorkspace();
  initDAGWorkspace();
  initValuationWorkspace();
});

function initElementRegistry() {
  el.tabBtns = document.querySelectorAll(".ws-tab-btn");
  el.panels = document.querySelectorAll(".workspace-panel");
  el.tickerTapeTrack = document.getElementById("tickerTapeTrack");

  // EDI Elements
  el.ediQueryInput = document.getElementById("ediQueryInput");
  el.btnRunEDI = document.getElementById("btnRunEDI");
  el.ediAnswerText = document.getElementById("ediAnswerText");
  el.ediLatencyBadge = document.getElementById("ediLatencyBadge");
  el.quickPromptChips = document.querySelectorAll(".quick-prompt-chip");
  el.spreadsheetGrid = document.getElementById("spreadsheetGrid");
  el.formulaCoord = document.getElementById("formulaCoord");
  el.formulaInput = document.getElementById("formulaInput");
  el.btnRefreshSheet = document.getElementById("btnRefreshSheet");
  el.btnExportCSV = document.getElementById("btnExportCSV");
  el.sheetTotalRows = document.getElementById("sheetTotalRows");
  el.sheetTotalCap = document.getElementById("sheetTotalCap");
  el.sheetAvgMargin = document.getElementById("sheetAvgMargin");

  // Chart Elements
  el.chartPillBtns = document.querySelectorAll(".chart-pill-btn");
  el.chartTitle = document.getElementById("chartTitle");
  el.chartSvg = document.getElementById("chartSvg");
  el.chartTooltip = document.getElementById("chartTooltip");
  el.chartLegend = document.getElementById("chartLegend");

  // Arlo Scraper Elements
  el.scraperWorkersContainer = document.getElementById("scraperWorkersContainer");
  el.crawlPresetSelect = document.getElementById("crawlPresetSelect");
  el.crawlUrlInput = document.getElementById("crawlUrlInput");
  el.pruneStrategySelect = document.getElementById("pruneStrategySelect");
  el.btnExecuteCrawl = document.getElementById("btnExecuteCrawl");
  el.btnScrapeToSheet = document.getElementById("btnScrapeToSheet");
  el.crawlRawChars = document.getElementById("crawlRawChars");
  el.crawlCleanChars = document.getElementById("crawlCleanChars");
  el.crawlCompressionBadge = document.getElementById("crawlCompressionBadge");
  el.crawlMarkdownPreview = document.getElementById("crawlMarkdownPreview");

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
        state.visualizer._setupCanvasSize();
        setTimeout(() => state.visualizer._setupCanvasSize(), 50);
        setTimeout(() => state.visualizer._setupCanvasSize(), 180);
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

    el.tickerTapeTrack.innerHTML = tickerHTML + tickerHTML;
  } catch (err) {
    console.error("Ticker tape fetch failed:", err);
  }
}

/* =========================================================================
   WORKSPACE 1: EDI SPREADSHEET & RECHARTS STUDIO
   ========================================================================= */
async function initEDIStudio() {
  // Query Input
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

  // Chart Type Pills
  el.chartPillBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      el.chartPillBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      state.activeChartType = btn.dataset.chart;
      loadEDIChart(state.activeChartType);
    });
  });

  // Toolbar Actions
  el.btnRefreshSheet.addEventListener("click", loadSpreadsheetData);
  el.btnExportCSV.addEventListener("click", exportSpreadsheetCSV);

  // Formula input enter
  el.formulaInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && state.selectedCell) {
      commitCellEdit(state.selectedCell.ticker, state.selectedCell.column, el.formulaInput.value);
    }
  });

  // Initial Load
  await loadSpreadsheetData();
  await loadEDIChart(state.activeChartType);
}

async function loadSpreadsheetData() {
  try {
    const res = await fetch("/api/edi/sheet");
    if (!res.ok) return;
    const data = await res.json();
    state.spreadsheetData = data;
    renderSpreadsheetGrid(data);
  } catch (err) {
    console.error("Spreadsheet load error:", err);
  }
}

function renderSpreadsheetGrid(data) {
  if (!el.spreadsheetGrid || !data) return;

  const colLabels = [
    { key: "ticker", label: "A: TICKER" },
    { key: "company_name", label: "B: COMPANY NAME" },
    { key: "sector", label: "C: SECTOR" },
    { key: "country", label: "D: CTRY" },
    { key: "market_cap_b", label: "E: MARKET CAP ($B)" },
    { key: "revenue_b", label: "F: REVENUE ($B)" },
    { key: "gross_margin_pct", label: "G: GROSS MARGIN (%)" },
    { key: "operating_margin_pct", label: "H: OPERATING MARGIN (%)" },
    { key: "debt_to_equity", label: "I: DEBT/EQUITY" }
  ];

  let totalCap = 0;
  let totalMargin = 0;
  let validMarginCount = 0;

  // Header row
  let headerHtml = '<thead><tr><th class="col-corner">#</th>';
  colLabels.forEach(col => {
    headerHtml += `<th>${col.label}</th>`;
  });
  headerHtml += "</tr></thead>";

  // Body rows
  let bodyHtml = "<tbody>";
  data.rows.forEach((row, rowIdx) => {
    const rowNum = rowIdx + 1;
    totalCap += (row.market_cap_b || 0);
    if (row.operating_margin_pct > 0) {
      totalMargin += row.operating_margin_pct;
      validMarginCount++;
    }

    bodyHtml += `<tr><td class="row-num">${rowNum}</td>`;
    colLabels.forEach((col, colIdx) => {
      const cellVal = row[col.key] !== null && row[col.key] !== undefined ? row[col.key] : "";
      const colLetter = String.fromCharCode(65 + colIdx);
      const coord = `${colLetter}${rowNum}`;
      bodyHtml += `
        <td class="editable-cell" 
            data-coord="${coord}" 
            data-ticker="${row.ticker}" 
            data-col="${col.key}" 
            data-val="${cellVal}">
          ${typeof cellVal === "number" ? cellVal.toLocaleString() : cellVal}
        </td>
      `;
    });
    bodyHtml += "</tr>";
  });
  bodyHtml += "</tbody>";

  el.spreadsheetGrid.innerHTML = headerHtml + bodyHtml;

  // Update Footer stats
  el.sheetTotalRows.textContent = data.total_rows;
  el.sheetTotalCap.textContent = `$${(totalCap / 1000).toFixed(1)}T`;
  const avgMargin = validMarginCount > 0 ? (totalMargin / validMarginCount).toFixed(1) : "0.0";
  el.sheetAvgMargin.textContent = `${avgMargin}%`;

  // Attach cell click handlers
  el.spreadsheetGrid.querySelectorAll(".editable-cell").forEach(td => {
    td.addEventListener("click", () => {
      el.spreadsheetGrid.querySelectorAll(".cell-selected").forEach(c => c.classList.remove("cell-selected"));
      td.classList.add("cell-selected");
      const coord = td.dataset.coord;
      const val = td.dataset.val;
      const ticker = td.dataset.ticker;
      const column = td.dataset.col;

      state.selectedCell = { td, coord, val, ticker, column };
      el.formulaCoord.textContent = coord;
      el.formulaInput.value = val;
    });

    td.addEventListener("dblclick", () => {
      const currentVal = td.dataset.val;
      const newVal = prompt(`Edit Cell ${td.dataset.coord}:`, currentVal);
      if (newVal !== null && newVal !== currentVal) {
        commitCellEdit(td.dataset.ticker, td.dataset.col, newVal);
      }
    });
  });

  // Auto-select first cell if none selected
  if (!state.selectedCell) {
    const firstCell = el.spreadsheetGrid.querySelector(".editable-cell");
    if (firstCell) {
      firstCell.click();
    }
  }
}

async function commitCellEdit(ticker, column, value) {
  try {
    const res = await fetch("/api/edi/sheet/update", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ticker, column, value })
    });
    if (!res.ok) throw new Error("Update failed");
    await loadSpreadsheetData();
    await loadEDIChart(state.activeChartType);
    showToast(`✓ Updated ${ticker} [${column}] = ${value}`);
  } catch (err) {
    showToast("Error updating cell: " + err.message, "error");
  }
}

function exportSpreadsheetCSV() {
  if (!state.spreadsheetData || !state.spreadsheetData.rows) return;
  const data = state.spreadsheetData;
  const csvRows = [data.columns.join(",")];

  data.rows.forEach(r => {
    const rowVals = data.columns.map(c => `"${r[c] !== undefined ? r[c] : ''}"`);
    csvRows.push(rowVals.join(","));
  });

  const blob = new Blob([csvRows.join("\n")], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `kuber_financial_cortex_${Date.now()}.csv`;
  a.click();
}

async function executeEDIQuery(queryText) {
  if (!queryText || !queryText.trim()) return;

  el.btnRunEDI.disabled = true;
  el.btnRunEDI.textContent = "Processing Query...";

  try {
    const res = await fetch("/api/edi/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ natural_query: queryText.trim() })
    });
    if (!res.ok) throw new Error("EDI Query Failed");
    const data = await res.json();

    el.ediAnswerText.textContent = data.natural_language_answer;
    el.ediLatencyBadge.textContent = `${data.execution_time_ms} ms (${data.grounded_record_count} records)`;

    // If chart returned in response, render it
    if (data.chart_spec) {
      renderSvgChart(data.chart_spec);
    } else {
      loadEDIChart(state.activeChartType);
    }

  } catch (err) {
    el.ediAnswerText.textContent = "Query error: " + err.message;
  } finally {
    el.btnRunEDI.disabled = false;
    el.btnRunEDI.textContent = "Ask EDI";
  }
}

/* --- Dynamic SVG / Recharts Visualizer --- */
async function loadEDIChart(chartType) {
  try {
    const res = await fetch(`/api/edi/chart?chart_type=${chartType}`);
    if (!res.ok) return;
    const spec = await res.json();
    renderSvgChart(spec);
  } catch (err) {
    console.error("Chart load error:", err);
  }
}

function renderSvgChart(spec) {
  if (!el.chartSvg || !spec) return;
  el.chartTitle.textContent = spec.title;

  const svg = el.chartSvg;
  svg.innerHTML = "";

  const width = 380;
  const height = 320;
  const margin = { top: 30, right: 20, bottom: 40, left: 45 };
  const innerW = width - margin.left - margin.right;
  const innerH = height - margin.top - margin.bottom;

  // Legend
  if (spec.legend && el.chartLegend) {
    el.chartLegend.innerHTML = spec.series.map(s => `
      <div style="display: flex; align-items: center; gap: 6px;">
        <span style="width: 10px; height: 10px; background: ${s.color}; border-radius: 2px;"></span>
        <span style="color: var(--text-muted);">${s.name}</span>
      </div>
    `).join("");
  }

  if (spec.chart_type === "RADAR") {
    renderRadarChart(svg, spec, width, height);
    return;
  }

  // Determine Max Value
  let maxVal = 0;
  spec.series.forEach(s => {
    s.data_points.forEach(v => {
      if (v > maxVal) maxVal = v;
    });
  });
  maxVal = Math.ceil(maxVal * 1.15) || 100;

  // Grid Lines
  for (let i = 0; i <= 4; i++) {
    const yVal = Math.round((maxVal / 4) * i);
    const yPos = margin.top + innerH - (i / 4) * innerH;

    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", margin.left);
    line.setAttribute("y1", yPos);
    line.setAttribute("x2", width - margin.right);
    line.setAttribute("y2", yPos);
    line.setAttribute("stroke", "rgba(255,255,255,0.06)");
    line.setAttribute("stroke-dasharray", "3,3");
    svg.appendChild(line);

    const txt = document.createElementNS("http://www.w3.org/2000/svg", "text");
    txt.setAttribute("x", margin.left - 6);
    txt.setAttribute("y", yPos + 3);
    txt.setAttribute("fill", "#64748b");
    txt.setAttribute("font-size", "9");
    txt.setAttribute("font-family", "ui-monospace");
    txt.setAttribute("text-anchor", "end");
    txt.textContent = yVal.toString();
    svg.appendChild(txt);
  }

  const categoryCount = spec.x_axis_labels.length;
  const slotWidth = innerW / Math.max(1, categoryCount);

  if (spec.chart_type === "LINE") {
    // Render Line Chart
    spec.series.forEach(s => {
      const points = [];
      s.data_points.forEach((val, idx) => {
        const x = margin.left + idx * slotWidth + slotWidth / 2;
        const y = margin.top + innerH - (val / maxVal) * innerH;
        points.push({ x, y, val, label: spec.x_axis_labels[idx] });
      });

      // Draw Path
      if (points.length > 0) {
        let d = `M ${points[0].x} ${points[0].y}`;
        for (let i = 1; i < points.length; i++) {
          d += ` L ${points[i].x} ${points[i].y}`;
        }
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("d", d);
        path.setAttribute("fill", "none");
        path.setAttribute("stroke", s.color);
        path.setAttribute("stroke-width", "2.5");
        svg.appendChild(path);

        // Draw Dots
        points.forEach(pt => {
          const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
          circle.setAttribute("cx", pt.x);
          circle.setAttribute("cy", pt.y);
          circle.setAttribute("r", "4.5");
          circle.setAttribute("fill", s.color);
          circle.setAttribute("stroke", "#fff");
          circle.setAttribute("stroke-width", "1.5");
          circle.style.cursor = "pointer";

          circle.addEventListener("mouseenter", (e) => {
            el.chartTooltip.style.opacity = "1";
            el.chartTooltip.style.left = `${e.offsetX + 10}px`;
            el.chartTooltip.style.top = `${e.offsetY - 25}px`;
            el.chartTooltip.textContent = `${pt.label}: $${pt.val}B`;
          });
          circle.addEventListener("mouseleave", () => {
            el.chartTooltip.style.opacity = "0";
          });

          svg.appendChild(circle);
        });
      }
    });

  } else {
    // Render Grouped Bar Chart
    const seriesCount = spec.series.length;
    const barWidth = Math.max(8, (slotWidth - 14) / seriesCount);

    spec.x_axis_labels.forEach((label, cIdx) => {
      const slotX = margin.left + cIdx * slotWidth;

      spec.series.forEach((s, sIdx) => {
        const val = s.data_points[cIdx] || 0;
        const barH = (val / maxVal) * innerH;
        const x = slotX + 7 + sIdx * barWidth;
        const y = margin.top + innerH - barH;

        const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        rect.setAttribute("class", "chart-svg-bar");
        rect.setAttribute("x", x);
        rect.setAttribute("y", y);
        rect.setAttribute("width", barWidth - 2);
        rect.setAttribute("height", Math.max(2, barH));
        rect.setAttribute("fill", s.color);
        rect.setAttribute("rx", "2");

        rect.addEventListener("mouseenter", (e) => {
          el.chartTooltip.style.opacity = "1";
          el.chartTooltip.style.left = `${e.offsetX + 10}px`;
          el.chartTooltip.style.top = `${e.offsetY - 25}px`;
          el.chartTooltip.textContent = `${label} [${s.name}]: ${val}`;
        });
        rect.addEventListener("mouseleave", () => {
          el.chartTooltip.style.opacity = "0";
        });

        svg.appendChild(rect);
      });
    });
  }

  // Draw X-axis labels for both Bar and Line charts
  spec.x_axis_labels.forEach((label, cIdx) => {
    const slotX = margin.left + cIdx * slotWidth;
    const txt = document.createElementNS("http://www.w3.org/2000/svg", "text");
    txt.setAttribute("x", slotX + slotWidth / 2);
    txt.setAttribute("y", height - margin.bottom + 16);
    txt.setAttribute("fill", "#94a3b8");
    txt.setAttribute("font-size", "10");
    txt.setAttribute("font-family", "ui-monospace");
    txt.setAttribute("text-anchor", "middle");
    txt.textContent = label;
    svg.appendChild(txt);
  });
}

function renderRadarChart(svg, spec, width, height) {
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = 100;
  const sides = spec.x_axis_labels.length;

  // Grid Webs
  for (let level = 1; level <= 4; level++) {
    const r = (radius / 4) * level;
    let pathD = "";
    for (let i = 0; i < sides; i++) {
      const angle = (i / sides) * Math.PI * 2 - Math.PI / 2;
      const x = centerX + Math.cos(angle) * r;
      const y = centerY + Math.sin(angle) * r;
      pathD += (i === 0 ? "M " : "L ") + `${x} ${y} `;
    }
    pathD += "Z";
    const web = document.createElementNS("http://www.w3.org/2000/svg", "path");
    web.setAttribute("d", pathD);
    web.setAttribute("fill", "none");
    web.setAttribute("stroke", "rgba(255,255,255,0.08)");
    web.setAttribute("stroke-dasharray", "2,2");
    svg.appendChild(web);
  }

  // Draw Axes and Labels
  spec.x_axis_labels.forEach((lbl, i) => {
    const angle = (i / sides) * Math.PI * 2 - Math.PI / 2;
    const x = centerX + Math.cos(angle) * radius;
    const y = centerY + Math.sin(angle) * radius;

    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", centerX);
    line.setAttribute("y1", centerY);
    line.setAttribute("x2", x);
    line.setAttribute("y2", y);
    line.setAttribute("stroke", "rgba(255,255,255,0.12)");
    svg.appendChild(line);

    // Label
    const lx = centerX + Math.cos(angle) * (radius + 20);
    const ly = centerY + Math.sin(angle) * (radius + 15);
    const txt = document.createElementNS("http://www.w3.org/2000/svg", "text");
    txt.setAttribute("x", lx);
    txt.setAttribute("y", ly);
    txt.setAttribute("fill", "#94a3b8");
    txt.setAttribute("font-size", "9");
    txt.setAttribute("font-family", "ui-monospace");
    txt.setAttribute("text-anchor", "middle");
    txt.textContent = lbl.split(" ")[0];
    svg.appendChild(txt);
  });

  // Series Polygons
  spec.series.forEach(s => {
    let polyD = "";
    s.data_points.forEach((val, i) => {
      const angle = (i / sides) * Math.PI * 2 - Math.PI / 2;
      const normalizedR = Math.min(radius, (val / 3.0) * radius);
      const x = centerX + Math.cos(angle) * normalizedR;
      const y = centerY + Math.sin(angle) * normalizedR;
      polyD += (i === 0 ? "M " : "L ") + `${x} ${y} `;
    });
    polyD += "Z";

    const poly = document.createElementNS("http://www.w3.org/2000/svg", "path");
    poly.setAttribute("d", polyD);
    poly.setAttribute("fill", s.color + "33");
    poly.setAttribute("stroke", s.color);
    poly.setAttribute("stroke-width", "2");
    svg.appendChild(poly);

    // Series Vertex Interactive Dots
    s.data_points.forEach((val, i) => {
      const angle = (i / sides) * Math.PI * 2 - Math.PI / 2;
      const normalizedR = Math.min(radius, (val / 3.0) * radius);
      const x = centerX + Math.cos(angle) * normalizedR;
      const y = centerY + Math.sin(angle) * normalizedR;

      const dot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      dot.setAttribute("cx", x);
      dot.setAttribute("cy", y);
      dot.setAttribute("r", "3.5");
      dot.setAttribute("fill", s.color);
      dot.setAttribute("stroke", "#fff");
      dot.setAttribute("stroke-width", "1.5");
      dot.style.cursor = "pointer";

      dot.addEventListener("mouseenter", (e) => {
        el.chartTooltip.style.opacity = "1";
        el.chartTooltip.style.left = `${e.offsetX + 10}px`;
        el.chartTooltip.style.top = `${e.offsetY - 25}px`;
        el.chartTooltip.textContent = `${spec.x_axis_labels[i]} [${s.name}]: ${val}`;
      });
      dot.addEventListener("mouseleave", () => {
        el.chartTooltip.style.opacity = "0";
      });
      svg.appendChild(dot);
    });
  });
}

/* =========================================================================
   WORKSPACE 2: ARLO WEB SCRAPING AUTOMATION
   ========================================================================= */
async function initArloScraperWorkspace() {
  // Load Scraper Workers Telemetry
  try {
    const res = await fetch("/api/crawler/workers");
    if (res.ok) {
      const workers = await res.json();
      el.scraperWorkersContainer.innerHTML = workers.map(w => `
        <div class="worker-node-card">
          <div class="worker-header">
            <span style="color: #fff; font-weight: 700;">${w.worker_id.toUpperCase()}</span>
            <span class="worker-status-active">● ACTIVE</span>
          </div>
          <div class="worker-meta-line">
            <span>${w.region}</span>
            <span style="color: var(--kuber-gold);">${w.latency_ms} ms</span>
          </div>
          <div class="worker-meta-line">
            <span style="color: var(--text-dim);">${w.type}</span>
            <span style="color: var(--market-emerald);">${w.uptime_pct}% Uptime</span>
          </div>
        </div>
      `).join("");
    }
  } catch (err) {
    console.error("Worker telemetry error:", err);
  }

  // Preset selector
  el.crawlPresetSelect.addEventListener("change", (e) => {
    if (e.target.value !== "custom") {
      el.crawlUrlInput.value = e.target.value;
    } else {
      el.crawlUrlInput.value = "";
      el.crawlUrlInput.placeholder = "https://example.com/target-filing";
      el.crawlUrlInput.focus();
    }
  });

  // Execute Crawl
  el.btnExecuteCrawl.addEventListener("click", async () => {
    const url = el.crawlUrlInput.value.trim();
    const strategy = el.pruneStrategySelect.value;
    if (!url) return;

    el.btnExecuteCrawl.disabled = true;
    el.btnExecuteCrawl.textContent = "Crawling & Pruning...";

    try {
      const crawlRes = await fetch("/api/crawler/crawl", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url, user_agent_mode: "desktop_chrome" })
      });
      if (!crawlRes.ok) throw new Error("Crawl failed");
      const crawlData = await crawlRes.json();

      const rawHtmlPayload = crawlData.raw_html || `<html><body><h1>${crawlData.title}</h1><p>Ingested content from ${url}</p></body></html>`;

      const pruneRes = await fetch("/api/crawler/prune", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          raw_html: rawHtmlPayload,
          strategy: strategy
        })
      });
      const pruneData = await pruneRes.json();

      el.crawlRawChars.textContent = crawlData.raw_html_length.toLocaleString();
      el.crawlCleanChars.textContent = pruneData.cleaned_char_count.toLocaleString();
      el.crawlCompressionBadge.textContent = `${pruneData.compression_ratio_pct}% Compression`;
      el.crawlMarkdownPreview.innerText = pruneData.markdown_content;
      showToast(`✓ Crawled & pruned ${crawlData.raw_html_length} raw bytes with ${pruneData.compression_ratio_pct}% compression.`);

    } catch (err) {
      showToast("Crawler error: " + err.message, "error");
    } finally {
      el.btnExecuteCrawl.disabled = false;
      el.btnExecuteCrawl.textContent = "Ingest & Prune";
    }
  });

  // Scrape & Inject To Sheet Action
  el.btnScrapeToSheet.addEventListener("click", async () => {
    const url = el.crawlUrlInput.value.trim();
    if (!url) return;

    el.btnScrapeToSheet.disabled = true;
    el.btnScrapeToSheet.textContent = "Scraping & Injecting...";

    try {
      const res = await fetch("/api/crawler/scrape-to-sheet", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url })
      });
      if (!res.ok) throw new Error("Scrape to sheet failed");
      const data = await res.json();

      showToast(`✓ Scraped ${data.scraped_url}: Parsed ${data.cleaned_bytes}B, extracted ${data.entities_extracted} entities!`);

      // Switch to EDI studio tab and refresh sheet
      const ediTabBtn = document.querySelector('[data-tab="ws-edi-studio"]');
      if (ediTabBtn) ediTabBtn.click();
      await loadSpreadsheetData();
      await loadEDIChart(state.activeChartType);

    } catch (err) {
      showToast("Scrape to sheet error: " + err.message, "error");
    } finally {
      el.btnScrapeToSheet.disabled = false;
      el.btnScrapeToSheet.textContent = "⚡ Scrape & Inject to EDI Sheet";
    }
  });
}

/* =========================================================================
   WORKSPACE 3: KNOWLEDGE GRAPH & CONTAGION
   ========================================================================= */
async function initGraphWorkspace() {
  state.visualizer = new KuberGraphVisualizer("graphCanvas", (node) => {
    renderNodeDetail(node);
  });

  if (el.btnResetZoom) {
    el.btnResetZoom.addEventListener("click", () => state.visualizer.resetZoom());
  }

  await refreshGraphData();

  if (el.btnFindPath) {
    el.btnFindPath.addEventListener("click", executeShortestPath);
  }

  if (el.shockMagnitudeSlider) {
    el.shockMagnitudeSlider.addEventListener("input", (e) => {
      el.shockMagnitudeVal.textContent = `${e.target.value}%`;
    });
  }

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

    const companyNodes = data.nodes.filter(n => n.type === "COMPANY");
    const optionsHTML = companyNodes.map(n => `<option value="${n.id}">${n.label} (${n.ticker || n.id})</option>`).join("");

    if (el.pathSourceSelect) el.pathSourceSelect.innerHTML = optionsHTML;
    if (el.pathTargetSelect) {
      el.pathTargetSelect.innerHTML = optionsHTML;
      if (companyNodes.length > 1) el.pathTargetSelect.selectedIndex = 1;
    }
    if (el.shockSourceSelect) {
      el.shockSourceSelect.innerHTML = optionsHTML;
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
      if (state.visualizer && data.path_nodes) {
        state.visualizer.highlightPath(data.path_nodes);
      }
      el.pathResultBox.innerHTML = `
        <div style="font-weight: 700; color: var(--kuber-gold); font-size: 12px; margin-bottom: 4px;">
          ✓ Shortest Path Found (${data.path_distance} Hops)
        </div>
        <div style="font-size: 12px; color: #fff;">${data.strategic_summary}</div>
      `;
    } else {
      if (state.visualizer) {
        state.visualizer.highlightPath([]);
      }
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

/* =========================================================================
   WORKSPACE 4: AUTONOMOUS DAG ORCHESTRATOR
   ========================================================================= */
async function initDAGWorkspace() {
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

    el.dagLogStream.innerHTML = run.execution_logs.map(log => `<div>${log}</div>`).join("");
    el.dagLogStream.scrollTop = el.dagLogStream.scrollHeight;

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

    if (run.run_artifacts && run.run_artifacts.executive_brief) {
      el.dagExecutiveBrief.innerHTML = `
        <div style="border-left: 3px solid var(--kuber-gold); padding-left: 14px;">
          <h4 style="color: var(--kuber-gold); font-size: 13px; font-family: var(--font-mono); margin-bottom: 6px;">EXECUTIVE INTELLIGENCE SYNTHESIS</h4>
          <p style="color: #f1f5f9; font-size: 13px; line-height: 1.6;">${run.run_artifacts.executive_brief}</p>
        </div>
      `;
    }

    await refreshGraphData();
    await loadSpreadsheetData();

  } catch (err) {
    el.dagLogStream.innerHTML += `<div style="color: var(--contagion-rose);">[ERROR] ${err.message}</div>`;
  } finally {
    el.btnRunDAG.disabled = false;
    el.btnRunDAG.textContent = "Execute Autonomous Pipeline";
  }
}

/* =========================================================================
   WORKSPACE 5: QUANTITATIVE VALUATION & ALTMAN Z
   ========================================================================= */
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
