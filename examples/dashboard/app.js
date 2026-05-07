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

const scenarioPresets = {
  deadline: { corpusSize: "95", topK: "8", signalLevel: 4 },
  decision: { corpusSize: "120", topK: "9", signalLevel: 4 },
  spec: { corpusSize: "70", topK: "7", signalLevel: 3 },
  customer: { corpusSize: "140", topK: "10", signalLevel: 4 },
  conflict: { corpusSize: "180", topK: "12", signalLevel: 4 },
};

const controls = {
  queryType: document.querySelector("#queryType"),
  retriever: document.querySelector("#retriever"),
  corpusSize: document.querySelector("#corpusSize"),
  signalLevel: document.querySelector("#signalLevel"),
  topK: document.querySelector("#topK"),
  metadata: document.querySelector("#metadata"),
  authority: document.querySelector("#authority"),
  freshness: document.querySelector("#freshness"),
  conflictGuard: document.querySelector("#conflictGuard"),
  adviserMode: document.querySelector("#adviserMode"),
  adviserModel: document.querySelector("#adviserModel"),
  runAdviser: document.querySelector("#runAdviser"),
  runComparison: document.querySelector("#runComparison"),
  stopSimulation: document.querySelector("#stopSimulation"),
  resetControls: document.querySelector("#resetControls"),
  detailToggle: document.querySelector("#detailToggle"),
  knobs: document.querySelectorAll("[data-knob]"),
  themeDots: document.querySelectorAll("[data-theme-dot]"),
  infoButtons: document.querySelectorAll(".info-button"),
};

const output = {
  runProfile: document.querySelector("#runProfile"),
  runSummary: document.querySelector("#runSummary"),
  corpusSizeValue: document.querySelector("#corpusSizeValue"),
  signalLevelValue: document.querySelector("#signalLevelValue"),
  topKValue: document.querySelector("#topKValue"),
  recallValue: document.querySelector("#recallValue"),
  precisionValue: document.querySelector("#precisionValue"),
  citationValue: document.querySelector("#citationValue"),
  densityValue: document.querySelector("#densityValue"),
  knobDocsValue: document.querySelector("#knobDocsValue"),
  knobSignalsValue: document.querySelector("#knobSignalsValue"),
  knobTopKValue: document.querySelector("#knobTopKValue"),
  recallBar: document.querySelector("#recallBar"),
  precisionBar: document.querySelector("#precisionBar"),
  citationBar: document.querySelector("#citationBar"),
  densityBar: document.querySelector("#densityBar"),
  diagnosticsPanel: document.querySelector("#diagnosticsPanel"),
  topKStatus: document.querySelector("#topKStatus"),
  conflictStatus: document.querySelector("#conflictStatus"),
  recommendation: document.querySelector("#recommendation"),
  summaryPanel: document.querySelector("#summaryPanel"),
  summaryHealth: document.querySelector("#summaryHealth"),
  summaryState: document.querySelector("#summaryState"),
  summaryItems: document.querySelector("#summaryItems"),
  candidateRows: document.querySelector("#candidateRows"),
  reviewCount: document.querySelector("#reviewCount"),
  lastRun: document.querySelector("#lastRun"),
  reviewItems: document.querySelector("#reviewItems"),
  evidencePolicy: document.querySelector("#evidencePolicy"),
  eventLog: document.querySelector("#eventLog"),
  progressState: document.querySelector("#progressState"),
  progressBar: document.querySelector("#progressBar"),
  progressSteps: document.querySelector("#progressSteps"),
  simulationCanvas: document.querySelector("#simulationCanvas"),
  pipelineSvg: document.querySelector("#pipelineSvg"),
  qualityNeedle: document.querySelector("#qualityNeedle"),
  qualityScoreValue: document.querySelector("#qualityScoreValue"),
  pipelineHealth: document.querySelector("#pipelineHealth"),
  pipelineGraph: document.querySelector("#pipelineGraph"),
  bottleneckList: document.querySelector("#bottleneckList"),
  fixSuggestions: document.querySelector("#fixSuggestions"),
  adapterOutput: document.querySelector("#adapterOutput"),
  adviserStatus: document.querySelector("#adviserStatus"),
  adviserProblem: document.querySelector("#adviserProblem"),
  adviserWhy: document.querySelector("#adviserWhy"),
  adviserFix: document.querySelector("#adviserFix"),
  adviserRisk: document.querySelector("#adviserRisk"),
  infoTooltip: document.querySelector("#infoTooltip"),
};

