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
<title>Pitch Doctor</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #070b14;
    --bg-elev: #121a2b;
    --ink: #f4f7fb;
    --muted: #93a0b8;
    --line: rgba(148, 163, 184, .28);
    --accent: #22c55e;
    --accent-2: #5eead4;
    --on-accent: #062014;
    --danger: #f87171;
    --font: "IBM Plex Sans", "Segoe UI", sans-serif;
    --mono: "JetBrains Mono", ui-monospace, monospace;
    color-scheme: dark;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; min-height: 100%; }
  body {
    font-family: var(--font);
    background: var(--bg);
    color: var(--ink);
    min-height: 100vh;
  }
  input, button, select { font-family: inherit; font-size: 16px; }
  button, .chip, .mode, .lang-btn, a { cursor: pointer; }
  a { color: var(--accent-2); }
  :focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 3px;
  }

  .glow {
    position: fixed; inset: 0; pointer-events: none; z-index: 0;
    background:
      radial-gradient(900px 420px at 12% -10%, rgba(34,197,94,.16), transparent 55%),
      radial-gradient(700px 360px at 90% 0%, rgba(94,234,212,.08), transparent 50%),
      linear-gradient(180deg, #0c1424 0%, var(--bg) 38%);
  }
  .grid {
    position: fixed; inset: 0; pointer-events: none; z-index: 0; opacity: .22;
    background-image:
      linear-gradient(rgba(148,163,184,.12) 1px, transparent 1px),
      linear-gradient(90deg, rgba(148,163,184,.12) 1px, transparent 1px);
    background-size: 48px 48px;
    mask-image: radial-gradient(ellipse at 50% 0%, #000 20%, transparent 75%);
  }

  .wrap { position: relative; z-index: 1; max-width: 920px; margin: 0 auto; padding: 20px 20px 64px; }
  header {
    display: flex; align-items: center; justify-content: space-between; gap: 16px;
    margin-bottom: 36px;
  }
  .brand { display: flex; align-items: center; gap: 10px; text-decoration: none; color: inherit; }
  .mark {
    width: 34px; height: 34px; border-radius: 9px;
    background: linear-gradient(145deg, var(--accent), #047857);
    color: var(--on-accent); display: grid; place-items: center;
    font-family: var(--mono); font-weight: 600; font-size: 13px;
    box-shadow: 0 0 24px rgba(34,197,94,.35);
  }
  .brand strong { font-size: 15px; letter-spacing: .02em; }
  .langs { display: flex; gap: 4px; background: rgba(255,255,255,.04); padding: 4px; border-radius: 999px; border: 1px solid var(--line); }
  .lang-btn {
    border: 0; background: transparent; color: var(--muted);
    padding: 6px 11px; border-radius: 999px; font-size: 12px; font-weight: 600;
    transition: background .2s, color .2s;
  }
  .lang-btn[aria-pressed="true"] { background: var(--ink); color: #0b1220; }

  .hero { margin-bottom: 28px; }
  .kicker {
    font-family: var(--mono); font-size: 12px; color: var(--accent);
    letter-spacing: .14em; text-transform: uppercase; margin: 0 0 12px;
  }
  h1 { font-size: clamp(28px, 4.6vw, 46px); line-height: 1.12; margin: 0 0 10px; max-width: 16ch; letter-spacing: -.03em; }
  .tagline { margin: 0; color: var(--muted); font-size: 17px; max-width: 42ch; }

  .panel {
    background: color-mix(in srgb, var(--bg-elev) 88%, transparent);
    border: 1px solid var(--line);
    border-radius: 22px;
    padding: 22px;
    backdrop-filter: blur(16px);
    box-shadow: 0 24px 80px rgba(0,0,0,.35);
    transition: transform .25s ease, box-shadow .25s ease;
  }
  .modes {
    display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 18px;
  }
  .mode {
    border: 1px solid var(--line); background: rgba(255,255,255,.03);
    color: var(--muted); border-radius: 14px; padding: 12px 14px; text-align: left;
    font-weight: 600; transition: border-color .2s, background .2s, color .2s, transform .15s;
  }
  .mode:hover { color: var(--ink); border-color: rgba(34,197,94,.45); }
  .mode[aria-pressed="true"] {
    color: var(--ink); border-color: var(--accent);
    background: rgba(34,197,94,.12);
    box-shadow: inset 0 0 0 1px rgba(34,197,94,.25);
  }
  .field { display: flex; flex-direction: column; gap: 6px; margin-bottom: 14px; }
  .field label, .group-title { font-size: 12px; font-weight: 600; color: var(--muted); letter-spacing: .04em; text-transform: uppercase; }
  .field input, .field select {
    width: 100%; padding: 13px 14px; border-radius: 12px;
    border: 1px solid var(--line); background: rgba(7,11,20,.55); color: var(--ink);
    -webkit-appearance: none; appearance: none;
    transition: border-color .2s, box-shadow .2s;
  }
  .field input:focus, .field select:focus {
    outline: none; border-color: var(--accent);
    box-shadow: 0 0 0 4px rgba(34,197,94,.16);
  }
  .field input.invalid, .field select.invalid {
    border-color: var(--danger);
    box-shadow: 0 0 0 4px rgba(248,113,113,.12);
  }
  .hint { font-size: 12px; color: var(--danger); min-height: 1em; }
  .search-row { display: flex; gap: 10px; align-items: stretch; }
  .search-row .field { flex: 1; margin: 0; }
  .chips { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 10px 0 18px; }
  .chips span { font-size: 12px; color: var(--muted); }
  .chip {
    border: 1px solid var(--line); background: transparent; color: var(--ink);
    border-radius: 999px; padding: 6px 12px; font-family: var(--mono); font-size: 12px;
    transition: background .15s, border-color .15s, transform .15s;
  }
  .chip:hover { border-color: var(--accent); background: rgba(34,197,94,.08); transform: translateY(-1px); }

  .group {
    border-top: 1px solid var(--line); padding-top: 16px; margin-top: 6px;
  }
  .group-head { display: flex; justify-content: space-between; gap: 12px; margin-bottom: 12px; }
  .group-head p { margin: 0; font-size: 12px; color: var(--muted); }
  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  .submit {
    width: 100%; margin-top: 8px; border: 0; border-radius: 14px;
    padding: 14px 18px; background: var(--accent); color: var(--on-accent);
    font-weight: 700; font-size: 16px;
    transition: filter .15s, transform .12s, box-shadow .2s;
    box-shadow: 0 10px 30px rgba(34,197,94,.25);
  }
  .submit:hover { filter: brightness(1.06); }
  .submit:active { transform: translateY(1px) scale(.99); }
  .submit:disabled { opacity: .6; cursor: wait; transform: none; }

  #error-slot:empty { display: none; }
  .error-box {
    background: rgba(248,113,113,.1); border: 1px solid rgba(248,113,113,.45);
    color: #fecaca; border-radius: 14px; padding: 14px 16px; margin: 0 0 16px;
  }
  .error-box a { color: inherit; }

  #progress-panel { display: none; }
  #progress-panel.active { display: block; }
  .progress-top { display: flex; justify-content: space-between; gap: 12px; align-items: baseline; margin-bottom: 10px; }
  .target-url { font-family: var(--mono); font-size: 13px; color: var(--accent-2); word-break: break-all; }
  .meta { font-size: 12px; color: var(--muted); font-family: var(--mono); }
  .bar { height: 6px; border-radius: 99px; background: rgba(255,255,255,.08); overflow: hidden; margin-bottom: 18px; }
  .bar > i {
    display: block; height: 100%; width: 8%;
    background: linear-gradient(90deg, var(--accent), var(--accent-2));
    border-radius: inherit; transition: width .45s ease;
  }
  .stage-list { display: flex; flex-direction: column; gap: 6px; }
  .stage {
    display: flex; align-items: center; gap: 12px; padding: 10px 12px; border-radius: 12px;
    color: var(--muted); font-size: 14.5px; transition: color .3s, background .3s, transform .25s;
  }
  .stage.active { color: var(--ink); background: rgba(255,255,255,.04); }
  .stage.done { color: var(--accent); }
  .stage-dot {
    width: 22px; height: 22px; border-radius: 50%; flex: none;
    border: 2px solid #334155; display: grid; place-items: center;
    transition: border-color .3s, background .3s;
  }
  .stage.active .stage-dot { border-color: var(--accent); }
  .stage.active .stage-dot::after {
    content: ""; width: 8px; height: 8px; border-radius: 50%; background: var(--accent);
    animation: pulse 1s ease-in-out infinite;
  }
  .stage.done .stage-dot { border-color: var(--accent); background: var(--accent); }
  .stage.done .stage-dot::after { content: "\\2713"; color: var(--on-accent); font-size: 12px; font-weight: 900; animation: none; }
  #progress-note { text-align: center; color: var(--muted); font-size: 13px; margin-top: 18px; }
  .ghost {
    display: none; margin: 14px auto 0; border: 1px solid var(--line); background: transparent;
    color: var(--ink); border-radius: 999px; padding: 8px 14px; font-size: 13px;
  }
  #progress-panel.done .ghost { display: inline-flex; }

  .foot {
    display: flex; flex-wrap: wrap; gap: 12px 20px; justify-content: space-between;
    align-items: center; margin-top: 22px; color: var(--muted); font-size: 12px;
  }
  .contact-cta {
    display: inline-flex; align-items: center; gap: 6px;
    color: var(--ink); text-decoration: none; font-weight: 600; font-size: 13px;
    border-bottom: 1px solid rgba(34,197,94,.5); padding-bottom: 2px;
    transition: color .15s, border-color .15s;
  }
  .contact-cta:hover { color: var(--accent); }

  input:-webkit-autofill,
  input:-webkit-autofill:hover,
  input:-webkit-autofill:focus {
    -webkit-text-fill-color: #fff;
    caret-color: #fff;
    -webkit-box-shadow: 0 0 0px 1000px #121a2b inset;
    transition: background-color 9999s ease-in-out 0s;
  }
  .field select option { color: #000; }

  @keyframes pulse { 0%, 100% { opacity: .4; transform: scale(.8); } 50% { opacity: 1; transform: scale(1); } }
  @keyframes rise { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
  @keyframes shake {
    0%, 100% { transform: none; }
    25% { transform: translateX(-4px); }
    75% { transform: translateX(4px); }
  }
  .panel { animation: rise .45s ease; }
  .shake { animation: shake .32s ease; }

  .hidden { display: none !important; }
  body.is-busy .hero, body.is-busy header .langs { opacity: .45; pointer-events: none; }

  @media (max-width: 640px) {
    .grid-2, .modes { grid-template-columns: 1fr; }
    .search-row { flex-direction: column; }
    h1 { max-width: none; }
    .wrap { padding: 16px 16px 48px; }
  }
  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
      animation: none !important; transition: none !important;
    }
  }
</style>
</head>
<body>
  <div class="glow" aria-hidden="true"></div>
  <div class="grid" aria-hidden="true"></div>
  <div class="wrap">
    <header>
      <a class="brand" href="/">
        <span class="mark">PD</span>
        <strong>Pitch Doctor</strong>
      </a>
      <div class="langs" role="group" aria-label="Language">
        <button type="button" class="lang-btn" data-lang="en" aria-pressed="true">EN</button>
        <button type="button" class="lang-btn" data-lang="es" aria-pressed="false">ES</button>
        <button type="button" class="lang-btn" data-lang="fr" aria-pressed="false">FR</button>
      </div>
    </header>

    <section class="hero">
      <p class="kicker" id="kicker"></p>
      <h1 id="tagline"></h1>
      <p class="tagline" id="subheading"></p>
    </section>

    <div id="error-slot"></div>

    <div class="panel" id="work-panel">
      <form id="scan-form" novalidate>
        <div class="modes" role="group" aria-label="Audit type">
          <button type="button" class="mode" id="mode-site" aria-pressed="true"></button>
          <button type="button" class="mode" id="mode-none" aria-pressed="false"></button>
        </div>

        <div id="site-fields">
          <div class="search-row">
            <div class="field">
              <label for="url-input" id="url-label"></label>
              <input type="text" name="url" id="url-input" inputmode="url" autocomplete="url" autocorrect="off" autocapitalize="off" spellcheck="false" autofocus>
              <div class="hint" id="url-hint"></div>
            </div>
          </div>
          <div class="chips" id="example-chips">
            <span id="examples-label"></span>
            <button type="button" class="chip" data-url="example.com">example.com</button>
            <button type="button" class="chip" data-url="wikipedia.org">wikipedia.org</button>
          </div>
        </div>

        <div id="nosite-fields" class="grid-2 hidden">
          <div class="field">
            <label for="business-name-input" id="business-name-label"></label>
            <input type="text" name="business_name" id="business-name-input" autocomplete="organization">
            <div class="hint" id="business-hint"></div>
          </div>
          <div class="field">
            <label for="city-input" id="city-label"></label>
            <input type="text" name="city" id="city-input" autocomplete="address-level2">
            <div class="hint" id="city-hint"></div>
          </div>
        </div>

        <div class="group">
          <div class="group-head">
            <div>
              <div class="group-title" id="required-heading"></div>
              <p id="required-hint"></p>
            </div>
            <div class="field" style="margin:0;min-width:160px">
              <label for="lang-select" id="lang-label"></label>
              <select name="lang" id="lang-select">
                <option value="en">English</option>
                <option value="es">Español</option>
                <option value="fr">Français</option>
              </select>
            </div>
          </div>
          <div class="grid-2">
            <div class="field">
              <label for="email-input" id="email-label"></label>
              <input type="email" name="email" id="email-input" autocomplete="email" required>
              <div class="hint" id="email-hint"></div>
            </div>
            <div class="field">
              <label for="brand-name-input" id="brand-name-label"></label>
              <input type="text" name="brand_name" id="brand-name-input" autocomplete="name" required>
              <div class="hint" id="name-hint"></div>
            </div>
            <div class="field">
              <label for="brand-phone-input" id="brand-phone-label"></label>
              <input type="tel" name="brand_phone" id="brand-phone-input" autocomplete="tel" required>
              <div class="hint" id="phone-hint"></div>
            </div>
          </div>
        </div>

        <button type="submit" class="submit" id="submit-btn"></button>
      </form>

      <div id="progress-panel" aria-live="polite" aria-busy="false">
        <div class="progress-top">
          <div class="target-url" id="progress-url"></div>
          <div class="meta" id="progress-meta"></div>
        </div>
        <div class="bar" aria-hidden="true"><i id="progress-bar"></i></div>
        <div class="stage-list" id="stage-list"></div>
        <div id="progress-note"></div>
        <button type="button" class="ghost" id="try-again"></button>
      </div>
    </div>

    <div class="foot">
      <p class="footer-note" id="footer-note"></p>
      <div>
        <a href="/privacy" id="privacy-link"></a>
        &nbsp;·&nbsp;
        <a href="https://zerodigitx.com" class="contact-cta" id="contact-cta"></a>
      </div>
    </div>
  </div>

<script>
const COPY = __COPY_JSON__;
const STAGES = ["dns", "http", "browser", "links", "presence", "report"];

const form = document.getElementById('scan-form');
const urlInput = document.getElementById('url-input');
const submitBtn = document.getElementById('submit-btn');
const langSelect = document.getElementById('lang-select');
const progressPanel = document.getElementById('progress-panel');
const progressUrl = document.getElementById('progress-url');
const stageList = document.getElementById('stage-list');
const errorSlot = document.getElementById('error-slot');
const panel = document.getElementById('work-panel');
const modeSite = document.getElementById('mode-site');
const modeNone = document.getElementById('mode-none');
const siteFields = document.getElementById('site-fields');
const noSiteFields = document.getElementById('nosite-fields');
const progressBar = document.getElementById('progress-bar');
const progressMeta = document.getElementById('progress-meta');
const tryAgain = document.getElementById('try-again');

let mode = 'site';
let activeStages = STAGES;
let elapsedTimer = null;
let startedAt = 0;

function t(lang) { return COPY[lang] || COPY.en; }
function withScheme(raw) { return raw.trim(); }

function fmt(template, vars) {
  return String(template || '').replace(/\\{(\\w+)\\}/g, function (_, k) {
    return vars[k] == null ? '' : vars[k];
  });
}

function setMode(next) {
  mode = next;
  modeSite.setAttribute('aria-pressed', next === 'site' ? 'true' : 'false');
  modeNone.setAttribute('aria-pressed', next === 'none' ? 'true' : 'false');
  siteFields.classList.toggle('hidden', next !== 'site');
  noSiteFields.classList.toggle('hidden', next !== 'none');
  if (next === 'none') {
    urlInput.value = '';
    document.getElementById('business-name-input').focus();
  } else {
    urlInput.focus();
  }
}

function applyCopy() {
  const c = t(langSelect.value);
  document.documentElement.lang = langSelect.value;
  document.getElementById('kicker').textContent = c.kicker;
  document.getElementById('tagline').textContent = c.heading;
  document.getElementById('subheading').textContent = c.subheading;
  document.getElementById('url-label').textContent = c.url_label;
  urlInput.placeholder = c.placeholder;
  submitBtn.textContent = c.cta;
  document.getElementById('examples-label').textContent = c.examples_label;
  document.getElementById('email-label').textContent = c.email_label;
  document.getElementById('business-name-label').textContent = c.business_name_label;
  document.getElementById('city-label').textContent = c.city_label;
  document.getElementById('lang-label').textContent = c.lang_label;
  document.getElementById('brand-name-label').textContent = c.brand_name_label;
  document.getElementById('brand-phone-label').textContent = c.brand_phone_label;
  document.getElementById('required-heading').textContent = c.required_heading;
  document.getElementById('required-hint').textContent = c.required_hint;
  document.getElementById('footer-note').textContent = c.footer;
  document.getElementById('contact-cta').textContent = c.contact_cta;
  document.getElementById('privacy-link').textContent = c.privacy;
  document.getElementById('privacy-link').href = '/privacy?lang=' + langSelect.value;
  modeSite.textContent = c.mode_site;
  modeNone.textContent = c.mode_none;
  tryAgain.textContent = c.try_again;
  document.querySelectorAll('.lang-btn').forEach(function (btn) {
    btn.setAttribute('aria-pressed', btn.dataset.lang === langSelect.value ? 'true' : 'false');
  });
  if (!progressPanel.classList.contains('active')) renderStageList(c);
}

function renderStageList(c, stages) {
  activeStages = stages || STAGES;
  stageList.innerHTML = activeStages.map(function (key) {
    return '<div class="stage" data-stage="' + key + '"><div class="stage-dot"></div>' +
      '<div>' + c.stages[key] + '</div></div>';
  }).join('');
}

langSelect.addEventListener('change', applyCopy);
document.querySelectorAll('.lang-btn').forEach(function (btn) {
  btn.addEventListener('click', function () {
    langSelect.value = btn.dataset.lang;
    applyCopy();
  });
});
modeSite.addEventListener('click', function () { setMode('site'); });
modeNone.addEventListener('click', function () { setMode('none'); });
document.querySelectorAll('.chip').forEach(function (chip) {
  chip.addEventListener('click', function () {
    setMode('site');
    urlInput.value = chip.dataset.url;
    urlInput.dispatchEvent(new Event('input'));
    urlInput.focus();
  });
});

const phoneInput = document.getElementById('brand-phone-input');
phoneInput.addEventListener('input', function (e) {
  const digits = e.target.value.replace(/\\D/g, '').slice(0, 15);
  e.target.value = digits;
  e.target.classList.remove('invalid');
  document.getElementById('phone-hint').textContent = '';
});

function setStage(stageKey) {
  const idx = activeStages.indexOf(stageKey);
  const total = activeStages.length;
  document.querySelectorAll('.stage').forEach(function (el, i) {
    el.classList.remove('active', 'done');
    if (idx === -1) return;
    if (i < idx) el.classList.add('done');
    else if (i === idx) el.classList.add('active');
  });
  const current = Math.max(idx, 0) + 1;
  const pct = Math.round(((Math.max(idx, 0)) / total) * 100);
  progressBar.style.width = Math.max(12, pct) + '%';
  const c = t(langSelect.value);
  const secs = Math.floor((Date.now() - startedAt) / 1000);
  progressMeta.textContent = fmt(c.step_of, { current: current, total: total }) + ' · ' + fmt(c.elapsed, { n: secs });
}

function markAllDone() {
  document.querySelectorAll('.stage').forEach(function (el) {
    el.classList.remove('active');
    el.classList.add('done');
  });
  progressBar.style.width = '100%';
  progressPanel.classList.add('done');
}

function clearFieldErrors() {
  ['url-input','email-input','brand-name-input','brand-phone-input','business-name-input','city-input'].forEach(function (id) {
    document.getElementById(id).classList.remove('invalid');
  });
  ['url-hint','email-hint','name-hint','phone-hint','business-hint','city-hint'].forEach(function (id) {
    document.getElementById(id).textContent = '';
  });
}

function markInvalid(id, hintId, message) {
  document.getElementById(id).classList.add('invalid');
  document.getElementById(hintId).textContent = message;
}

function errorMessage(data) {
  if (!data) return 'could not start scan';
  if (typeof data.detail === 'string') return data.detail;
  if (Array.isArray(data.detail)) {
    return data.detail.map(function (d) { return d.msg || String(d); }).join('; ');
  }
  return 'could not start scan';
}

function showError(message, firstFieldId) {
  const c = t(langSelect.value);
  errorSlot.innerHTML = '<div class="error-box" role="alert" tabindex="-1" id="error-box"><strong id="error-title">' +
    c.error_heading + '</strong><div>' + message + '</div></div>';
  form.classList.remove('hidden');
  progressPanel.classList.remove('active', 'done');
  document.body.classList.remove('is-busy');
  submitBtn.disabled = false;
  submitBtn.textContent = c.cta;
  panel.classList.remove('shake');
  void panel.offsetWidth;
  panel.classList.add('shake');
  const box = document.getElementById('error-box');
  if (box) box.focus();
  if (firstFieldId) document.getElementById(firstFieldId).focus();
  if (elapsedTimer) { clearInterval(elapsedTimer); elapsedTimer = null; }
}

function resetScan() {
  form.classList.remove('hidden');
  progressPanel.classList.remove('active', 'done');
  document.body.classList.remove('is-busy');
  errorSlot.innerHTML = '';
  submitBtn.disabled = false;
  submitBtn.textContent = t(langSelect.value).cta;
  if (elapsedTimer) { clearInterval(elapsedTimer); elapsedTimer = null; }
}

tryAgain.addEventListener('click', resetScan);

function validate() {
  const c = t(langSelect.value);
  clearFieldErrors();
  const email = document.getElementById('email-input').value.trim();
  const name = document.getElementById('brand-name-input').value.trim();
  const phone = document.getElementById('brand-phone-input').value.trim();
  const businessName = document.getElementById('business-name-input').value.trim();
  const city = document.getElementById('city-input').value.trim();
  const url = urlInput.value.trim();
  let first = null;
  const problems = [];

  if (mode === 'site') {
    if (!url) {
      markInvalid('url-input', 'url-hint', c.need_target);
      first = first || 'url-input';
      problems.push('<a href="#url-input">' + c.need_target + '</a>');
    }
  } else {
    if (!businessName) {
      markInvalid('business-name-input', 'business-hint', c.field_business_error);
      first = first || 'business-name-input';
      problems.push('<a href="#business-name-input">' + c.field_business_error + '</a>');
    }
    if (!city) {
      markInvalid('city-input', 'city-hint', c.field_city_error);
      first = first || 'city-input';
      problems.push('<a href="#city-input">' + c.field_city_error + '</a>');
    }
  }
  if (!email || !/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email)) {
    markInvalid('email-input', 'email-hint', c.field_email_error);
    first = first || 'email-input';
    problems.push('<a href="#email-input">' + c.field_email_error + '</a>');
  }
  if (!name) {
    markInvalid('brand-name-input', 'name-hint', c.field_name_error);
    first = first || 'brand-name-input';
    problems.push('<a href="#brand-name-input">' + c.field_name_error + '</a>');
  }
  if (phone.replace(/\\D/g, '').length < 8) {
    markInvalid('brand-phone-input', 'phone-hint', c.field_phone_error);
    first = first || 'brand-phone-input';
    problems.push('<a href="#brand-phone-input">' + c.field_phone_error + '</a>');
  }
  return { ok: problems.length === 0, first: first, html: problems.join('<br>') };
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
      progressPanel.setAttribute('aria-busy', 'false');
      setTimeout(function () { window.location.href = data.report_url; }, 700);
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
  const check = validate();
  if (!check.ok) {
    showError(check.html, check.first);
    return;
  }

  errorSlot.innerHTML = '';
  submitBtn.disabled = true;
  submitBtn.textContent = c.scanning_label;

  const businessName = document.getElementById('business-name-input').value.trim();
  const city = document.getElementById('city-input').value.trim();
  const url = mode === 'site' ? urlInput.value.trim() : '';

  const payload = {
    url: url ? withScheme(url) : null,
    business_name: businessName || null,
    city: city || null,
    email: document.getElementById('email-input').value,
    lang: langSelect.value,
    brand_name: document.getElementById('brand-name-input').value,
    brand_phone: document.getElementById('brand-phone-input').value,
  };

  try {
    const res = await fetch('/api/scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const raw = await res.text();
    let data;
    try { data = JSON.parse(raw); }
    catch { throw new Error(res.statusText || 'could not start scan'); }
    if (!res.ok) throw new Error(errorMessage(data));

    form.classList.add('hidden');
    progressPanel.classList.add('active');
    progressPanel.classList.remove('done');
    progressPanel.setAttribute('aria-busy', 'true');
    document.body.classList.add('is-busy');
    progressUrl.textContent = payload.url || (businessName + ', ' + city);
    document.getElementById('progress-note').textContent = c.progress_note;
    renderStageList(c, payload.url ? STAGES : ['presence', 'report']);
    startedAt = Date.now();
    if (elapsedTimer) clearInterval(elapsedTimer);
    var firstStage = payload.url ? 'dns' : 'presence';
    elapsedTimer = setInterval(function () {
      var active = document.querySelector('.stage.active');
      setStage(active ? active.dataset.stage : firstStage);
    }, 1000);
    setStage(firstStage);
    poll(data.job_id);
  } catch (err) {
    showError(String(err));
  }
});

const params = new URLSearchParams(location.search);
if (params.get('lang') && COPY[params.get('lang')]) langSelect.value = params.get('lang');
if (params.get('url')) {
  setMode('site');
  urlInput.value = params.get('url');
}
applyCopy();
</script>
</body>
</html>"""
