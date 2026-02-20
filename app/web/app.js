function getApiBase() {
  const raw = (document.getElementById("apiBase")?.value || "").trim();
  if (raw) return `${raw.replace(/\/$/, "")}/api/v1`;
  // default: same-origin FastAPI deployment
  return "/api/v1";
}

async function call(path, options = {}) {
  const base = getApiBase();
  const res = await fetch(`${base}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const text = await res.text();
  let body;
  try { body = text ? JSON.parse(text) : {}; } catch { body = { raw: text }; }
  if (!res.ok) throw new Error(`${res.status} ${JSON.stringify(body)}`);
  return body;
}

function put(id, obj) { document.getElementById(id).textContent = JSON.stringify(obj, null, 2); }

window.addEventListener("DOMContentLoaded", () => {
  const apiInput = document.getElementById("apiBase");
  if (apiInput && window.location.port === "8006") {
    apiInput.value = "http://localhost:8000";
  }
});

document.getElementById("btnIngest").onclick = async () => {
  try {
    const raw = document.getElementById("ingestJson").value.trim();
    const payload = JSON.parse(raw || '{"applications": []}');
    put("opsOut", await call("/ingest", { method: "POST", body: JSON.stringify(payload) }));
  } catch (e) { put("opsOut", { error: String(e) }); }
};

document.getElementById("btnLoadApps").onclick = async () => {
  try {
    const data = await call("/applications?page=1&page_size=30");
    const list = document.getElementById("appsList");
    list.innerHTML = "";
    data.items.forEach((a) => {
      const li = document.createElement("li");
      li.textContent = `${a.application_id} | ${a.status} | ${a.loan_amount}`;
      li.onclick = () => { document.getElementById("appId").value = a.application_id; document.getElementById("graphAppId").value = a.application_id; };
      list.appendChild(li);
    });
  } catch (e) { put("detailsOut", { error: String(e) }); }
};

document.getElementById("btnGetRisk").onclick = async () => {
  const id = document.getElementById("appId").value.trim();
  if (!id) return;
  try { put("detailsOut", await call(`/risk/${id}`, { method: "POST" })); }
  catch (e) { put("detailsOut", { error: String(e) }); }
};

document.getElementById("btnGetDetails").onclick = async () => {
  const id = document.getElementById("appId").value.trim();
  if (!id) return;
  try { put("detailsOut", await call(`/applications/${id}`)); }
  catch (e) { put("detailsOut", { error: String(e) }); }
};

document.getElementById("btnRings").onclick = async () => {
  try { put("ringsOut", await call("/fraud-rings")); }
  catch (e) { put("ringsOut", { error: String(e) }); }
};

document.getElementById("btnSearch").onclick = async () => {
  const q = encodeURIComponent(document.getElementById("searchQ").value.trim());
  if (!q) return;
  try { put("searchOut", await call(`/semantic-search?q=${q}&top_k=5`)); }
  catch (e) { put("searchOut", { error: String(e) }); }
};

document.getElementById("btnRag").onclick = async () => {
  const question = document.getElementById("ragQ").value.trim();
  if (!question) return;
  try { put("ragOut", await call("/rag-query", { method: "POST", body: JSON.stringify({ question, top_k: 5 }) })); }
  catch (e) { put("ragOut", { error: String(e) }); }
};

document.getElementById("btnRecompute").onclick = async () => {
  try { put("opsOut", await call("/communities/recompute", { method: "POST" })); }
  catch (e) { put("opsOut", { error: String(e) }); }
};

document.getElementById("btnReset").onclick = async () => {
  try { put("opsOut", await call("/reset", { method: "POST" })); }
  catch (e) { put("opsOut", { error: String(e) }); }
};

let network;
document.getElementById("btnGraph").onclick = async () => {
  const id = document.getElementById("graphAppId").value.trim();
  if (!id) return;
  try {
    const graph = await call(`/applications/${id}/graph`);
    const nodes = new vis.DataSet(graph.nodes.map((n) => ({ id: n.id, label: `${n.kind}
${n.label}` })));
    const edges = new vis.DataSet(graph.edges.map((e) => ({ from: e.source, to: e.target, label: e.label, arrows: "to" })));
    const container = document.getElementById("graph");
    network = new vis.Network(container, { nodes, edges }, { physics: { stabilization: true } });
  } catch (e) {
    put("opsOut", { error: String(e) });
  }
};