const logItems = [];
const svgNamespace = ["http:", "//www.w3.org/2000/svg"].join("");
let progressIndex = 0;
let progressTimer = 0;
let hasRun = false;
let isStopped = false;
let activeInfoButton = null;
let infoTooltipPinned = false;
let connectorFrame = 0;

const progressSteps = [
  ["Adapter", "Normalise external retriever output."],
  ["Retrieve", "Collect dense, lexical, and hybrid candidates."],
  ["Density scan", "Measure candidate crowding and near-neighbour pressure."],
  ["Rerank", "Apply metadata, authority, and freshness signals."],
  ["Conflict gate", "Flag contradictory evidence before generation."],
  ["LLM gate", "Approve context or block generation."],
  ["Telemetry", "Persist diagnostics, errors, and review actions."],
];

const stageSymbols = new Map([
  [1, "+"],
  [2, "▽"],
  [3, "≡"],
  [4, "×"],
  [5, "✓"],
]);

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
  const stages = pipelineStages(state);
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
    const pipelineStage = stages.find((stage) => stage.title === title);
    if (pipelineStage && pipelineStage.severity !== "ok") {
      li.className =
        index <= progressIndex || progressIndex >= progressSteps.length
          ? pipelineStage.severity
          : li.className;
    }
    li.append(strong, span);
    output.progressSteps.append(li);
  });
  const percent = progressIndex / progressSteps.length;
  output.progressBar.style.width = percentage(percent);
  setSeverity(output.progressBar.parentElement, state.severity);
  if (!hasRun) {
    output.progressState.textContent = "Idle";
  } else if (isStopped) {
    output.progressState.textContent = "Stopped";
  } else {
    output.progressState.textContent = progressIndex >= progressSteps.length ? "Complete" : "Running";
  }
}

function updateKnobs(state) {
  const enabledSignals = enabledSignalCount();
  controls.knobs.forEach((knob) => {
    const dial = knob.querySelector(".dial span");
    if (!dial) return;
    if (knob.dataset.knob === "docs") {
      dial.style.setProperty("--turn", `${-58 + (state.corpusSize / 500) * 116}deg`);
      output.knobDocsValue.textContent = `${state.corpusSize}k`;
      knob.setAttribute("aria-label", `Adjust corpus size. Current value ${state.corpusSize}k documents.`);
    }
    if (knob.dataset.knob === "signals") {
      dial.style.setProperty("--turn", `${-58 + (enabledSignals / 4) * 116}deg`);
      output.knobSignalsValue.textContent = `${enabledSignals}/4`;
      knob.setAttribute("aria-label", `Adjust scoring signals. Current value ${enabledSignals} of 4 enabled.`);
    }
    if (knob.dataset.knob === "topk") {
      dial.style.setProperty("--turn", `${-58 + (state.topK / 30) * 116}deg`);
      output.knobTopKValue.textContent = String(state.topK);
      knob.setAttribute("aria-label", `Adjust top-k. Current value ${state.topK}.`);
    }
  });
  controls.signalLevel.value = String(enabledSignals);
  output.signalLevelValue.textContent = `${enabledSignals}/4`;
}

function enabledSignalCount() {
  return [
    controls.metadata.checked,
    controls.authority.checked,
    controls.freshness.checked,
    controls.conflictGuard.checked,
  ].filter(Boolean).length;
}

function setSignalLevel(level) {
  const nextLevel = clamp(level, 1, 4);
  controls.signalLevel.value = String(nextLevel);
  controls.metadata.checked = nextLevel >= 1;
  controls.authority.checked = nextLevel >= 2;
  controls.freshness.checked = nextLevel >= 3;
  controls.conflictGuard.checked = nextLevel >= 4;
}

