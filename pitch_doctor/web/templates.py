"""Inline HTML/CSS/JS for the local web UI. Kept as a plain string (no
separate template engine, no build step) since this is one small reactive
page -- not the client-facing report, which already has its own real Jinja2
template and design system.
"""

from __future__ import annotations

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>pitch-doctor</title>
<style>
  :root {
    --slate-950: #0b1220; --slate-900: #0f172a; --slate-800: #1e293b;
    --slate-700: #334155; --slate-500: #64748b; --slate-300: #cbd5e1;
    --slate-100: #f1f5f9; --emerald: #10b981; --emerald-dim: rgba(16,185,129,.16);
    --red: #ef4444; --amber: #f59e0b;
    --font: -apple-system, "Segoe UI", "Inter", Roboto, Helvetica, Arial, sans-serif;
    color-scheme: dark;
  }
  * { box-sizing: border-box; }
  input, button, select, textarea { font-family: inherit; }
  body {
    margin: 0; min-height: 100vh; font-family: var(--font);
    background: radial-gradient(circle at 30% 0%, #142238 0%, var(--slate-950) 45%, #060a14 100%);
    color: var(--slate-100); display: flex; align-items: center; justify-content: center; padding: 24px;
  }
  .card { width: 100%; max-width: 640px; animation: rise .5s ease; }
  @keyframes rise { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
  .eyebrow { font-size: 12px; text-transform: uppercase; letter-spacing: .08em; color: var(--emerald); font-weight: 700; margin-bottom: 10px; text-align: center; }
  h1 { font-size: 34px; margin: 0 0 6px; text-align: center; }
  .tagline { color: var(--slate-300); text-align: center; margin-bottom: 6px; transition: opacity .2s; }
  .subheading {
    color: var(--emerald); text-align: center; margin-bottom: 32px; font-size: 13px;
    font-weight: 700; text-transform: uppercase; letter-spacing: .05em; transition: opacity .2s;
  }
  form { display: flex; flex-direction: column; gap: 14px; }
  .search-row {
    display: flex; align-items: center; gap: 0; background: rgba(255,255,255,.06);
    border: 1px solid rgba(255,255,255,.12); border-radius: 999px; padding: 6px 6px 6px 22px;
    transition: border-color .2s, box-shadow .2s;
  }
  .search-row:focus-within { border-color: var(--emerald); box-shadow: 0 0 0 3px var(--emerald-dim); }
  .url-prefix { color: var(--slate-500); font-size: 16px; white-space: nowrap; user-select: none; transition: color .15s; }
  .search-row:focus-within .url-prefix { color: #fff; }
  .search-row input[type=text] {
    flex: 1; min-width: 0; background: transparent; border: none; outline: none;
    color: #fff; font-size: 16px; padding: 0 0 0 2px; -webkit-appearance: none; appearance: none;
  }
  .search-row input[type=text]::placeholder { color: var(--slate-500); }
  /* Chrome/Edge force a light "autofill" background + dark text on inputs;
     override both so it can't flash white against this dark theme. */
  input:-webkit-autofill,
  input:-webkit-autofill:hover,
  input:-webkit-autofill:focus,
  input:-webkit-autofill:active {
    -webkit-text-fill-color: #fff;
    caret-color: #fff;
    -webkit-box-shadow: 0 0 0px 1000px rgba(255,255,255,.06) inset;
    box-shadow: 0 0 0px 1000px rgba(255,255,255,.06) inset;
    transition: background-color 9999s ease-in-out 0s;
  }
  .fields input:-webkit-autofill,
  .fields input:-webkit-autofill:hover,
  .fields input:-webkit-autofill:focus,
  .fields input:-webkit-autofill:active {
    -webkit-box-shadow: 0 0 0px 1000px rgba(255,255,255,.05) inset;
    box-shadow: 0 0 0px 1000px rgba(255,255,255,.05) inset;
  }
  button {
    background: var(--emerald); color: #04231a; border: none; border-radius: 999px;
    padding: 12px 26px; font-size: 15px; font-weight: 700; cursor: pointer;
    transition: filter .15s, transform .1s; -webkit-appearance: none; appearance: none;
    flex: none;
  }
  button:hover { filter: brightness(1.08); }
  button:active { transform: scale(.97); }
  button:disabled { opacity: .55; cursor: wait; }
  details { background: rgba(255,255,255,.04); border: 1px solid rgba(255,255,255,.08); border-radius: 14px; padding: 14px 18px; }
  summary { cursor: pointer; color: var(--slate-300); font-size: 13px; user-select: none; }
  .fields { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 14px; }
  .fields label { font-size: 12px; color: var(--slate-500); display: block; margin-bottom: 4px; }
  .fields input, .fields select {
    width: 100%; padding: 9px 10px; border-radius: 8px; border: 1px solid rgba(255,255,255,.15);
    background: rgba(255,255,255,.05); color: #fff; font-size: 14px;
    -webkit-appearance: none; appearance: none;
  }
  .fields select option { color: #000; }
  .error-box {
    background: rgba(239,68,68,.12); border: 1px solid rgba(239,68,68,.4); color: #fecaca;
    border-radius: 10px; padding: 14px 18px; margin-bottom: 20px; animation: rise .3s ease;
  }
  .footer-note { text-align: center; color: var(--slate-500); font-size: 12px; margin-top: 22px; }

  /* ---------- Progress panel ---------- */
  #progress-panel { display: none; }
  #progress-panel.active { display: block; animation: rise .35s ease; }
  #progress-panel .target-url { text-align: center; color: var(--slate-300); font-size: 14px; margin-bottom: 26px; word-break: break-all; }
  .stage-list { display: flex; flex-direction: column; gap: 4px; }
  .stage {
    display: flex; align-items: center; gap: 14px; padding: 12px 16px; border-radius: 12px;
    color: var(--slate-500); font-size: 14.5px; transition: color .3s, background .3s;
  }
  .stage.active { color: #fff; background: rgba(255,255,255,.05); }
  .stage.done { color: var(--emerald); }
  .stage-dot {
    width: 22px; height: 22px; border-radius: 50%; flex: none;
    border: 2px solid var(--slate-700); display: flex; align-items: center; justify-content: center;
    transition: border-color .3s, background .3s;
  }
  .stage.active .stage-dot { border-color: var(--emerald); }
  .stage.active .stage-dot::after {
    content: ""; width: 8px; height: 8px; border-radius: 50%; background: var(--emerald);
    animation: pulse 1s ease-in-out infinite;
  }
  @keyframes pulse { 0%, 100% { opacity: .4; transform: scale(.8); } 50% { opacity: 1; transform: scale(1); } }
  .stage.done .stage-dot { border-color: var(--emerald); background: var(--emerald); }
  .stage.done .stage-dot::after { content: "\\2713"; color: #04231a; font-size: 12px; font-weight: 900; }
  #progress-note { text-align: center; color: var(--slate-500); font-size: 12px; margin-top: 24px; }
</style>
</head>
<body>
  <div class="card">
    <div class="eyebrow">pitch-doctor</div>
    <h1>pitch-doctor</h1>
    <div class="tagline" id="tagline"></div>
    <div class="subheading" id="subheading"></div>

    <div id="error-slot"></div>

    <form id="scan-form">
      <div class="search-row">
        <span class="url-prefix">https://</span>
        <input
          type="text"
          name="url"
          id="url-input"
          inputmode="url"
          autocomplete="off"
          autocorrect="off"
          autocapitalize="off"
          spellcheck="false"
          required
          autofocus
        >
        <button type="submit" id="submit-btn"></button>
      </div>
      <details>
        <summary id="advanced-label"></summary>
        <div class="fields">
          <div>
            <label id="lang-label"></label>
            <select name="lang" id="lang-select">
              <option value="en">English</option>
              <option value="es">Español</option>
              <option value="fr">Français</option>
              <option value="zh">中文</option>
            </select>
          </div>
          <div>
            <label id="brand-name-label"></label>
            <input type="text" name="brand_name" id="brand-name-input" value="Your Agency">
          </div>
          <div>
            <label id="brand-email-label"></label>
            <input type="email" name="brand_email" id="brand-email-input">
          </div>
          <div>
            <label id="brand-phone-label"></label>
            <input type="text" name="brand_phone" id="brand-phone-input">
          </div>
        </div>
      </details>
    </form>

    <div id="progress-panel">
      <div class="target-url" id="progress-url"></div>
      <div class="stage-list" id="stage-list"></div>
      <div id="progress-note"></div>
    </div>

    <div class="footer-note" id="footer-note"></div>
  </div>

<script>
const COPY = __COPY_JSON__;
const STAGES = ["dns", "http", "browser", "links", "report"];

const form = document.getElementById('scan-form');
const urlInput = document.getElementById('url-input');
const submitBtn = document.getElementById('submit-btn');
const langSelect = document.getElementById('lang-select');
const progressPanel = document.getElementById('progress-panel');
const progressUrl = document.getElementById('progress-url');
const stageList = document.getElementById('stage-list');
const errorSlot = document.getElementById('error-slot');

function t(lang) { return COPY[lang] || COPY.en; }

// The visible "https://" is a static prefix, not part of the input's value,
// so the client only ever has to type "website.com". If they paste a full
// URL anyway (with its own scheme), respect it as-is.
function withScheme(raw) {
  const value = raw.trim();
  return /^https?:\/\//i.test(value) ? value : 'https://' + value;
}

function applyCopy() {
  const c = t(langSelect.value);
  document.documentElement.lang = langSelect.value;
  document.getElementById('tagline').textContent = c.heading;
  document.getElementById('subheading').textContent = c.subheading;
  document.getElementById('url-input').placeholder = c.placeholder;
  document.getElementById('submit-btn').textContent = c.cta;
  document.getElementById('advanced-label').textContent = c.advanced_label;
  document.getElementById('lang-label').textContent = c.lang_label;
  document.getElementById('brand-name-label').textContent = c.brand_name_label;
  document.getElementById('brand-email-label').textContent = c.brand_email_label;
  document.getElementById('brand-phone-label').textContent = c.brand_phone_label;
  document.getElementById('footer-note').textContent = c.footer;
  renderStageList(c);
}

function renderStageList(c) {
  stageList.innerHTML = STAGES.map(function (key) {
    return '<div class="stage" data-stage="' + key + '"><div class="stage-dot"></div>' +
      '<div>' + c.stages[key] + '</div></div>';
  }).join('');
}

langSelect.addEventListener('change', applyCopy);
applyCopy();

function setStage(stageKey) {
  const idx = STAGES.indexOf(stageKey);
  document.querySelectorAll('.stage').forEach(function (el, i) {
    el.classList.remove('active', 'done');
    if (idx === -1) return;
    if (i < idx) el.classList.add('done');
    else if (i === idx) el.classList.add('active');
  });
}

function markAllDone() {
  document.querySelectorAll('.stage').forEach(function (el) {
    el.classList.remove('active');
    el.classList.add('done');
  });
}

function showError(message) {
  const c = t(langSelect.value);
  errorSlot.innerHTML = '<div class="error-box">' + c.error_heading + ': ' + message + '</div>';
  form.style.display = '';
  progressPanel.classList.remove('active');
  submitBtn.disabled = false;
  submitBtn.textContent = c.cta;
}

async function poll(jobId) {
  const c = t(langSelect.value);
  try {
    const res = await fetch('/api/status/' + jobId);
    if (!res.ok) throw new Error('status check failed');
    const data = await res.json();
    if (data.status === 'running') {
      setStage(data.stage);
      setTimeout(function () { poll(jobId); }, 700);
    } else if (data.status === 'done') {
      markAllDone();
      document.getElementById('progress-note').textContent = c.redirecting;
      setTimeout(function () { window.location.href = data.report_url; }, 500);
    } else {
      showError(data.error || 'unknown error');
    }
  } catch (err) {
    showError(String(err));
  }
}

form.addEventListener('submit', async function (evt) {
  evt.preventDefault();
  const c = t(langSelect.value);
  errorSlot.innerHTML = '';
  submitBtn.disabled = true;
  submitBtn.textContent = c.scanning_label;

  const payload = {
    url: withScheme(urlInput.value),
    lang: langSelect.value,
    brand_name: document.getElementById('brand-name-input').value,
    brand_email: document.getElementById('brand-email-input').value,
    brand_phone: document.getElementById('brand-phone-input').value,
  };

  try {
    const res = await fetch('/api/scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'could not start scan');

    form.style.display = 'none';
    progressPanel.classList.add('active');
    progressUrl.textContent = payload.url;
    document.getElementById('progress-note').textContent = c.progress_note;
    setStage('dns');
    poll(data.job_id);
  } catch (err) {
    showError(String(err));
  }
});
</script>
</body>
</html>"""
