const scenarios = {
  deadline: {
    label: "Specific deadline",
    density: 0.68,
    conflict: 0.18,
    rows: [
      ["Jira", "Implementation ticket with the explicit due date", 0.92],
      ["Slack", "Decision discussion with related project context", 0.76],
      ["Confluence", "Technical plan without the delivery date", 0.69],
      ["Email", "Customer request that triggered the work", 0.63],
    ],
  },
  decision: {
    label: "Decision source",
    density: 0.62,
    conflict: 0.22,
    rows: [
      ["Slack", "Final decision from project channel", 0.9],
      ["Meeting", "Discussion transcript before the decision", 0.74],
      ["Confluence", "Spec page updated after approval", 0.71],
      ["Ticket", "Tracking item with partial context", 0.61],
    ],
  },
  spec: {
    label: "Technical spec",
    density: 0.58,
    conflict: 0.14,
    rows: [
      ["Confluence", "Current technical specification", 0.94],
      ["GitHub", "Pull request with implementation notes", 0.78],
      ["Ticket", "Engineering task with acceptance criteria", 0.68],
      ["Chat", "Design discussion with stale assumptions", 0.52],
    ],
  },
  customer: {
    label: "Customer request",
    density: 0.7,
    conflict: 0.2,
    rows: [
      ["Email", "Original customer request", 0.91],
      ["CRM", "Account note with business context", 0.81],
      ["Support", "Escalation item with impact summary", 0.72],
      ["Chat", "Internal triage thread", 0.58],
    ],
  },
  conflict: {
    label: "Conflicting facts",
    density: 0.75,
    conflict: 0.72,
    rows: [
      ["Confluence", "Approved current policy", 0.88],
      ["Email", "Older exception request", 0.8],
      ["Chat", "Informal statement with contradictory value", 0.73],
      ["Ticket", "Resolved item confirming final state", 0.7],
    ],
  },
};

const retrievers = {
  dense: { label: "Dense only", recall: 0.62, precision: 0.58, citation: 0.54, densityPenalty: 0.34 },
  bm25: { label: "BM25 only", recall: 0.68, precision: 0.53, citation: 0.58, densityPenalty: 0.18 },
  hybrid: { label: "Hybrid", recall: 0.76, precision: 0.64, citation: 0.67, densityPenalty: 0.14 },
  rerank: { label: "Hybrid rerank", recall: 0.82, precision: 0.7, citation: 0.74, densityPenalty: 0.09 },
};

const controls = {
  queryType: document.querySelector("#queryType"),
  retriever: document.querySelector("#retriever"),
  corpusSize: document.querySelector("#corpusSize"),
  topK: document.querySelector("#topK"),
  metadata: document.querySelector("#metadata"),
  authority: document.querySelector("#authority"),
  freshness: document.querySelector("#freshness"),
  conflictGuard: document.querySelector("#conflictGuard"),
  runComparison: document.querySelector("#runComparison"),
  resetControls: document.querySelector("#resetControls"),
};

const output = {
  runProfile: document.querySelector("#runProfile"),
  runSummary: document.querySelector("#runSummary"),
  corpusSizeValue: document.querySelector("#corpusSizeValue"),
  topKValue: document.querySelector("#topKValue"),
  recallValue: document.querySelector("#recallValue"),
  precisionValue: document.querySelector("#precisionValue"),
  citationValue: document.querySelector("#citationValue"),
  densityValue: document.querySelector("#densityValue"),
  recallBar: document.querySelector("#recallBar"),
  precisionBar: document.querySelector("#precisionBar"),
  citationBar: document.querySelector("#citationBar"),
  densityBar: document.querySelector("#densityBar"),
  diagnosticsPanel: document.querySelector("#diagnosticsPanel"),
  topKStatus: document.querySelector("#topKStatus"),
  conflictStatus: document.querySelector("#conflictStatus"),
  recommendation: document.querySelector("#recommendation"),
  candidateRows: document.querySelector("#candidateRows"),
  reviewCount: document.querySelector("#reviewCount"),
  lastRun: document.querySelector("#lastRun"),
  reviewItems: document.querySelector("#reviewItems"),
  evidencePolicy: document.querySelector("#evidencePolicy"),
  eventLog: document.querySelector("#eventLog"),
  progressState: document.querySelector("#progressState"),
  progressBar: document.querySelector("#progressBar"),
  progressSteps: document.querySelector("#progressSteps"),
};