function applyScenarioPreset(scenarioKey) {
  const preset = scenarioPresets[scenarioKey];
  if (!preset) return;
  controls.corpusSize.value = preset.corpusSize;
  controls.topK.value = preset.topK;
  setSignalLevel(preset.signalLevel);
}

function handleKnobPress(event) {
  const knob = event.currentTarget.dataset.knob;
  if (knob === "docs") {
    const current = Number.parseInt(controls.corpusSize.value, 10);
    controls.corpusSize.value = current >= 500 ? "5" : String(Math.min(500, current + 55));
  }
  if (knob === "signals") {
    const nextLevel = enabledSignalCount() >= 4 ? 1 : enabledSignalCount() + 1;
    setSignalLevel(nextLevel);
  }
  if (knob === "topk") {
    const current = Number.parseInt(controls.topK.value, 10);
    controls.topK.value = current >= 30 ? "1" : String(Math.min(30, current + 3));
  }
  recordLog("info", "Stack knob changed the simulation profile.", { knob });
  render();
}

function activeSimulationStage() {
  if (!hasRun) {
    return -1;
  }
  if (progressIndex <= 0) {
    return 0;
  }
  if (progressIndex >= progressSteps.length - 1) {
    return 5;
  }
  return Math.min(progressIndex, 5);
}

function simulationStageSeverity(stage, state) {
  if (stage === 2 && state.densityRisk > 0.78) return "error";
  if (stage === 2 && state.densityRisk > 0.62) return "warn";
  if (stage === 3 && state.precisionRisk) return "warn";
  if (stage === 4 && state.conflictRisk) return "error";
  if (stage === 4 && state.scenario.conflict > 0.5) return "warn";
  if (stage === 5 && state.severity === "error") return "error";
  if (stage === 5 && state.severity === "warn") return "warn";
  return "ok";
}

function relativeRect(element, containerRect) {
  const rect = element.getBoundingClientRect();
  return {
    left: rect.left - containerRect.left,
    right: rect.right - containerRect.left,
    top: rect.top - containerRect.top,
    bottom: rect.bottom - containerRect.top,
    width: rect.width,
    height: rect.height,
    centreX: rect.left - containerRect.left + rect.width / 2,
    centreY: rect.top - containerRect.top + rect.height / 2,
  };
}

function centrePoint(element, containerRect) {
  const rect = relativeRect(element, containerRect);
  return { x: rect.centreX, y: rect.centreY };
}

function sidePoint(element, containerRect, side) {
  const rect = relativeRect(element, containerRect);
  return {
    x: side === "right" ? rect.right : rect.left,
    y: rect.centreY,
  };
}

function connectorCurve(from, to, bend = 0.48) {
  const distance = Math.abs(to.x - from.x);
  const control = Math.max(42, distance * bend);
  return `M${from.x.toFixed(1)} ${from.y.toFixed(1)} C${(from.x + control).toFixed(1)} ${from.y.toFixed(1)} ${(to.x - control).toFixed(1)} ${to.y.toFixed(1)} ${to.x.toFixed(1)} ${to.y.toFixed(1)}`;
}

function createSvgPath(connector) {
  const path = document.createElementNS(svgNamespace, "path");
  path.setAttribute("class", connector.className);
  path.setAttribute("data-flow", String(connector.flow));
  path.setAttribute("d", connector.d);
  return path;
}

