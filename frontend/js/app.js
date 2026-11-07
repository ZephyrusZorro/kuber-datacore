"use strict";

const byId = id => document.getElementById(id);
const text = (id, value) => { byId(id).textContent = value ?? "—"; };
const svgNS = "http://www.w3.org/2000/svg";
let toastTimer;

function element(tag, label, className) {
  const item = document.createElement(tag);
  if (label != null) item.textContent = label;
  if (className) item.className = className;
  return item;
}

async function api(path, body) {
  const response = await fetch(path, body === undefined ? undefined : {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  const data = await response.json().catch(() => null);
  if (!response.ok || data === null) {
    const detail = typeof data?.detail === "string" ? data.detail : "Request failed (" + response.status + ")";
    throw new Error(detail);
  }
  return data;
}

function showToast(message, type = "success") {
  const toast = byId("kuberToast");
  toast.textContent = message;
  toast.dataset.type = type;
  toast.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { toast.hidden = true; }, 4500);
}

async function runAction(button, pendingLabel, action) {
  if (button.disabled) return;
  const content = [...button.childNodes];
  button.disabled = true;
  button.textContent = pendingLabel;
  try {
    await action();
  } catch (error) {
    showToast(error.message, "error");
  } finally {
    button.replaceChildren(...content);
    button.disabled = false;
  }
}

const tabs = [...document.querySelectorAll(".ws-tab-btn")];
const panels = [...document.querySelectorAll(".workspace-panel")];
let activeTab;
let visualizer;

function activateWorkspace(scroll = false) {
  const tab = tabs.find(item => "#" + item.dataset.tab === location.hash) || tabs[0];
  if (activeTab === tab) return;
  activeTab = tab;
  for (const item of tabs) {
    const selected = item === tab;
    item.classList.toggle("active", selected);
    if (selected) item.setAttribute("aria-current", "page");
    else item.removeAttribute("aria-current");
  }
  for (const panel of panels) panel.classList.toggle("active", panel.id === tab.dataset.tab);
  text("workspaceName", tab.querySelector("span").textContent);
  if (scroll) window.scrollTo(0, 0);
  if (tab.dataset.tab === "ws-graph") visualizer?._setupCanvasSize();
}

async function loadSnapshot() {
  const [health, tickers] = await Promise.allSettled([api("/api/health"), api("/api/financials/tickers")]);
  const online = health.status === "fulfilled" && health.value.status === "healthy";
  byId("serviceStatus").parentElement.dataset.online = String(online);
  text("serviceStatus", online ? "Local engine online" : "Local engine unavailable");
  if (tickers.status !== "fulfilled") {
    text("tickerTapeTrack", "Snapshot unavailable");
    return;
  }
  const items = tickers.value.map(ticker => {
    const item = element("div", null, "ticker-item");
    const direction = ticker.change_pct >= 0 ? "ticker-up" : "ticker-down";
    const change = (ticker.change_pct >= 0 ? "+" : "") + ticker.change_pct.toFixed(2) + "%";
    item.append(element("span", ticker.ticker, "ticker-symbol"), element("span", "$" + ticker.price.toFixed(2)), element("span", change, direction));
    return item;
  });
  byId("tickerTapeTrack").replaceChildren(...items);
  fillSelect("valTickerSelect", tickers.value.map(ticker => [ticker.ticker, ticker.name + " · " + ticker.ticker]), "NVDA");
  loadValuation();
}

const headings = {
  ticker: "Ticker", company_name: "Company", sector: "Sector", country: "Country",
  market_cap_b: "Market cap ($B)", revenue_b: "Revenue ($B)", gross_margin_pct: "Gross margin (%)",
  operating_margin_pct: "Op. margin (%)", debt_to_equity: "Debt / equity"
};
let worksheet;
let selectedCell;
let sheetRequest = 0;
let savingCell = false;
let activeChartType = "BAR";
let chartRequest = 0;

function selectCell(cell) {
  const previous = byId("spreadsheetGrid").querySelector(".cell-selected");
  if (previous) {
    previous.classList.remove("cell-selected");
    previous.tabIndex = -1;
    previous.setAttribute("aria-selected", "false");
  }
  selectedCell = cell;
  cell.classList.add("cell-selected");
  cell.tabIndex = 0;
  cell.setAttribute("aria-selected", "true");
  text("formulaCoord", cell.dataset.coord);
  const input = byId("formulaInput");
  input.value = cell.dataset.value;
  input.disabled = savingCell || cell.dataset.column === "ticker";
  input.placeholder = cell.dataset.column === "ticker" ? "Ticker is a row identifier" : "Enter a value";
}

function buildTable(columns, rows, isWorksheet = false) {
  const head = element("thead");
  const header = element("tr");
  if (isWorksheet) header.append(element("th", "#", "col-corner"));
  for (const column of columns) {
    const cell = element("th", headings[column] || column.replaceAll("_", " "));
    cell.scope = "col";
    header.append(cell);
  }
  head.append(header);
  const body = element("tbody");
  rows.forEach((row, rowIndex) => {
    const line = element("tr");
    if (isWorksheet) line.append(element("td", rowIndex + 1, "row-num"));
    columns.forEach((column, columnIndex) => {
      const value = row[column];
      const cell = element("td", typeof value === "number" ? value.toLocaleString("en-US") : value ?? "—");
      if (isWorksheet) {
        cell.className = "editable-cell";
        cell.tabIndex = -1;
        cell.dataset.ticker = row.ticker;
        cell.dataset.column = column;
        cell.dataset.col = column;
        cell.dataset.value = value ?? "";
        cell.dataset.coord = String.fromCharCode(65 + columnIndex) + (rowIndex + 1);
        cell.setAttribute("role", "gridcell");
        cell.setAttribute("aria-selected", "false");
        cell.setAttribute("aria-readonly", String(column === "ticker"));
      }
      line.append(cell);
    });
    body.append(line);
  });
  return [head, body];
}

async function loadWorksheet() {
  const request = ++sheetRequest;
  const data = await api("/api/edi/sheet");
  if (request !== sheetRequest) return;
  worksheet = data;
  const grid = byId("spreadsheetGrid");
  const previous = selectedCell?.dataset;
  grid.replaceChildren(...buildTable(data.columns, data.rows, true));
  const cells = [...grid.querySelectorAll(".editable-cell")];
  const restored = cells.find(cell => cell.dataset.ticker === previous?.ticker && cell.dataset.column === previous?.column);
  const initial = restored || cells.find(cell => cell.dataset.column === "company_name") || cells[0];
  selectedCell = null;
  if (initial) selectCell(initial);
  else byId("formulaInput").disabled = true;
  const total = data.rows.reduce((sum, row) => sum + (row.market_cap_b ?? 0), 0);
  const margins = data.rows.map(row => row.operating_margin_pct).filter(Number.isFinite);
  text("sheetTotalRows", data.total_rows);
  text("sheetTotalCap", "$" + (total / 1000).toFixed(1) + "T");
  text("sheetAvgMargin", margins.length ? (margins.reduce((a, b) => a + b, 0) / margins.length).toFixed(1) + "%" : "—");
}

async function saveCell() {
  if (savingCell || !selectedCell || selectedCell.dataset.column === "ticker") return;
  const { ticker, column } = selectedCell.dataset;
  const value = byId("formulaInput").value;
  savingCell = true;
  byId("formulaInput").disabled = true;
  byId("btnRefreshSheet").disabled = true;
  try {
    await api("/api/edi/sheet/update", { ticker, column, value });
    await loadWorksheet();
    showToast(ticker + " " + headings[column] + " saved.");
    await loadChart(activeChartType);
  } catch (error) {
    showToast(error.message, "error");
  } finally {
    savingCell = false;
    byId("formulaInput").disabled = !selectedCell || selectedCell.dataset.column === "ticker";
    byId("btnRefreshSheet").disabled = false;
  }
}

function exportCsv() {
  if (!worksheet) return;
  function encode(value) {
    let field = String(value ?? "");
    if (typeof value === "string" && /^[\s]*[=+@-]/.test(field)) field = "'" + field;
    return '"' + field.replaceAll('"', '""') + '"';
  }
  const lines = [worksheet.columns.map(encode).join(",")];
  for (const row of worksheet.rows) lines.push(worksheet.columns.map(column => encode(row[column])).join(","));
  const url = URL.createObjectURL(new Blob([lines.join("\r\n")], { type: "text/csv;charset=utf-8" }));
  const link = element("a");
  link.href = url;
  link.download = "kuber-company-fundamentals.csv";
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

async function executeQuery() {
  const query = byId("ediQueryInput").value.trim();
  if (!query) return;
  await runAction(byId("btnRunEDI"), "Running…", async () => {
    const request = ++chartRequest;
    byId("ediAnswerCard").hidden = false;
    byId("queryDetails").hidden = true;
    text("ediAnswerText", "Looking up matching records…");
    try {
      const result = await api("/api/edi/query", { natural_query: query });
      text("ediAnswerText", result.natural_language_answer);
      text("ediLatencyBadge", result.execution_time_ms + " ms · " + result.grounded_record_count + " records");
      text("querySql", [result.generated_sql, result.generated_cypher].filter(Boolean).join("\n\n"));
      const table = element("table", null, "query-record-table");
      table.append(...buildTable(result.column_headers, result.rows));
      byId("queryRecords").replaceChildren(table);
      byId("queryDetails").hidden = !result.generated_sql && !result.rows.length;
      byId("queryDetails").open = false;
      if (request === chartRequest) {
        if (result.chart_spec) renderChart(result.chart_spec);
        else await loadChart(activeChartType);
      }
    } catch (error) {
      text("ediAnswerText", error.message);
      text("ediLatencyBadge", "Query failed");
    }
  });
}

function svgElement(tag, attributes, label) {
  const node = document.createElementNS(svgNS, tag);
  for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, value);
  if (label != null) node.textContent = label;
  return node;
}

function chartTooltip(node, label) {
  node.append(svgElement("title", {}, label));
  node.addEventListener("pointerenter", event => {
    const tooltip = byId("chartTooltip");
    const bounds = tooltip.parentElement.getBoundingClientRect();
    tooltip.textContent = label;
    tooltip.style.left = Math.max(5, Math.min(event.clientX - bounds.left + 8, bounds.width - tooltip.offsetWidth - 5)) + "px";
    tooltip.style.top = Math.max(3, event.clientY - bounds.top - 32) + "px";
    tooltip.style.opacity = "1";
  });
  node.addEventListener("pointerleave", () => { byId("chartTooltip").style.opacity = "0"; });
}

function renderChart(spec) {
  const svg = byId("chartSvg");
  svg.replaceChildren();
  byId("chartTooltip").style.opacity = "0";
  text("chartTitle", spec.title);
  const palette = ["#a34f3c", "#397665", "#78546a"];
  const legend = spec.series.map((series, index) => {
    const entry = element("span", series.name);
    entry.style.color = palette[index % palette.length];
    return entry;
  });
  byId("chartLegend").replaceChildren(...legend);
  for (const button of document.querySelectorAll(".chart-pill-btn")) {
    const selected = button.dataset.chart === spec.chart_type;
    button.classList.toggle("active", selected);
    button.setAttribute("aria-pressed", String(selected));
  }
  activeChartType = spec.chart_type;
  if (!spec.x_axis_labels.length || !spec.series.length) return;
  if (spec.chart_type === "RADAR") {
    renderRadar(svg, spec, palette);
    return;
  }

  const values = spec.series.flatMap(series => series.data_points);
  const minimum = Math.min(0, ...values);
  const maximum = Math.max(0, ...values);
  const range = maximum - minimum || 1;
  const x0 = 43;
  const chartWidth = 323;
  const y = value => 255 - (value - minimum) / range * 205;
  const slot = chartWidth / spec.x_axis_labels.length;
  const step = range / 4;
  for (let index = 0; index <= 4; index++) {
    const value = minimum + index * step;
    svg.append(svgElement("line", { x1: x0, x2: 366, y1: y(value), y2: y(value), stroke: "#dfcfc2", "stroke-dasharray": "3 3" }));
    svg.append(svgElement("text", { x: x0 - 6, y: y(value) + 3, fill: "#786761", "font-size": 9, "text-anchor": "end" }, value.toLocaleString("en-US", { maximumFractionDigits: 1 })));
  }
  spec.x_axis_labels.forEach((label, index) => svg.append(svgElement("text", {
    x: x0 + (index + .5) * slot, y: 280, fill: "#66534f", "font-size": 9, "text-anchor": "middle"
  }, label)));
  spec.series.forEach((series, seriesIndex) => {
    const color = palette[seriesIndex % palette.length];
    const points = series.data_points.map((value, index) => [x0 + (index + .5) * slot, y(value)]);
    if (spec.chart_type === "LINE") {
      svg.append(svgElement("polyline", { points: points.map(point => point.join(",")).join(" "), fill: "none", stroke: color, "stroke-width": 2.5 }));
    }
    const width = Math.min(34, slot * .72 / spec.series.length);
    points.forEach(([x, top], index) => {
      const value = series.data_points[index];
      const mark = spec.chart_type === "LINE"
        ? svgElement("circle", { cx: x, cy: top, r: 4.2, fill: color })
        : svgElement("rect", { class: "chart-svg-bar", x: x + (seriesIndex - spec.series.length / 2) * width, y: Math.min(top, y(0)), width: Math.max(1, width - 2), height: Math.max(1, Math.abs(top - y(0))), rx: 3, fill: color });
      chartTooltip(mark, spec.x_axis_labels[index] + " · " + series.name + ": " + value.toLocaleString("en-US"));
      svg.append(mark);
    });
  });
}

function renderRadar(svg, spec, palette) {
  const scale = Math.max(1, ...spec.series.flatMap(series => series.data_points));
  function point(index, ratio) {
    const angle = index / spec.x_axis_labels.length * Math.PI * 2 - Math.PI / 2;
    return [190 + Math.cos(angle) * 92 * ratio, 156 + Math.sin(angle) * 92 * ratio];
  }
  for (const ratio of [.25, .5, .75, 1]) {
    svg.append(svgElement("polygon", { points: spec.x_axis_labels.map((_, index) => point(index, ratio).join(",")).join(" "), fill: "none", stroke: "#d7c5ba" }));
  }
  spec.x_axis_labels.forEach((label, index) => {
    const [x, y] = point(index, 1.17);
    svg.append(svgElement("text", { x, y, "text-anchor": "middle", fill: "#66534f", "font-size": 9 }, label));
  });
  spec.series.forEach((series, index) => {
    const color = palette[index % palette.length];
    const points = series.data_points.map((value, axis) => point(axis, value / scale));
    svg.append(svgElement("polygon", { points: points.map(position => position.join(",")).join(" "), fill: color, "fill-opacity": ".15", stroke: color, "stroke-width": 2 }));
    points.forEach(([x, y], axis) => {
      const mark = svgElement("circle", { cx: x, cy: y, r: 4, fill: color });
      chartTooltip(mark, series.name + " · " + spec.x_axis_labels[axis] + ": " + series.data_points[axis]);
      svg.append(mark);
    });
  });
}

async function loadChart(chartType) {
  const request = ++chartRequest;
  try {
    const spec = await api("/api/edi/chart?chart_type=" + encodeURIComponent(chartType));
    if (request === chartRequest) renderChart(spec);
  } catch (error) {
    if (request === chartRequest) showToast(error.message, "error");
  }
}

function fillSelect(id, entries, fallback) {
  const select = byId(id);
  const prior = select.value;
  select.replaceChildren(...entries.map(([value, label]) => new Option(label, value)));
  if (entries.some(([value]) => value === prior)) select.value = prior;
  else if (fallback && entries.some(([value]) => value === fallback)) select.value = fallback;
}

async function loadWorkers() {
  const workers = await api("/api/crawler/workers");
  byId("scraperWorkersContainer").replaceChildren(...workers.map(worker => {
    const card = element("article", null, "worker-node-card");
    const head = element("div", null, "worker-header");
    head.append(element("strong", worker.region), element("span", worker.latency_ms + " ms", "worker-status-active"));
    card.append(head, element("p", worker.type, "worker-meta-line"));
    return card;
  }));
}

let crawlPending = false;
async function readSource(findEntities) {
  if (crawlPending) return;
  const input = byId("crawlUrlInput");
  if (!input.value.trim() || !input.reportValidity()) {
    showToast("Enter an HTTP or HTTPS document URL.", "error");
    return;
  }
  const url = input.value.trim();
  const strategy = byId("pruneStrategySelect").value;
  const query_context = byId("crawlContextInput").value.trim();
  if (strategy === "BM25_RELEVANCE" && !query_context) {
    showToast("Enter terms to rank the document by relevance.", "error");
    byId("crawlContextInput").focus();
    return;
  }
  const extraction = { strategy, query_context };
  const button = byId(findEntities ? "btnScrapeToSheet" : "btnExecuteCrawl");
  const other = byId(findEntities ? "btnExecuteCrawl" : "btnScrapeToSheet");
  crawlPending = true;
  other.disabled = true;
  byId("crawlEntities").replaceChildren();
  byId("crawlChunkDetails").hidden = true;
  byId("crawlChunkDetails").open = false;
  byId("crawlChunks").replaceChildren();
  for (const id of ["crawlRawChars", "crawlCleanChars", "crawlCompressionBadge"]) text(id, "—");
  text("crawlSourceStatus", "Reading document…");
  await runAction(button, "Reading…", async () => {
    try {
      let source, raw, clean, reduction, markdown, entities, chunks;
      if (findEntities) {
        const result = await api("/api/crawler/scrape-to-sheet", { url, ...extraction });
        ({ source, raw_bytes: raw, cleaned_bytes: clean, compression_pct: reduction, markdown_content: markdown, entities, chunks } = result);
      } else {
        const document = await api("/api/crawler/crawl", { url });
        const result = await api("/api/crawler/prune", { raw_html: document.raw_html, ...extraction });
        source = document.source;
        raw = document.raw_html_length;
        ({ cleaned_char_count: clean, compression_ratio_pct: reduction, markdown_content: markdown, chunks } = result);
      }
      text("crawlRawChars", raw.toLocaleString());
      text("crawlCleanChars", clean.toLocaleString());
      text("crawlCompressionBadge", reduction + "%");
      text("crawlMarkdownPreview", markdown || "No readable text was extracted.");
      text("crawlSourceStatus", source === "fixture" ? "Bundled sample document" : "Retrieved from the requested URL");
      if (chunks?.length) {
        byId("crawlChunks").replaceChildren(...chunks.map(chunk => {
          const article = element("article");
          article.append(element("strong", "Chunk " + chunk.chunk_index + " · " + chunk.word_count + " words"), element("p", chunk.content));
          return article;
        }));
        byId("crawlChunkDetails").hidden = false;
      }
      if (findEntities) {
        byId("crawlEntities").replaceChildren(...(entities.length ? entities.map(name => element("span", name, "small-badge")) : [element("p", "No known entities matched this document.", "panel-note")]));
      }
    } catch (error) {
      text("crawlSourceStatus", "Document could not be read.");
      text("crawlMarkdownPreview", error.message);
    }
  });
  other.disabled = false;
  crawlPending = false;
}

let graphNodes = [];
async function refreshGraph() {
  const data = await api("/api/graph/view");
  graphNodes = data.nodes;
  visualizer.loadGraphData(data);
  const companies = graphNodes.filter(item => item.type === "COMPANY").map(item => [item.id, item.label]);
  fillSelect("graphInspectSelect", graphNodes.map(item => [item.id, item.label]));
  fillSelect("pathSourceSelect", companies);
  fillSelect("pathTargetSelect", companies, companies[1]?.[0]);
  fillSelect("shockSourceSelect", companies, "company-tsm");
  const current = graphNodes.find(item => item.id === byId("graphInspectSelect").value);
  if (current) renderNode(current);
}

function renderNode(node) {
  byId("graphInspectSelect").value = node.id;
  const info = element("div", null, "node-detail");
  info.append(element("h3", node.label), element("p", node.sector || node.type, "panel-note"));
  const metrics = element("div", null, "ratio-grid");
  for (const [label, value] of [["Market cap", node.market_cap_b == null ? "—" : "$" + node.market_cap_b + "B"], ["Connections", node.degree ?? 0]]) {
    const item = element("div");
    item.append(element("span", label), element("strong", value));
    metrics.append(item);
  }
  info.append(metrics);
  byId("graphNodeDetail").replaceChildren(info);
}

async function findPath() {
  await runAction(byId("btnFindPath"), "Tracing…", async () => {
    const source_id = byId("pathSourceSelect").value;
    const target_id = byId("pathTargetSelect").value;
    if (!source_id || !target_id) return;
    const result = await api("/api/graph/shortest-path", { source_id, target_id });
    if (source_id !== byId("pathSourceSelect").value || target_id !== byId("pathTargetSelect").value) return;
    visualizer.highlightPath(result.found ? result.path_nodes : []);
    text("pathResultBox", result.strategic_summary);
  });
}

async function simulateShock() {
  await runAction(byId("btnSimulateShock"), "Simulating…", async () => {
    const shock_source_id = byId("shockSourceSelect").value;
    const shock_magnitude_pct = Number(byId("shockMagnitudeSlider").value);
    if (!shock_source_id) return;
    const result = await api("/api/graph/simulate-contagion", { shock_source_id, shock_magnitude_pct });
    if (shock_source_id !== byId("shockSourceSelect").value || shock_magnitude_pct !== Number(byId("shockMagnitudeSlider").value)) return;
    visualizer.triggerShockAnimation(shock_source_id);
    const title = element("strong", result.systemic_risk_level.replaceAll("_", " ") + " · $" + result.total_market_cap_at_risk_b + "B modeled exposure");
    byId("shockResultBox").replaceChildren(title, element("p", result.narrative_assessment), element("p", result.affected_nodes.map(node => node.label + " (" + node.shock_intensity_pct + "%)").join(", "), "panel-note"));
  });
}

let pipelines = [];
function renderPipeline(pipeline, run) {
  const nodes = pipeline?.nodes || [];
  byId("dagFlowSteps").replaceChildren(...nodes.map((node, index) => {
    const progress = run?.nodes_state[node.id];
    const status = progress?.status || "PENDING";
    const item = element("div", null, "dag-step-node status-" + status);
    const header = element("div", null, "dag-step-header");
    header.append(element("span", "STEP " + (index + 1)), element("span", status, "step-status-tag"));
    item.append(header, element("p", node.name, "dag-step-name"), element("p", progress?.duration_ms != null ? progress.duration_ms + " ms" : "—", "dag-step-duration"));
    return item;
  }));
}

async function loadPipelines() {
  pipelines = await api("/api/dag/pipelines");
  fillSelect("dagPipelineSelect", pipelines.map(item => [item.pipeline_id, item.title]));
  renderPipeline(pipelines.find(item => item.pipeline_id === byId("dagPipelineSelect").value));
}

async function runPipeline() {
  await runAction(byId("btnRunDAG"), "Running…", async () => {
    const select = byId("dagPipelineSelect");
    const pipeline = pipelines.find(item => item.pipeline_id === select.value);
    if (!pipeline) return;
    select.disabled = true;
    renderPipeline(pipeline);
    text("dagRunStatus", "Running");
    text("dagLogStream", "Starting " + pipeline.title + "…");
    text("dagExecutiveBrief", "Waiting for the run to finish.");
    try {
      const run = await api("/api/dag/execute/" + encodeURIComponent(pipeline.pipeline_id), {});
      renderPipeline(pipeline, run);
      text("dagRunStatus", run.status + " · " + run.total_duration_ms + " ms");
      text("dagLogStream", run.execution_logs.join("\n"));
      text("dagExecutiveBrief", run.run_artifacts?.executive_brief || "No brief was generated by this run.");
      await refreshGraph().catch(error => showToast("Graph refresh failed: " + error.message, "error"));
    } catch (error) {
      text("dagRunStatus", "Failed");
      text("dagLogStream", error.message);
      text("dagExecutiveBrief", "No brief was generated by this run.");
    } finally {
      select.disabled = false;
    }
  });
}

let valuationRequest = 0;
async function loadValuation() {
  const ticker = byId("valTickerSelect").value;
  if (!ticker) return;
  const request = ++valuationRequest;
  const fields = ["valHealthGrade", "valAltmanScore", "valAltmanZone", "valBeneishScore", "valBeneishRisk", "valGrossMargin", "valOperatingMargin", "valCurrentRatio", "valDebtEquity", "valPeRatio"];
  for (const id of fields) text(id, "—");
  byId("valAltmanPointer").hidden = true;
  text("valAltmanInterp", "Loading " + ticker + "…");
  try {
    const report = await api("/api/financials/ratios/" + encodeURIComponent(ticker));
    if (request !== valuationRequest) return;
    const altman = report.altman_z;
    const beneish = report.beneish_m;
    const values = [report.health_grade, altman.z_score.toFixed(2), altman.zone.replaceAll("_", " "), beneish.m_score.toFixed(2),
      beneish.manipulation_risk.replaceAll("_", " "), report.gross_margin_pct + "%", report.operating_margin_pct + "%",
      report.current_ratio, report.debt_to_equity, report.price_to_earnings];
    fields.forEach((id, index) => text(id, values[index]));
    text("valAltmanInterp", altman.clinical_interpretation);
    byId("valAltmanPointer").style.left = Math.min(100, Math.max(0, altman.z_score / 8 * 100)) + "%";
    byId("valAltmanPointer").hidden = false;
  } catch (error) {
    if (request === valuationRequest) text("valAltmanInterp", error.message);
  }
}

function boot() {
  if (location.protocol === "file:") {
    byId("fileProtocolWarning").hidden = false;
    return;
  }
  for (const tab of tabs) tab.addEventListener("click", () => { location.hash = tab.dataset.tab; });
  window.addEventListener("hashchange", () => activateWorkspace(true));
  document.querySelector(".skip-link").addEventListener("click", event => {
    event.preventDefault();
    const main = byId("main");
    main.focus({ preventScroll: true });
    main.scrollIntoView();
  });
  visualizer = new KuberGraphVisualizer("graphCanvas", renderNode);
  activateWorkspace();
  byId("queryForm").addEventListener("submit", event => { event.preventDefault(); executeQuery(); });
  for (const chip of document.querySelectorAll(".quick-prompt-chip")) chip.addEventListener("click", () => {
    if (byId("btnRunEDI").disabled) return;
    byId("ediQueryInput").value = chip.dataset.query;
    executeQuery();
  });
  for (const pill of document.querySelectorAll(".chart-pill-btn")) pill.addEventListener("click", () => loadChart(pill.dataset.chart));
  byId("btnRefreshSheet").addEventListener("click", () => runAction(byId("btnRefreshSheet"), "Refreshing…", loadWorksheet));
  byId("btnExportCSV").addEventListener("click", exportCsv);
  byId("formulaInput").addEventListener("keydown", event => { if (event.key === "Enter") saveCell(); });
  const sheet = byId("spreadsheetGrid");
  sheet.setAttribute("role", "grid");
  sheet.addEventListener("click", event => {
    const cell = event.target.closest(".editable-cell");
    if (cell) selectCell(cell);
  });
  sheet.addEventListener("dblclick", event => {
    if (event.target.closest(".editable-cell")) byId("formulaInput").focus();
  });
  sheet.addEventListener("keydown", event => {
    const cell = event.target.closest(".editable-cell");
    if (!cell) return;
    const row = cell.parentElement;
    const moves = {
      ArrowLeft: cell.previousElementSibling,
      ArrowRight: cell.nextElementSibling,
      ArrowUp: row.previousElementSibling?.cells[cell.cellIndex],
      ArrowDown: row.nextElementSibling?.cells[cell.cellIndex]
    };
    if (event.key === "Enter") {
      event.preventDefault();
      byId("formulaInput").focus();
    } else if (event.key in moves) {
      event.preventDefault();
      const next = moves[event.key];
      if (next?.classList.contains("editable-cell")) {
        selectCell(next);
        next.focus();
      }
    }
  });
  byId("crawlPresetSelect").addEventListener("change", event => {
    byId("crawlUrlInput").value = event.target.value === "custom" ? "" : event.target.value;
    if (event.target.value === "custom") byId("crawlUrlInput").focus();
  });
  byId("pruneStrategySelect").addEventListener("change", event => {
    byId("crawlContextField").hidden = event.target.value !== "BM25_RELEVANCE";
  });
  byId("btnExecuteCrawl").addEventListener("click", () => readSource(false));
  byId("btnScrapeToSheet").addEventListener("click", () => readSource(true));
  byId("graphInspectSelect").addEventListener("change", event => {
    const node = graphNodes.find(item => item.id === event.target.value);
    if (node) renderNode(node);
  });
  byId("btnZoomOut").addEventListener("click", () => visualizer.zoomBy(1 / 1.25));
  byId("btnZoomIn").addEventListener("click", () => visualizer.zoomBy(1.25));
  byId("btnResetZoom").addEventListener("click", () => visualizer.resetZoom());
  byId("btnFindPath").addEventListener("click", findPath);
  byId("btnSimulateShock").addEventListener("click", simulateShock);
  byId("shockMagnitudeSlider").addEventListener("input", event => text("shockMagnitudeVal", event.target.value + "%"));
  byId("dagPipelineSelect").addEventListener("change", event => {
    renderPipeline(pipelines.find(item => item.pipeline_id === event.target.value));
    text("dagRunStatus", "Ready");
    text("dagExecutiveBrief", "Run a pipeline to generate the brief.");
    text("dagLogStream", "Waiting for a run.");
  });
  byId("btnRunDAG").addEventListener("click", runPipeline);
  byId("valTickerSelect").addEventListener("change", loadValuation);
  loadSnapshot();
  loadWorksheet().catch(error => {
    byId("spreadsheetGrid").replaceChildren(element("caption", error.message));
  });
  loadChart(activeChartType);
  loadWorkers().catch(error => text("scraperWorkersContainer", error.message));
  refreshGraph().catch(error => text("graphNodeDetail", error.message));
  loadPipelines().catch(error => text("dagRunStatus", error.message));
}

boot();
