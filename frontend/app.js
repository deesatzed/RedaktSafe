const inputText = document.querySelector("#inputText");
const size = document.querySelector("#size");
const riskLane = document.querySelector("#riskLane");
const warnings = document.querySelector("#warnings");
const entityRows = document.querySelector("#entityRows");
const limitations = document.querySelector("#limitations");
const redactedText = document.querySelector("#redactedText");
const packetButton = document.querySelector("#packetButton");
const downloads = document.querySelector("#downloads");
const learningSubmitButton = document.querySelector("#learningSubmitButton");
const learningQueueButton = document.querySelector("#learningQueueButton");
const learningStatus = document.querySelector("#learningStatus");
const learningQueue = document.querySelector("#learningQueue");

const demoText = `Name: Maria Rivera
MRN: MRN-992188
DOB: 04/05/1965
Phone: (212) 555-0101
Address: 123 Oak Street, Boston MA
Assessment: chest pain resolved.`;

document.querySelector("#demoButton").addEventListener("click", () => {
  inputText.value = demoText;
  updateSize();
});

document.querySelector("#clearButton").addEventListener("click", () => {
  inputText.value = "";
  updateSize();
  renderEmpty();
});

document.querySelector("#fileInput").addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  inputText.value = await file.text();
  updateSize();
});

document.querySelector("#preflightButton").addEventListener("click", async () => {
  const text = inputText.value.trim();
  if (!text) return;
  const response = await fetch("/api/preflight", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({text, source_name: "browser-preflight"})
  });
  if (!response.ok) {
    renderError(`Preflight failed with status ${response.status}`);
    return;
  }
  renderResult(await response.json());
  packetButton.disabled = false;
});

packetButton.addEventListener("click", async () => {
  const text = inputText.value.trim();
  if (!text) return;
  const response = await fetch("/api/packet", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({text, source_name: "browser-packet"})
  });
  if (!response.ok) {
    renderError(`Packet creation failed with status ${response.status}`);
    return;
  }
  renderDownloads(await response.json());
});

learningSubmitButton.addEventListener("click", async () => {
  const text = inputText.value.trim();
  const passphrase = document.querySelector("#learningPassphrase").value;
  const spanText = document.querySelector("#learningSpanText").value.trim();
  if (!text || !passphrase || !spanText) {
    renderLearningStatus("Input text, passphrase, and span text are required.");
    return;
  }
  const payload = {
    passphrase,
    text,
    span_text: spanText,
    entity_type: document.querySelector("#learningEntityType").value.trim(),
    error_type: document.querySelector("#learningErrorType").value,
    context_category: document.querySelector("#learningContextCategory").value,
    downstream_exposure: document.querySelector("#learningExposure").value.trim() || "local",
    detector_disagreement: document.querySelector("#learningDisagreement").checked
  };
  const response = await fetch("/api/learning/corrections", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    renderLearningStatus(`Correction failed with status ${response.status}`);
    return;
  }
  const correction = await response.json();
  renderLearningStatus(`Saved ${correction.entity_type} correction as ${correction.route}.`);
  await refreshLearningQueue();
});

learningQueueButton.addEventListener("click", refreshLearningQueue);

inputText.addEventListener("input", updateSize);
updateSize();

function updateSize() {
  size.value = `${inputText.value.length} chars`;
}

function renderResult(payload) {
  riskLane.textContent = payload.risk_lane;
  riskLane.className = `risk lane-${payload.risk_lane.toLowerCase().replaceAll("_", "-")}`;
  warnings.innerHTML = "";
  for (const warning of payload.warnings || []) {
    const item = document.createElement("p");
    item.textContent = warning;
    warnings.appendChild(item);
  }
  renderEntities(payload.counts_by_entity_type || {});
  renderLimitations(payload.limitations || []);
  redactedText.textContent = payload.redacted_text || "No redacted text returned.";
}

function renderEntities(counts) {
  entityRows.innerHTML = "";
  const entries = Object.entries(counts);
  if (!entries.length) {
    entityRows.innerHTML = "<tr><td colspan=\"2\">No entities detected</td></tr>";
    return;
  }
  for (const [type, count] of entries) {
    const row = document.createElement("tr");
    row.innerHTML = `<td>${escapeHtml(type)}</td><td>${Number(count)}</td>`;
    entityRows.appendChild(row);
  }
}

function renderLimitations(items) {
  limitations.innerHTML = "";
  for (const item of items) {
    const li = document.createElement("li");
    li.textContent = item;
    limitations.appendChild(li);
  }
}

function renderDownloads(payload) {
  downloads.innerHTML = "";
  const urls = payload.artifact_urls || {};
  for (const name of Object.keys(urls).sort()) {
    const link = document.createElement("a");
    link.href = urls[name];
    link.download = name;
    link.textContent = `Download ${name}`;
    downloads.appendChild(link);
  }
}

function renderError(message) {
  warnings.innerHTML = "";
  const item = document.createElement("p");
  item.textContent = message;
  warnings.appendChild(item);
}

function renderLearningStatus(message) {
  learningStatus.innerHTML = "";
  const item = document.createElement("p");
  item.textContent = message;
  learningStatus.appendChild(item);
}

async function refreshLearningQueue() {
  const response = await fetch("/api/learning/queue");
  if (!response.ok) {
    renderLearningStatus(`Queue refresh failed with status ${response.status}`);
    return;
  }
  const payload = await response.json();
  learningQueue.textContent = JSON.stringify(payload, null, 2);
}

function renderEmpty() {
  riskLane.textContent = "Not run";
  riskLane.className = "risk";
  warnings.innerHTML = "";
  entityRows.innerHTML = "<tr><td colspan=\"2\">No result</td></tr>";
  redactedText.textContent = "Run local preflight to review redacted text.";
  downloads.innerHTML = "<p>No downloads yet.</p>";
  packetButton.disabled = true;
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\"": "&quot;",
    "'": "&#039;"
  })[char]);
}