function updateConnectorPaths() {
  const canvas = output.simulationCanvas;
  const svg = output.pipelineSvg;
  if (!canvas || !svg) return;

  const canvasRect = canvas.getBoundingClientRect();
  const queryTarget = canvas.querySelector(".query-orb span");
  const sourceTargets = [...canvas.querySelectorAll(".source-dot")];
  const stageTargets = [...canvas.querySelectorAll(".sim-stage")];
  const documentTargets = [...canvas.querySelectorAll(".document-stack div")];
  if (!queryTarget || stageTargets.length === 0) return;

  svg.setAttribute("viewBox", `0 0 ${canvasRect.width.toFixed(1)} ${canvasRect.height.toFixed(1)}`);
  const query = centrePoint(queryTarget, canvasRect);
  const firstStage = stageTargets[0];
  const finalStage = stageTargets.at(-1);
  const connectors = [];

  sourceTargets.forEach((source, index) => {
    const sourceCentre = centrePoint(source, canvasRect);
    connectors.push({
      className: `flow-path branch source-${index + 1}`,
      flow: 0,
      d: connectorCurve(query, sourceCentre, 0.34),
    });
    connectors.push({
      className: `flow-path merge source-merge-${index + 1}`,
      flow: 1,
      d: connectorCurve(sourceCentre, sidePoint(firstStage, canvasRect, "left"), 0.42),
    });
  });

  stageTargets.slice(0, -1).forEach((stage, index) => {
    connectors.push({
      className: `flow-path main-flow main-${index + 1}`,
      flow: index + 1,
      d: connectorCurve(sidePoint(stage, canvasRect, "right"), sidePoint(stageTargets[index + 1], canvasRect, "left"), 0.5),
    });
  });

  if (finalStage) {
    documentTargets.forEach((documentNode, index) => {
      connectors.push({
        className: `flow-path output output-${index + 1}`,
        flow: 5,
        d: connectorCurve(sidePoint(finalStage, canvasRect, "right"), sidePoint(documentNode, canvasRect, "left"), 0.42),
      });
    });
  }

  svg.replaceChildren(...connectors.map(createSvgPath));
}

function updateSimulationCanvas(state) {
  const activeStage = activeSimulationStage();
  updateConnectorPaths();
  output.simulationCanvas.classList.remove("running", "warn", "error");
  if (hasRun && !isStopped && progressIndex < progressSteps.length) {
    output.simulationCanvas.classList.add("running");
  }
  if (hasRun && state.severity !== "ok") {
    output.simulationCanvas.classList.add(state.severity);
  }

  output.simulationCanvas.querySelectorAll(".sim-node").forEach((node) => {
    const stage = Number.parseInt(node.dataset.stage || "-1", 10);
    const severity = simulationStageSeverity(stage, state);
    const icon = node.matches(".sim-stage") ? node.querySelector("strong") : null;
    node.classList.remove("active", "warn", "error", "done");
    if (hasRun && stage < activeStage) {
      node.classList.add("done");
    }
    if (hasRun && stage === activeStage) {
      node.classList.add("active");
    }
    if (hasRun && severity !== "ok" && stage <= activeStage) {
      node.classList.add(severity);
    }
    if (icon && stageSymbols.has(stage)) {
      icon.dataset.symbol = stageSymbols.get(stage);
    }
  });

  const activeLineCount = activeStage < 0 ? 0 : Math.min(activeStage + 1, 6);
  output.simulationCanvas.querySelectorAll(".flow-line").forEach((line, index) => {
    line.classList.remove("active", "warn", "error");
    if (index < activeLineCount) {
      line.classList.add("active");
      if (hasRun && state.severity !== "ok" && index >= 3) {
        line.classList.add(state.severity);
      }
    }
  });

  output.simulationCanvas.querySelectorAll(".flow-path").forEach((path) => {
    const flowStage = Number.parseInt(path.dataset.flow || "0", 10);
    path.classList.remove("active", "warn", "error");
    if (hasRun && flowStage <= activeStage) {
      path.classList.add("active");
    }
    if (hasRun && state.severity !== "ok" && flowStage >= 4 && flowStage <= activeStage) {
      path.classList.add(state.severity);
    }
  });

  const documents = output.simulationCanvas.querySelector(".document-stack");
  documents.classList.remove("active", "warn", "error");
  if (hasRun && activeStage >= 5) {
    documents.classList.add("active");
    if (state.severity !== "ok") {
      documents.classList.add(state.severity);
    }
  }

  const qualityScore = clamp(state.recall * 0.45 + state.precision * 0.35 + state.citation * 0.2, 0, 1);
  const angle = -58 + qualityScore * 116;
  output.qualityNeedle.style.transform = `translateX(-50%) rotate(${angle.toFixed(1)}deg)`;
  output.qualityScoreValue.textContent = formatScore(qualityScore);
  setSeverity(output.qualityNeedle.closest(".quality-gauge"), state.severity);
}