const logItems = [];
let progressIndex = 0;
let progressTimer = 0;
let hasRun = false;

const progressSteps = [
  ["Read query", "Parse the request and any constraints."],
  ["Retrieve", "Collect dense, lexical, and hybrid candidates."],
  ["Rerank", "Apply metadata, authority, and freshness signals."],
  ["Check conflicts", "Flag contradictory evidence before generation."],
  ["Report", "Update metrics, evidence, and review actions."],
];

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function percentage(value) {
  return `${Math.round(clamp(value, 0, 1) * 100)}%`;
}

function formatScore(value) {
  return clamp(value, 0, 1).toFixed(2);
}

function calculateState() {
  const scenario = scenarios[controls.queryType.value];
  const retriever = retrievers[controls.retriever.value];
  const corpusSize = Number.parseInt(controls.corpusSize.value, 10);
  const topK = Number.parseInt(controls.topK.value, 10);
  const scalePressure = corpusSize / 500;
  const topKBoost = Math.log2(topK + 1) / 8;
  const signalBoost =
    (controls.metadata.checked ? 0.04 : 0) +
    (controls.authority.checked ? 0.03 : 0) +
    (controls.freshness.checked ? 0.025 : 0);
  const conflictPenalty = controls.conflictGuard.checked ? 0 : scenario.conflict * 0.09;
  const densityRisk = clamp(
    scenario.density * 0.58 + scalePressure * 0.38 + retriever.densityPenalty - signalBoost,
    0,
    1,
  );

  const recall = clamp(retriever.recall + topKBoost - densityRisk * 0.24 + signalBoost, 0.05, 0.98);
  const precision = clamp(
    retriever.precision - topK * 0.006 - densityRisk * 0.08 + signalBoost * 0.7,
    0.05,
    0.96,
  );
  const citation = clamp(
    retriever.citation - densityRisk * 0.16 + signalBoost + (controls.conflictGuard.checked ? 0.04 : 0) - conflictPenalty,
    0.05,
    0.97,
  );

  const topKStress = topK < 5 && densityRisk > 0.55;
  const conflictRisk = scenario.conflict > 0.5 && !controls.conflictGuard.checked;
  const precisionRisk = precision < 0.5;
  const severity =
    conflictRisk || densityRisk > 0.78 || recall < 0.45
      ? "error"
      : topKStress || precisionRisk || densityRisk > 0.62
        ? "warn"
        : "ok";

  return {
    scenario,
    retriever,
    corpusSize,
    topK,
    densityRisk,
    recall,
    precision,
    citation,
    topKStress,
    conflictRisk,
    precisionRisk,
    severity,
  };
}

function setBar(element, value) {
  element.style.width = percentage(value);
}

function setSeverity(element, severity) {
  element.classList.remove("warn", "error");
  if (severity === "warn" || severity === "error") {
    element.classList.add(severity);
  }
}

function metricSeverity(kind, value, state) {
  if (kind === "density") {
    if (state.severity === "error") return "error";
    if (value >= 0.62) return "warn";
    return "ok";
  }
  if (value < 0.5) return "error";
  if (value < 0.68) return "warn";
  return "ok";
}

function densityLabel(value) {
  if (value >= 0.72) return "High";
  if (value >= 0.46) return "Medium";
  return "Low";
}

function updateRows(state) {
  output.candidateRows.replaceChildren();
  state.scenario.rows.slice(0, Math.min(4, state.topK)).forEach((row, index) => {
    const tr = document.createElement("tr");
    const rank = document.createElement("td");
    const source = document.createElement("td");
    const evidence = document.createElement("td");
    const score = document.createElement("td");

    rank.textContent = String(index + 1);
    source.textContent = row[0];
    evidence.textContent = row[1];
    score.textContent = formatScore(row[2] - state.densityRisk * 0.08 + state.recall * 0.04);

    tr.append(rank, source, evidence, score);
    output.candidateRows.append(tr);
  });
}

