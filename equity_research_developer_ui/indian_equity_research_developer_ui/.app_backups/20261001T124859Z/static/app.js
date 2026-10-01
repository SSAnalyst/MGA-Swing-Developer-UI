(() => {
  const $ = (selector) => document.querySelector(selector);
  let planId = null;
  const setStatus = (message, bad = false) => { const el = $('#status'); el.textContent = message; el.className = bad ? 'error' : 'success'; };
  const node = (tag, text, className = '') => { const el = document.createElement(tag); el.textContent = text; el.className = className; return el; };
  async function api(url, options = {}) {
    const response = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...options });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Request failed.');
    return data;
  }
  function showTab(id) {
    document.querySelectorAll('.tab').forEach((button) => { const selected = button.dataset.tab === id; button.classList.toggle('active', selected); button.setAttribute('aria-selected', String(selected)); });
    document.querySelectorAll('.panel').forEach((panel) => panel.classList.toggle('active', panel.id === id));
    if (id === 'project') refreshProject();
  }
  document.querySelectorAll('.tab').forEach((button) => button.addEventListener('click', () => showTab(button.dataset.tab)));

  $('#research-form').addEventListener('submit', async (event) => {
    event.preventDefault(); setStatus('Running research…');
    const values = Object.fromEntries(new FormData(event.currentTarget));
    try { const data = await api('/api/research', { method: 'POST', body: JSON.stringify(values) }); $('#research-output').textContent = data.report; $('#research-meta').textContent = `Saved to ${data.saved_to}`; setStatus('Research complete.'); }
    catch (err) { setStatus(err.message, true); }
  });
  $('#developer-form').addEventListener('submit', async (event) => {
    event.preventDefault(); setStatus('Requesting a safe change plan…');
    try { const data = await api('/api/developer/plan', { method: 'POST', body: JSON.stringify(Object.fromEntries(new FormData(event.currentTarget))) }); planId = data.plan_id; renderPlan(data.plan); setStatus('Plan ready for review. No files have been changed.'); }
    catch (err) { setStatus(err.message, true); }
  });
  function renderList(title, values) { const wrapper = document.createElement('section'); wrapper.append(node('h3', title)); const list = document.createElement('ul'); (values || []).forEach((value) => list.append(node('li', value))); wrapper.append(list); return wrapper; }
  function renderPlan(plan) {
    $('#plan-card').classList.remove('hidden'); $('#plan-summary').textContent = plan.summary;
    const details = $('#plan-details'); details.replaceChildren(renderList('Assumptions', plan.assumptions), renderList('Manual steps', plan.manual_steps), renderList('Suggested tests', plan.tests));
    const files = $('#plan-files'); files.replaceChildren(); plan.files.forEach((file) => { const detailsEl = document.createElement('details'); const summary = document.createElement('summary'); summary.textContent = `${file.path} — ${file.reason}`; const diff = node('pre', file.diff, 'diff'); detailsEl.append(summary, diff); files.append(detailsEl); });
  }
  $('#apply-plan').addEventListener('click', async () => {
    if (!planId || !confirm('Apply the reviewed changes? Existing changed files will be backed up.')) return;
    try { const data = await api('/api/developer/apply', { method: 'POST', body: JSON.stringify({ plan_id: planId }) }); planId = null; $('#apply-plan').disabled = true; setStatus(`Applied ${data.applied.files.length} file(s). Backup: ${data.applied.backup_dir || 'not needed'}.`); refreshProject(); }
    catch (err) { setStatus(err.message, true); }
  });
  async function refreshProject() {
    try { const [project, history] = await Promise.all([api('/api/project'), api('/api/history')]); const files = $('#project-files'); files.replaceChildren(); project.files.forEach((file) => files.append(node('li', `${file.path} (${file.size.toLocaleString()} bytes)`))); const entries = $('#history'); entries.replaceChildren(); if (!history.history.length) entries.append(node('li', 'No applied changes yet.')); history.history.forEach((entry) => entries.append(node('li', `${entry.timestamp}: ${entry.summary} — ${entry.files.join(', ')}`))); }
    catch (err) { setStatus(err.message, true); }
  }
  $('#refresh-project').addEventListener('click', refreshProject); refreshProject();
})();