function pipelineStages(state) {
  return [
    {
      title: "Adapter",
      status: "Normalised",
      detail: "Accepts SearchResult, document objects, or dictionaries from an existing retriever.",
      severity: "ok",
    },
    {
      title: "Retrieve",
      status: state.densityRisk > 0.78 ? "Crowded" : "Collected",
      detail: `${state.topK} visible candidates from ${state.retriever.label}.`,
      severity: state.densityRisk > 0.78 ? "error" : state.densityRisk > 0.62 ? "warn" : "ok",
    },
    {
      title: "Density scan",
      status: densityLabel(state.densityRisk),
      detail: "Checks whether related documents are competing for the same top-k slots.",
      severity: state.densityRisk > 0.78 ? "error" : state.densityRisk > 0.62 ? "warn" : "ok",
    },
    {
      title: "Rerank",
      status: state.precisionRisk ? "Weak precision" : "Ranked",
      detail: "Combines retrieval score, metadata, source authority, and freshness signals.",
      severity: state.precisionRisk ? "warn" : state.densityRisk > 0.62 ? "warn" : "ok",
    },
    {
      title: "Conflict gate",
      status: state.conflictRisk ? "Blocking issue" : "Checked",
      detail: state.conflictRisk ? "Contradictory facts would reach generation." : "No blocking contradiction.",
      severity: state.conflictRisk ? "error" : state.scenario.conflict > 0.5 ? "warn" : "ok",
    },
    {
      title: "LLM gate",
      status: state.severity === "error" ? "Do not generate" : "Context approved",
      detail:
        state.severity === "error"
          ? "Return a retrieval failure or request review before calling the model."
          : "Approved evidence can be packaged for any model provider.",
      severity: state.severity,
    },
    {
      title: "Telemetry",
      status: "Logged",
      detail: "Writes local events and can be forwarded to external observability.",
      severity: state.severity === "error" ? "warn" : "ok",
    },
  ];
}

function bottlenecks(state) {
  const retrievalLoad = clamp(state.corpusSize / 500 + state.densityRisk * 0.42, 0, 1);
  const rerankLoad = clamp((state.topK / 30) * 0.52 + state.densityRisk * 0.36, 0, 1);
  const conflictLoad = clamp(state.scenario.conflict + (controls.conflictGuard.checked ? -0.22 : 0.12), 0, 1);
  const contextLoad = clamp((1 - state.precision) * 0.7 + state.topK / 60, 0, 1);
  return [
    ["Candidate pressure", retrievalLoad, "More near-related documents are competing for top-k slots."],
    ["Rerank work", rerankLoad, "Candidate volume and source signals increase ranking cost."],
    ["Conflict review", conflictLoad, "Contradictory facts require review before model generation."],
    ["Context packaging", contextLoad, "Low precision increases irrelevant context sent downstream."],
  ];
}

function severityForLoad(value) {
  if (value >= 0.78) return "error";
  if (value >= 0.58) return "warn";
  return "ok";
}

function fixSuggestions(state) {
  const suggestions = [];
  if (state.densityRisk > 0.72) {
    suggestions.push(["Reduce crowding", "Increase candidate depth, add lexical retrieval, then rerank with source metadata."]);
  }
  if (state.conflictRisk) {
    suggestions.push(["Block generation", "Return a conflict response until final-source evidence is selected."]);
  }
  if (state.precision < 0.55) {
    suggestions.push(["Improve precision", "Lower top-k after reranking or apply authority and freshness scoring first."]);
  }
  if (state.severity !== "error") {
    suggestions.push(["Safe model handoff", "Send only approved context to the model and keep citation checks active."]);
  }
  suggestions.push([
    "Optional model adviser",
    "Attach a suggestion provider to turn guard issues into remediation text for your team.",
  ]);
  return suggestions;
}