function reviewQueue(state) {
  const items = [];
  if (state.densityRisk > 0.7) {
    items.push(["High density", "Increase candidate depth or strengthen reranking before generation."]);
  }
  if (state.scenario.conflict > 0.5) {
    items.push(["Conflicting evidence", "Compare final-source evidence before accepting an answer."]);
  }
  if (state.precision < 0.5) {
    items.push(["Low precision", "Candidate set may include too much related but incomplete evidence."]);
  }
  if (items.length === 0) {
    items.push(["No blocking review", "Current settings are suitable for the selected scenario."]);
  }
  return items;
}

function updateReviewQueue(state) {
  const items = reviewQueue(state);
  output.reviewCount.textContent = `${items.length} ${items.length === 1 ? "item" : "items"}`;
  output.reviewItems.replaceChildren();
  items.forEach(([title, body]) => {
    const li = document.createElement("li");
    const strong = document.createElement("strong");
    const span = document.createElement("span");
    strong.textContent = title;
    span.textContent = body;
    if (title === "High density" || title === "Conflicting evidence") {
      li.className = state.severity;
    } else if (title === "Low precision") {
      li.className = "warn";
    }
    li.append(strong, span);
    output.reviewItems.append(li);
  });
}

function updateConfigSummary(state) {
  output.evidencePolicy.textContent = controls.conflictGuard.checked
    ? "Cite top candidate and flag conflicts"
    : "Cite top candidate without conflict blocking";
  output.lastRun.textContent = `${state.retriever.label}, top-k ${state.topK}`;
}

function updateEventLog() {
  output.eventLog.replaceChildren();
  logItems.slice(-5).forEach((entry) => {
    const li = document.createElement("li");
    const strong = document.createElement("strong");
    const span = document.createElement("span");
    strong.textContent = entry.level.toUpperCase();
    span.textContent = entry.message;
    li.className = entry.level === "error" ? "error" : entry.level === "warn" ? "warn" : "";
    li.append(strong, span);
    output.eventLog.prepend(li);
  });
}

function updateProgressWindow() {
  const state = calculateState();
  output.progressSteps.replaceChildren();
  progressSteps.forEach(([title, body], index) => {
    const li = document.createElement("li");
    const strong = document.createElement("strong");
    const span = document.createElement("span");
    strong.textContent = title;
    span.textContent = body;
    if (index < progressIndex) {
      li.className = "done";
    } else if (index === progressIndex) {
      li.className = "active";
    }
    if (
      state.severity === "error" &&
      ((state.conflictRisk && title === "Check conflicts") ||
        (state.densityRisk > 0.78 && title === "Retrieve"))
    ) {
      li.className = index <= progressIndex || progressIndex >= progressSteps.length ? "error" : li.className;
    } else if (state.severity === "warn" && title === "Rerank") {
      li.className = index <= progressIndex || progressIndex >= progressSteps.length ? "warn" : li.className;
    }
    li.append(strong, span);
    output.progressSteps.append(li);
  });
  const percent = progressIndex / progressSteps.length;
  output.progressBar.style.width = percentage(percent);
  setSeverity(output.progressBar.parentElement, state.severity);
  if (!hasRun) {
    output.progressState.textContent = "Idle";
  } else {
    output.progressState.textContent = progressIndex >= progressSteps.length ? "Complete" : "Running";
  }
}

function updateDiagnostics(state) {
  setSeverity(output.diagnosticsPanel, state.severity);

  output.topKStatus.textContent = state.topKStress
    ? "Likely to miss fact-bearing evidence. Increase top-k or add stronger ranking signals."
    : "Candidate set has enough room for this simulation.";

  output.conflictStatus.textContent = state.conflictRisk
    ? "Conflicting evidence is likely to reach generation without an explicit guard."
    : "Contradictory evidence is either low-risk or flagged by the guard.";

  if (state.densityRisk > 0.72) {
    output.recommendation.textContent =
      "Use hybrid retrieval, reranking, and metadata constraints before increasing generation scope.";
  } else if (state.precision < 0.45) {
    output.recommendation.textContent =
      "Top-k is broad enough for recall, but precision is weak. Add reranking or authority scoring.";
  } else {
    output.recommendation.textContent =
      "Current settings are balanced for this scenario. Review evidence before answer generation.";
  }
}

