let current = null;

function short(v, n=22) {
  if (v === null || v === undefined) return "—";
  const s = typeof v === "string" ? v : JSON.stringify(v);
  return s.length > n ? `${s.slice(0,n)}…` : s;
}

async function run(caseId) {
  document.querySelectorAll("button[data-case]").forEach(b => b.classList.toggle("active", b.dataset.case === caseId));
  const status = document.getElementById("status");
  status.textContent = `Running ${caseId}…`;
  status.className = "status";
  try {
    const r = await fetch(`/api/proof/${caseId}`, {cache:"no-store"});
    if (!r.ok) throw new Error(await r.text());
    current = await r.json();
    const c = current.c2pa_receipt;
    const e = current.epm_transition_result;
    const a = current.external_action_authority;
    document.getElementById("c2pa-state").textContent = short(c.validation_state, 60);
    document.getElementById("asset-hash").textContent = c.asset_sha256;
    document.getElementById("manifest-hash").textContent = c.manifest_store_sha256;
    document.getElementById("active-manifest").textContent = short(c.active_manifest, 70);
    document.getElementById("c2pa-results").textContent = JSON.stringify(c.validation_results, null, 2);
    document.getElementById("context-delta").textContent = JSON.stringify(current.epm_input.context_delta);
    document.getElementById("epm-state").textContent = e.state;
    document.getElementById("epm-decision").textContent = e.decision;
    document.getElementById("epm-failure").textContent = e.failure;
    document.getElementById("epm-reason").textContent = e.reason;
    document.getElementById("epm-input").textContent = JSON.stringify(current.epm_input, null, 2);
    document.getElementById("authority-status").textContent = a.status;
    document.getElementById("authority-reason").textContent = a.reason;
    document.getElementById("proof-hash").textContent = current.proof_sha256;
    document.getElementById("epm-version").textContent = `${current.versions.epm_engine} @ ${current.versions.epm_release_commit}`;
    document.getElementById("mutated").textContent = String(current.invariants.c2pa_semantics_mutated);
    document.getElementById("authority-imported").textContent = String(current.invariants.external_authority_from_epm);
    status.textContent = "Proof complete. Change context and compare: the C2PA receipt hash must remain identical.";
    status.className = "status ok";
  } catch (err) {
    status.textContent = `Proof failed closed: ${err}`;
    status.className = "status fail";
  }
}

document.querySelectorAll("button[data-case]").forEach(b => b.addEventListener("click", () => run(b.dataset.case)));
document.getElementById("download").addEventListener("click", () => {
  if (!current) return;
  const blob = new Blob([JSON.stringify(current, null, 2)], {type:"application/json"});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `c2pa-epm-boundary-${current.case_id}-${current.proof_sha256.slice(0,12)}.json`;
  a.click();
  URL.revokeObjectURL(a.href);
});
run("baseline");