function summaryRecommendations(state) {
  const items = [];
  if (state.densityRisk > 0.72) {
    items.push("Candidate set is crowded. Increase candidate depth and rerank before generation.");
  } else {
    items.push("Candidate set has room for this simulation.");
  }
  if (state.conflictRisk) {
    items.push("Conflicting evidence can reach generation. Block model handoff until final evidence is selected.");
  } else {
    items.push("Contradictory factors are low or flagged by the guard.");
  }
  if (state.precision < 0.55) {
    items.push("Precision is weak. Tighten reranking, authority scoring, and freshness scoring.");
  } else if (state.severity !== "error") {
    items.push("Current settings are balanced for this scenario before generation.");
  }
  if (state.topKStress) {
    items.push("Top-k is tight for this density. Increase visible candidates before the rerank step.");
  }
  return items;
}

function updateSummaryPanel(state) {
  const status =
    state.severity === "error"
      ? ["Red: Blocked", "error"]
      : state.severity === "warn"
        ? ["Amber: Review", "warn"]
        : ["Green: Healthy", "ok"];

  setSeverity(output.summaryPanel, status[1]);
  setSeverity(output.summaryHealth, status[1]);
  output.summaryState.textContent = status[0];
  output.summaryItems.replaceChildren();
  summaryRecommendations(state).forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    output.summaryItems.append(li);
  });
}

function updatePipelineView(state) {
  const stages = pipelineStages(state);
  output.pipelineHealth.textContent =
    state.severity === "error" ? "Blocked" : state.severity === "warn" ? "Review" : "Healthy";
  setSeverity(output.pipelineHealth, state.severity);
  output.pipelineGraph.replaceChildren();
  stages.forEach((stage, index) => {
    const article = document.createElement("article");
    const title = document.createElement("strong");
    const status = document.createElement("span");
    const detail = document.createElement("p");
    title.textContent = stage.title;
    status.textContent = stage.status;
    detail.textContent = stage.detail;
    article.className = `pipeline-node ${stage.severity}`;
    if (hasRun && index === Math.min(progressIndex, stages.length - 1)) {
      article.classList.add("active");
    }
    article.append(title, status, detail);
    output.pipelineGraph.append(article);
  });

  output.bottleneckList.replaceChildren();
  bottlenecks(state).forEach(([title, value, body]) => {
    const li = document.createElement("li");
    const strong = document.createElement("strong");
    const span = document.createElement("span");
    const meter = document.createElement("div");
    const meterValue = document.createElement("span");
    strong.textContent = title;
    span.textContent = body;
    li.className = severityForLoad(value);
    meter.className = "bottleneck-meter";
    meterValue.style.width = percentage(value);
    meter.append(meterValue);
    li.append(strong, span, meter);
    output.bottleneckList.append(li);
  });

  output.fixSuggestions.replaceChildren();
  fixSuggestions(state).forEach(([title, body]) => {
    const li = document.createElement("li");
    const strong = document.createElement("strong");
    const span = document.createElement("span");
    strong.textContent = title;
    span.textContent = body;
    li.className = title === "Block generation" ? "error" : title === "Optional model adviser" ? "" : state.severity;
    li.append(strong, span);
    output.fixSuggestions.append(li);
  });

  output.adapterOutput.textContent = JSON.stringify(
    {
      severity: state.severity,
      block_generation: state.severity === "error",
      approved_context: state.severity === "error" ? "hold_for_review" : "ready",
      adapter: "GuardedRetriever(existing_retriever)",
      model_handoff: state.severity === "error" ? "blocked" : "allowed",
    },
    null,
    2,
  );
}

function adviserDiagnostics(state) {
  return {
    severity: state.severity,
    question_type: state.scenario.label,
    retriever: state.retriever.label,
    corpus_size_k: state.corpusSize,
    top_k: state.topK,
    recall: formatScore(state.recall),
    precision: formatScore(state.precision),
    citation_accuracy: formatScore(state.citation),
    density_risk: densityLabel(state.densityRisk),
    conflict_risk: state.conflictRisk,
    top_k_stress: state.topKStress,
    bottlenecks: bottlenecks(state).map(([title, value, body]) => ({
      title,
      severity: severityForLoad(value),
      score: formatScore(value),
      detail: body,
    })),
    suggestions: fixSuggestions(state).map(([title, body]) => ({ title, detail: body })),
  };
}