function render() {
  const state = calculateState();

  output.runProfile.textContent = state.retriever.label;
  output.runSummary.textContent = `${state.scenario.label}, ${state.corpusSize}k corpus, top-k ${state.topK}`;
  output.corpusSizeValue.textContent = `${state.corpusSize}k`;
  output.topKValue.textContent = String(state.topK);
  output.recallValue.textContent = formatScore(state.recall);
  output.precisionValue.textContent = formatScore(state.precision);
  output.citationValue.textContent = formatScore(state.citation);
  output.densityValue.textContent = densityLabel(state.densityRisk);

  setBar(output.recallBar, state.recall);
  setBar(output.precisionBar, state.precision);
  setBar(output.citationBar, state.citation);
  setBar(output.densityBar, state.densityRisk);
  setSeverity(output.recallBar.parentElement, metricSeverity("recall", state.recall, state));
  setSeverity(output.precisionBar.parentElement, metricSeverity("precision", state.precision, state));
  setSeverity(output.citationBar.parentElement, metricSeverity("citation", state.citation, state));
  setSeverity(output.densityBar.parentElement, metricSeverity("density", state.densityRisk, state));
  setSeverity(output.recallBar.closest("article"), metricSeverity("recall", state.recall, state));
  setSeverity(output.precisionBar.closest("article"), metricSeverity("precision", state.precision, state));
  setSeverity(output.citationBar.closest("article"), metricSeverity("citation", state.citation, state));
  setSeverity(output.densityBar.closest("article"), metricSeverity("density", state.densityRisk, state));

  updateDiagnostics(state);
  updateRows(state);
  updateReviewQueue(state);
  updateConfigSummary(state);
  updateEventLog();
  updateProgressWindow();
}

function resetControls() {
  window.clearInterval(progressTimer);
  hasRun = false;
  progressIndex = 0;
  controls.queryType.value = "deadline";
  controls.retriever.value = "rerank";
  controls.corpusSize.value = "80";
  controls.topK.value = "8";
  controls.metadata.checked = true;
  controls.authority.checked = true;
  controls.freshness.checked = true;
  controls.conflictGuard.checked = true;
  recordLog("info", "Controls reset to the default profile.");
  render();
}

function runComparison() {
  const state = calculateState();
  window.clearInterval(progressTimer);
  hasRun = true;
  progressIndex = 0;
  recordLog(
    state.severity,
    `Compared ${state.retriever.label} on ${state.scenario.label.toLowerCase()} at ${state.corpusSize}k corpus.`,
  );
  render();
  progressTimer = window.setInterval(() => {
    progressIndex += 1;
    if (progressIndex >= progressSteps.length) {
      window.clearInterval(progressTimer);
      progressIndex = progressSteps.length;
      recordLog(state.severity, "Run completed and review actions updated.");
    }
    render();
  }, 520);
}

function recordLog(level, message, details = {}) {
  const entry = {
    level: level === "error" || level === "warn" ? level : "info",
    message,
    details,
    timestamp: new Date().toISOString(),
  };
  logItems.push(entry);
  writeExternalLog(entry);
}

function writeExternalLog(entry) {
  if (window.location.protocol !== "http:" && window.location.protocol !== "https:") {
    return;
  }
  const payload = JSON.stringify(entry);
  if (navigator.sendBeacon) {
    navigator.sendBeacon("/events", new Blob([payload], { type: "application/json" }));
    return;
  }
  window
    .fetch("/events", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: payload,
      keepalive: true,
    })
    .catch(() => undefined);
}

window.addEventListener("error", (event) => {
  recordLog("error", "Unhandled dashboard error.", {
    message: event.message,
    source: event.filename,
    line: event.lineno,
    column: event.colno,
  });
});

window.addEventListener("unhandledrejection", (event) => {
  recordLog("error", "Unhandled dashboard promise rejection.", {
    reason: String(event.reason),
  });
});

[
  controls.queryType,
  controls.retriever,
  controls.corpusSize,
  controls.topK,
  controls.metadata,
  controls.authority,
  controls.freshness,
  controls.conflictGuard,
].forEach((control) => {
  control.addEventListener("input", render);
});

controls.resetControls.addEventListener("click", resetControls);
controls.runComparison.addEventListener("click", runComparison);

recordLog("info", "Dashboard loaded with local sample state.");
render();