function updateAdviserStatus(level, text) {
  output.adviserStatus.textContent = text;
  setSeverity(output.adviserStatus, level);
}

function setAdviserOutput(response) {
  output.adviserProblem.textContent = response.problem || "No problem summary returned.";
  output.adviserWhy.textContent = response.why_it_matters || "No impact summary returned.";
  output.adviserFix.textContent = response.fix || "No fix returned.";
  output.adviserRisk.textContent = response.risk || "Review before applying any change.";
}

function updateAdviserMode() {
  if (controls.adviserMode.value === "off") {
    updateAdviserStatus("ok", "Off");
    setAdviserOutput({
      problem: "Adviser is off.",
      why_it_matters: "No model call has been made.",
      fix: "Turn on explain mode when you want local advice.",
      risk: "No external adviser call.",
    });
  } else {
    updateAdviserStatus("warn", "Ready");
  }
}

function updateViewMode() {
  document.body.classList.toggle("details-open", controls.detailToggle.checked);
  document.body.classList.toggle("console-mode", !controls.detailToggle.checked);
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
  updateSummaryPanel(state);
  updateRows(state);
  updateReviewQueue(state);
  updateConfigSummary(state);
  updateEventLog();
  updateProgressWindow();
  updateSimulationCanvas(state);
  updatePipelineView(state);
  updateKnobs(state);
  controls.stopSimulation.disabled = !hasRun || isStopped || progressIndex >= progressSteps.length;
}

function resetControls() {
  window.clearInterval(progressTimer);
  hasRun = false;
  isStopped = false;
  progressIndex = 0;
  controls.queryType.value = "deadline";
  controls.retriever.value = "rerank";
  applyScenarioPreset("deadline");
  controls.adviserMode.value = "off";
  recordLog("info", "Controls reset to the default profile.");
  updateAdviserMode();
  render();
}

function runComparison() {
  const state = calculateState();
  window.clearInterval(progressTimer);
  hasRun = true;
  isStopped = false;
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
      isStopped = false;
      recordLog(state.severity, "Run completed and review actions updated.");
    }
    render();
  }, 520);
}

function stopSimulation() {
  if (!hasRun || progressIndex >= progressSteps.length) {
    recordLog("info", "Stop ignored because no simulation is running.");
    render();
    return;
  }
  window.clearInterval(progressTimer);
  isStopped = true;
  recordLog("warn", "Simulation stopped by user.");
  render();
}

async function runAdviser() {
  const mode = controls.adviserMode.value;
  if (mode === "off") {
    updateAdviserMode();
    recordLog("info", "Adviser was not called because it is off.");
    render();
    return;
  }
  const state = calculateState();
  updateAdviserStatus("warn", "Thinking");
  setAdviserOutput({
    problem: "Sending sanitised diagnostics to the local adviser route.",
    why_it_matters: "The application system prompt is not changed.",
    fix: "Waiting for structured advice.",
    risk: "Advice will not be applied automatically.",
  });
  try {
    const response = await window.fetch("/adviser", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mode,
        model: controls.adviserModel.value,
        diagnostics: adviserDiagnostics(state),
      }),
    });
    if (!response.ok) {
      throw new Error(`Adviser returned ${response.status}`);
    }
    const data = await response.json();
    setAdviserOutput(data);
    updateAdviserStatus(state.severity === "error" ? "error" : "ok", "Returned");
    recordLog("info", `Adviser ${mode} returned structured advice.`);
  } catch (error) {
    updateAdviserStatus("error", "Failed");
    setAdviserOutput({
      problem: "Adviser request failed.",
      why_it_matters: "The retrieval guard still works, but model-generated advice is unavailable.",
      fix: String(error.message || error),
      risk: "Check the local model endpoint and server opt-in before relying on adviser output.",
    });
    recordLog("error", "Adviser request failed.", { message: String(error.message || error) });
  }
  render();
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

function positionInfoTooltip(button) {
  const tooltip = output.infoTooltip;
  if (!tooltip || !button) return;

  const margin = 12;
  const gap = 10;
  const buttonRect = button.getBoundingClientRect();
  tooltip.hidden = false;
  const tooltipRect = tooltip.getBoundingClientRect();
  const maxLeft = window.innerWidth - tooltipRect.width - margin;
  const left = clamp(buttonRect.left + buttonRect.width / 2 - tooltipRect.width / 2, margin, maxLeft);
  const above = buttonRect.top - tooltipRect.height - gap;
  const top = above > margin ? above : buttonRect.bottom + gap;

  tooltip.style.left = `${left}px`;
  tooltip.style.top = `${top}px`;
}

function showInfoTooltip(button, pinned = false) {
  const message = button.dataset.info || "";
  if (!message) return;
  if (activeInfoButton && activeInfoButton !== button) {
    activeInfoButton.removeAttribute("aria-describedby");
  }

  activeInfoButton = button;
  infoTooltipPinned = pinned;
  output.infoTooltip.textContent = message;
  button.setAttribute("aria-describedby", "infoTooltip");
  positionInfoTooltip(button);
}

function hideInfoTooltip() {
  if (activeInfoButton) {
    activeInfoButton.removeAttribute("aria-describedby");
  }
  activeInfoButton = null;
  infoTooltipPinned = false;
  output.infoTooltip.hidden = true;
}

function toggleInfoTooltip(button) {
  if (activeInfoButton === button && infoTooltipPinned) {
    hideInfoTooltip();
    return;
  }
  showInfoTooltip(button, true);
}

function scheduleConnectorRefresh() {
  if (connectorFrame) return;
  connectorFrame = window.requestAnimationFrame(() => {
    connectorFrame = 0;
    render();
  });
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

controls.signalLevel.addEventListener("input", () => {
  setSignalLevel(Number.parseInt(controls.signalLevel.value, 10));
  recordLog("info", "Signal bar changed hardening signals.", { enabled_signals: controls.signalLevel.value });
  render();
});
controls.queryType.addEventListener("input", () => {
  applyScenarioPreset(controls.queryType.value);
  recordLog("info", "Scenario preset updated the stack controls.", { scenario: controls.queryType.value });
  render();
});
controls.resetControls.addEventListener("click", resetControls);
controls.runComparison.addEventListener("click", runComparison);
controls.stopSimulation.addEventListener("click", stopSimulation);
controls.adviserMode.addEventListener("input", updateAdviserMode);
controls.runAdviser.addEventListener("click", runAdviser);
controls.detailToggle.addEventListener("input", updateViewMode);
controls.knobs.forEach((knob) => knob.addEventListener("click", handleKnobPress));
controls.themeDots.forEach((dot) => {
  dot.addEventListener("click", () => {
    document.documentElement.style.setProperty("--accent-2", dot.dataset.themeDot);
    recordLog("info", "Console status colour selected.");
    render();
  });
});
controls.infoButtons.forEach((button) => {
  button.addEventListener("mouseenter", () => showInfoTooltip(button));
  button.addEventListener("mouseleave", () => {
    if (!infoTooltipPinned) hideInfoTooltip();
  });
  button.addEventListener("focus", () => showInfoTooltip(button));
  button.addEventListener("blur", () => {
    if (!infoTooltipPinned) hideInfoTooltip();
  });
  button.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    toggleInfoTooltip(button);
  });
});
document.addEventListener("click", (event) => {
  if (!event.target.closest(".info-button")) {
    hideInfoTooltip();
  }
});
window.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    hideInfoTooltip();
  }
});
window.addEventListener("resize", () => positionInfoTooltip(activeInfoButton));
window.addEventListener("resize", scheduleConnectorRefresh);
window.addEventListener("scroll", () => positionInfoTooltip(activeInfoButton), true);
if (window.ResizeObserver) {
  const connectorObserver = new ResizeObserver(scheduleConnectorRefresh);
  connectorObserver.observe(output.simulationCanvas);
}

applyScenarioPreset(controls.queryType.value);
recordLog("info", "Dashboard loaded with local sample state.");
updateAdviserMode();
updateViewMode();
render();
