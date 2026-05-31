<!DOCTYPE html>
<html lang="ro">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Shorts Pipeline</title>
  <link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@400;500;600;700;800&family=JetBrains+Mono:wght@300;400;500&display=swap" rel="stylesheet" />
  <style>
    :root {
      --bg: #080810;
      --surface: #0e0e1c;
      --surface2: #13131f;
      --border: #1e1e32;
      --border-bright: #2e2e50;
      --accent: #e8445a;
      --violet: #6d4afe;
      --violet-dim: rgba(109,74,254,0.1);
      --green: #0fba81;
      --green-dim: rgba(15,186,129,0.1);
      --yellow: #f5c542;
      --text: #ddddf0;
      --muted: #5a5a80;
      --muted2: #3a3a58;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: 'Bricolage Grotesque', sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
    }

    body::before {
      content: '';
      position: fixed;
      width: 600px; height: 600px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(109,74,254,0.06) 0%, transparent 70%);
      top: -100px; left: 50%;
      transform: translateX(-50%);
      pointer-events: none;
      z-index: 0;
    }

    .container {
      position: relative; z-index: 1;
      max-width: 660px;
      margin: 0 auto;
      padding: 64px 24px 100px;
    }

    header {
      text-align: center;
      margin-bottom: 52px;
    }

    .status-pill {
      display: inline-flex; align-items: center; gap: 7px;
      background: var(--surface); border: 1px solid var(--border-bright);
      border-radius: 100px; padding: 5px 14px 5px 10px;
      font-family: 'JetBrains Mono', monospace; font-size: 10px;
      color: var(--muted); letter-spacing: 0.06em; text-transform: uppercase;
      margin-bottom: 28px;
    }
    .live-dot {
      width: 5px; height: 5px; border-radius: 50%;
      background: var(--green); box-shadow: 0 0 6px var(--green);
      animation: breathe 2.5s ease-in-out infinite;
    }
    @keyframes breathe {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.4; transform: scale(0.8); }
    }

    h1 {
      font-size: clamp(36px, 7vw, 58px); font-weight: 800;
      line-height: 1.08; letter-spacing: -0.04em; color: #fff;
    }
    h1 span {
      background: linear-gradient(120deg, var(--violet), var(--accent));
      -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    }
    .subtitle {
      color: var(--muted); font-size: 13px; line-height: 1.7;
      max-width: 400px; margin: 14px auto 0;
    }

    /* ── PIPELINE STEPS ── */
    .pipeline {
      display: flex; align-items: flex-start; justify-content: center;
      margin-bottom: 44px; position: relative; gap: 0;
    }
    .pipeline-line {
      position: absolute; top: 16px;
      left: calc(8% + 16px); right: calc(8% + 16px);
      height: 1px;
      background: linear-gradient(90deg, transparent, var(--border-bright) 20%, var(--border-bright) 80%, transparent);
    }
    .step {
      display: flex; flex-direction: column; align-items: center;
      gap: 8px; flex: 1; position: relative;
    }
    .step-icon {
      width: 32px; height: 32px; border-radius: 8px;
      background: var(--surface2); border: 1px solid var(--border-bright);
      display: flex; align-items: center; justify-content: center;
      font-size: 13px; z-index: 1;
    }
    .step-label {
      font-size: 9px; font-family: 'JetBrains Mono', monospace;
      color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em;
      text-align: center;
    }

    /* ── SECTION BLOCKS ── */
    .section {
      background: var(--surface); border: 1px solid var(--border-bright);
      border-radius: 16px; padding: 22px 24px; margin-bottom: 14px;
    }
    .section-title {
      font-family: 'JetBrains Mono', monospace; font-size: 10px;
      color: var(--muted); text-transform: uppercase; letter-spacing: 0.1em;
      margin-bottom: 14px;
    }

    /* URL input */
    .input-row {
      display: flex; gap: 10px;
      background: var(--surface2); border: 1px solid var(--border-bright);
      border-radius: 12px; padding: 5px 5px 5px 16px;
      transition: border-color 0.2s, box-shadow 0.2s;
    }
    .input-row:focus-within {
      border-color: var(--violet);
      box-shadow: 0 0 0 3px rgba(109,74,254,0.08);
    }
    .url-input {
      flex: 1; background: transparent; border: none;
      color: var(--text); font-family: 'JetBrains Mono', monospace;
      font-size: 12px; outline: none; min-width: 0;
    }
    .url-input::placeholder { color: var(--muted2); }

    /* Buttons */
    .btn-primary {
      background: var(--violet); border: none; border-radius: 10px;
      padding: 11px 22px; color: white;
      font-family: 'Bricolage Grotesque', sans-serif;
      font-size: 13px; font-weight: 700; cursor: pointer;
      transition: all 0.2s; white-space: nowrap; letter-spacing: -0.01em;
    }
    .btn-primary:hover { background: #7d5eff; transform: translateY(-1px); box-shadow: 0 6px 20px rgba(109,74,254,0.35); }
    .btn-primary:active { transform: translateY(0); }
    .btn-primary:disabled { opacity: 0.4; cursor: not-allowed; transform: none; box-shadow: none; }

    .btn-ghost {
      background: none; border: 1px solid var(--border-bright);
      border-radius: 10px; padding: 10px 20px; color: var(--muted);
      font-family: 'Bricolage Grotesque', sans-serif;
      font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.15s;
    }
    .btn-ghost:hover { border-color: var(--muted); color: var(--text); }

    .btn-green {
      background: var(--green); border: none; border-radius: 10px;
      padding: 11px 22px; color: #fff;
      font-family: 'Bricolage Grotesque', sans-serif;
      font-size: 13px; font-weight: 700; cursor: pointer;
      transition: all 0.2s;
    }
    .btn-green:hover { background: #0da870; transform: translateY(-1px); }
    .btn-green:disabled { opacity: 0.4; cursor: not-allowed; transform: none; }

    /* Music section */
    .music-row {
      display: flex; gap: 10px; align-items: center; flex-wrap: wrap;
    }
    .music-select {
      flex: 1; min-width: 0; background: var(--surface2);
      border: 1px solid var(--border-bright); border-radius: 10px;
      padding: 10px 14px; color: var(--text);
      font-family: 'JetBrains Mono', monospace; font-size: 11px;
      outline: none; transition: border-color 0.2s;
    }
    .music-select:focus { border-color: var(--violet); }
    .music-select option { background: var(--surface2); }

    .upload-label {
      display: inline-flex; align-items: center; gap: 8px;
      background: var(--surface2); border: 1px dashed var(--border-bright);
      border-radius: 10px; padding: 10px 16px; cursor: pointer;
      font-size: 12px; color: var(--muted); transition: all 0.2s;
      white-space: nowrap;
    }
    .upload-label:hover { border-color: var(--violet); color: var(--text); }

    .volume-row {
      display: flex; align-items: center; gap: 12px; margin-top: 12px;
    }
    .volume-label {
      font-family: 'JetBrains Mono', monospace; font-size: 10px;
      color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em;
      white-space: nowrap;
    }
    input[type=range] {
      flex: 1; -webkit-appearance: none; height: 3px;
      background: var(--border-bright); border-radius: 2px; outline: none;
    }
    input[type=range]::-webkit-slider-thumb {
      -webkit-appearance: none; width: 14px; height: 14px;
      border-radius: 50%; background: var(--violet); cursor: pointer;
    }
    .volume-val {
      font-family: 'JetBrains Mono', monospace; font-size: 11px;
      color: var(--green); min-width: 36px; text-align: right;
    }

    /* Progress */
    .progress-card {
      background: var(--surface); border: 1px solid var(--border-bright);
      border-radius: 14px; padding: 22px 26px; margin-bottom: 14px; display: none;
    }
    .progress-card.visible { display: block; }
    .progress-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
    .progress-label { font-size: 13px; font-weight: 600; color: var(--text); }
    .progress-pct { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: var(--green); }
    .bar-bg { background: var(--surface2); border-radius: 100px; height: 3px; overflow: hidden; margin-bottom: 10px; }
    .bar-fill {
      height: 100%; border-radius: 100px;
      background: linear-gradient(90deg, var(--violet), var(--green));
      transition: width 0.6s cubic-bezier(0.4,0,0.2,1); width: 0%;
    }
    .progress-sub {
      font-family: 'JetBrains Mono', monospace; font-size: 10px;
      color: var(--muted); display: flex; align-items: center; gap: 8px;
    }
    .spinner {
      width: 10px; height: 10px; border-radius: 50%;
      border: 1.5px solid var(--border-bright); border-top-color: var(--violet);
      animation: spin 0.8s linear infinite; flex-shrink: 0;
    }
    @keyframes spin { to { transform: rotate(360deg); } }

    /* Error */
    .error-card {
      background: rgba(232,68,90,0.08); border: 1px solid rgba(232,68,90,0.3);
      border-radius: 12px; padding: 14px 18px; color: var(--accent);
      font-family: 'JetBrains Mono', monospace; font-size: 11px;
      margin-bottom: 14px; display: none;
    }
    .error-card.visible { display: block; }

    /* ── MINI-EDITOR (awaiting confirmation) ── */
    .editor-card {
      background: var(--surface); border: 1px solid var(--yellow);
      border-radius: 16px; padding: 24px; margin-bottom: 14px; display: none;
    }
    .editor-card.visible { display: block; }
    .editor-header {
      display: flex; align-items: center; gap: 10px; margin-bottom: 16px;
    }
    .editor-badge {
      background: rgba(245,197,66,0.12); border: 1px solid rgba(245,197,66,0.3);
      border-radius: 6px; padding: 3px 10px;
      font-family: 'JetBrains Mono', monospace; font-size: 10px;
      color: var(--yellow); text-transform: uppercase; letter-spacing: 0.06em;
    }
    .editor-title { font-size: 14px; font-weight: 700; color: var(--text); }
    .editor-sub { font-size: 12px; color: var(--muted); margin-bottom: 14px; line-height: 1.6; }

    .editor-textarea {
      width: 100%; min-height: 160px; background: var(--surface2);
      border: 1px solid var(--border-bright); border-radius: 10px;
      padding: 14px 16px; color: var(--text);
      font-family: 'JetBrains Mono', monospace; font-size: 12px;
      line-height: 1.8; outline: none; resize: vertical;
      transition: border-color 0.2s;
    }
    .editor-textarea:focus { border-color: var(--yellow); }

    .editor-footer {
      display: flex; justify-content: flex-end; gap: 10px; margin-top: 14px;
    }

    .char-count {
      font-family: 'JetBrains Mono', monospace; font-size: 10px;
      color: var(--muted); margin-top: 6px; text-align: right;
    }

    /* ── RESULTS ── */
    .results-card {
      background: var(--surface); border: 1px solid var(--border-bright);
      border-radius: 16px; padding: 24px; margin-bottom: 14px; display: none;
    }
    .results-card.visible { display: block; }
    .results-header {
      display: flex; align-items: center; gap: 12px; margin-bottom: 20px;
    }
    .check-badge {
      width: 32px; height: 32px; border-radius: 8px;
      background: var(--green-dim); border: 1px solid rgba(15,186,129,0.3);
      display: flex; align-items: center; justify-content: center;
      font-size: 14px; color: var(--green); font-weight: 700;
    }
    .results-title-text { font-size: 15px; font-weight: 700; color: #fff; }

    .download-list { display: flex; flex-direction: column; gap: 8px; margin-bottom: 20px; }
    .download-item {
      display: flex; align-items: center; gap: 14px;
      background: var(--surface2); border: 1px solid var(--border);
      border-radius: 10px; padding: 12px 14px;
    }
    .dl-icon {
      width: 34px; height: 34px; border-radius: 8px;
      display: flex; align-items: center; justify-content: center; font-size: 15px; flex-shrink: 0;
    }
    .dl-icon.video { background: var(--violet-dim); }
    .dl-icon.audio { background: var(--green-dim); }
    .dl-icon.text  { background: rgba(232,68,90,0.1); }
    .dl-icon.srt   { background: rgba(245,197,66,0.1); }
    .dl-info { flex: 1; min-width: 0; }
    .dl-name { font-size: 13px; font-weight: 600; color: var(--text); }
    .dl-desc { font-size: 10px; font-family: 'JetBrains Mono', monospace; color: var(--muted); margin-top: 2px; }
    .dl-btn {
      background: var(--violet-dim); border: 1px solid rgba(109,74,254,0.25);
      border-radius: 8px; padding: 7px 14px;
      color: var(--violet); font-size: 12px; font-weight: 700;
      text-decoration: none; transition: all 0.15s; white-space: nowrap;
    }
    .dl-btn:hover { background: var(--violet); color: #fff; }

    /* Transcript tabs */
    .transcript-section { margin-top: 4px; }
    .tabs { display: flex; background: var(--surface2); border-radius: 8px; padding: 3px; width: fit-content; margin-bottom: 10px; }
    .tab-btn {
      background: none; border: none; border-radius: 6px;
      padding: 5px 14px; color: var(--muted);
      font-family: 'Bricolage Grotesque', sans-serif;
      font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.15s;
    }
    .tab-btn.active { background: var(--surface); color: var(--text); box-shadow: 0 1px 3px rgba(0,0,0,0.3); }
    .transcript-box {
      background: var(--surface2); border: 1px solid var(--border);
      border-radius: 10px; padding: 14px 16px;
      font-family: 'JetBrains Mono', monospace; font-size: 11px;
      line-height: 1.9; color: var(--muted);
      max-height: 160px; overflow-y: auto; display: none;
    }
    .transcript-box.active { display: block; }
    .transcript-box::-webkit-scrollbar { width: 3px; }
    .transcript-box::-webkit-scrollbar-thumb { background: var(--border-bright); border-radius: 2px; }

    @media (max-width: 500px) {
      .pipeline { display: none; }
      .music-row { flex-direction: column; }
      .music-select { width: 100%; }
    }
  </style>
</head>
<body>
<div class="container">

  <header>
    <div class="status-pill"><span class="live-dot"></span>ONLINE</div>
    <h1>PIPE<br><span>LINE</span></h1>
    <p class="subtitle">Download · Mut · Fundal · TTS român · Captions</p>
  </header>

  <!-- Pipeline steps -->
  <div class="pipeline">
    <div class="pipeline-line"></div>
    <div class="step">
      <div class="step-icon">⬇</div>
      <div class="step-label">Download</div>
    </div>
    <div class="step">
      <div class="step-icon">🔇</div>
      <div class="step-label">Mut</div>
    </div>
    <div class="step">
      <div class="step-icon">🎙</div>
      <div class="step-label">Transcriere</div>
    </div>
    <div class="step">
      <div class="step-icon">✏️</div>
      <div class="step-label">Editor</div>
    </div>
    <div class="step">
      <div class="step-icon">🎬</div>
      <div class="step-label">Compilare</div>
    </div>
    <div class="step">
      <div class="step-icon">✓</div>
      <div class="step-label">Descarcă</div>
    </div>
  </div>

  <!-- URL Input -->
  <div class="section">
    <div class="section-title">YouTube Shorts Link</div>
    <div class="input-row">
      <input class="url-input" id="urlInput" type="url"
        placeholder="https://youtube.com/shorts/..." autocomplete="off" spellcheck="false" />
      <button class="btn-primary" id="processBtn" onclick="startProcess()">Procesează →</button>
    </div>
  </div>

  <!-- Music section -->
  <div class="section">
    <div class="section-title">🎵 Muzică de fundal</div>
    <div class="music-row">
      <select class="music-select" id="musicSelect">
        <option value="">— fără muzică —</option>
      </select>
      <label class="upload-label" for="musicUpload">
        ⬆ Upload MP3
        <input type="file" id="musicUpload" accept="audio/*" style="display:none" onchange="uploadMusic(this)" />
      </label>
    </div>
    <div class="volume-row">
      <span class="volume-label">Volum fundal</span>
      <input type="range" id="bgVolume" min="1" max="30" value="8" oninput="updateVolumeLabel()" />
      <span class="volume-val" id="volumeVal">8%</span>
    </div>
  </div>

  <!-- Progress -->
  <div class="progress-card" id="progressCard">
    <div class="progress-top">
      <span class="progress-label" id="stepLabel">Se procesează...</span>
      <span class="progress-pct" id="progressPct">0%</span>
    </div>
    <div class="bar-bg"><div class="bar-fill" id="progressBar"></div></div>
    <div class="progress-sub">
      <div class="spinner"></div>
      <span id="progressLog">Inițializare...</span>
    </div>
  </div>

  <!-- Error -->
  <div class="error-card" id="errorCard"></div>

  <!-- Mini-editor (awaiting confirmation) -->
  <div class="editor-card" id="editorCard">
    <div class="editor-header">
      <div class="editor-badge">✏ Editor</div>
      <div class="editor-title">Verifică și editează textul român</div>
    </div>
    <p class="editor-sub">
      Textul de mai jos va fi transformat în voce și captions. Poți edita, corecta sau reformula înainte de a continua.
    </p>
    <textarea class="editor-textarea" id="editorText" oninput="updateCharCount()"></textarea>
    <div class="char-count" id="charCount">0 caractere</div>
    <div class="editor-footer">
      <button class="btn-ghost" onclick="resetAll()">✕ Anulează</button>
      <button class="btn-green" id="confirmBtn" onclick="confirmText()">✓ Confirmă și generează →</button>
    </div>
  </div>

  <!-- Results -->
  <div class="results-card" id="resultsCard">
    <div class="results-header">
      <div class="check-badge">✓</div>
      <span class="results-title-text">Fișierele sunt gata</span>
    </div>
    <div class="download-list" id="downloadGrid"></div>
    <div class="transcript-section">
      <div class="tabs">
        <button class="tab-btn active" onclick="showTab('orig')">Original</button>
        <button class="tab-btn" onclick="showTab('ro')">Română</button>
      </div>
      <div class="transcript-box active" id="origBox"></div>
      <div class="transcript-box" id="roBox"></div>
    </div>
  </div>

  <button class="btn-ghost" id="resetBtn" style="display:none;margin:0 auto;" onclick="resetAll()">
    ↩ Procesează alt video
  </button>

</div>
<script>
  let pollInterval = null;
  let currentJobId = null;

  // ── Music ──────────────────────────────────────────────────────────────────
  async function loadMusicList() {
    try {
      const resp = await fetch('/list-music');
      const data = await resp.json();
      const sel = document.getElementById('musicSelect');
      // Keep first option
      while (sel.options.length > 1) sel.remove(1);
      (data.files || []).forEach(f => {
        const opt = document.createElement('option');
        opt.value = f; opt.textContent = f;
        sel.appendChild(opt);
      });
    } catch(e) {}
  }

  async function uploadMusic(input) {
    const file = input.files[0];
    if (!file) return;
    const fd = new FormData();
    fd.append('music', file);
    try {
      const resp = await fetch('/upload-music', { method: 'POST', body: fd });
      const data = await resp.json();
      if (data.filename) {
        await loadMusicList();
        document.getElementById('musicSelect').value = data.filename;
      }
    } catch(e) { showError('Upload muzică eșuat.'); }
    input.value = '';
  }

  function updateVolumeLabel() {
    const v = document.getElementById('bgVolume').value;
    document.getElementById('volumeVal').textContent = v + '%';
  }

  // ── Process ────────────────────────────────────────────────────────────────
  async function startProcess() {
    const url = document.getElementById('urlInput').value.trim();
    if (!url) { showError('Introdu un link YouTube Shorts valid.'); return; }

    hideError();
    hideEditor();
    document.getElementById('resultsCard').classList.remove('visible');
    document.getElementById('resetBtn').style.display = 'none';
    document.getElementById('processBtn').disabled = true;
    document.getElementById('progressCard').classList.add('visible');
    setProgress(0, 'Se trimite cererea...');

    const musicFilename = document.getElementById('musicSelect').value || null;
    const bgVolume = parseInt(document.getElementById('bgVolume').value) / 100;

    try {
      const resp = await fetch('/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, music_filename: musicFilename, bg_volume: bgVolume })
      });
      const data = await resp.json();
      if (data.error) { showError(data.error); stopUI(); return; }
      currentJobId = data.job_id;
      pollStatus(data.job_id);
    } catch(e) {
      showError('Nu s-a putut conecta la server.');
      stopUI();
    }
  }

  function pollStatus(jobId) {
    pollInterval = setInterval(async () => {
      try {
        const resp = await fetch(`/status/${jobId}`);
        const data = await resp.json();
        setProgress(data.progress || 0, data.step || '...');

        if (data.status === 'awaiting_confirmation') {
          clearInterval(pollInterval);
          document.getElementById('progressCard').classList.remove('visible');
          showEditor(data.romanian_text || '');
        } else if (data.status === 'done') {
          clearInterval(pollInterval);
          showResults(jobId, data);
        } else if (data.status === 'error') {
          clearInterval(pollInterval);
          showError(data.error || 'Eroare necunoscută.');
          stopUI();
        }
      } catch(e) {
        clearInterval(pollInterval);
        showError('Conexiunea cu serverul a fost pierdută.');
        stopUI();
      }
    }, 1200);
  }

  // ── Mini-editor ────────────────────────────────────────────────────────────
  function showEditor(text) {
    document.getElementById('editorText').value = text;
    updateCharCount();
    document.getElementById('editorCard').classList.add('visible');
  }

  function hideEditor() {
    document.getElementById('editorCard').classList.remove('visible');
  }

  function updateCharCount() {
    const len = document.getElementById('editorText').value.length;
    document.getElementById('charCount').textContent = len + ' caractere';
  }

  async function confirmText() {
    const text = document.getElementById('editorText').value.trim();
    if (!text) { showError('Textul nu poate fi gol.'); return; }

    document.getElementById('confirmBtn').disabled = true;
    hideError();
    hideEditor();
    document.getElementById('progressCard').classList.add('visible');
    setProgress(62, 'Se continuă procesarea...');

    try {
      const resp = await fetch('/confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_id: currentJobId, tts_text: text })
      });
      const data = await resp.json();
      if (data.error) { showError(data.error); stopUI(); return; }
      pollStatus(currentJobId);
    } catch(e) {
      showError('Eroare la trimiterea confirmării.');
      stopUI();
    }
  }

  // ── Results ────────────────────────────────────────────────────────────────
  function showResults(jobId, data) {
    document.getElementById('progressCard').classList.remove('visible');
    const files = data.files || {};
    const preview = data.preview || {};
    const grid = document.getElementById('downloadGrid');
    grid.innerHTML = '';

    [
      { key: 'final_video',          icon: '🎬', cls: 'video', name: 'Video Final',             desc: 'MP4 · mut + fundal + TTS + captions' },
      { key: 'tts_romanian',         icon: '🔊', cls: 'audio', name: 'Audio voce română',        desc: 'MP3 · Cartesia TTS' },
      { key: 'captions_srt',         icon: '💬', cls: 'srt',   name: 'Captions SRT',             desc: 'SRT · sincronizat cu vocea' },
      { key: 'transcript_original',  icon: '📄', cls: 'text',  name: 'Transcriere originală',    desc: 'TXT · Groq Whisper' },
      { key: 'transcript_romanian',  icon: '🌐', cls: 'text',  name: 'Traducere română',          desc: 'TXT · Google Translate' },
    ].forEach(item => {
      if (!files[item.key]) return;
      grid.innerHTML += `
        <div class="download-item">
          <div class="dl-icon ${item.cls}">${item.icon}</div>
          <div class="dl-info">
            <div class="dl-name">${item.name}</div>
            <div class="dl-desc">${item.desc}</div>
          </div>
          <a class="dl-btn" href="/download/${jobId}/${files[item.key]}">Descarcă</a>
        </div>`;
    });

    // Populate transcripts
    const origText = files['transcript_original']
      ? `[descarcă pentru textul complet]`
      : '';
    if (data.preview) {
      document.getElementById('origBox').textContent = data.preview.original || '';
      document.getElementById('roBox').textContent = data.preview.romanian || '';
    }

    document.getElementById('resultsCard').classList.add('visible');
    document.getElementById('resetBtn').style.display = 'block';
    document.getElementById('processBtn').disabled = false;
    document.getElementById('confirmBtn').disabled = false;
  }

  // ── Tabs ───────────────────────────────────────────────────────────────────
  function showTab(tab) {
    document.querySelectorAll('.tab-btn').forEach((b, i) => {
      b.classList.toggle('active', (i === 0 && tab === 'orig') || (i === 1 && tab === 'ro'));
    });
    document.getElementById('origBox').classList.toggle('active', tab === 'orig');
    document.getElementById('roBox').classList.toggle('active', tab === 'ro');
  }

  // ── Helpers ────────────────────────────────────────────────────────────────
  function setProgress(pct, label) {
    document.getElementById('progressBar').style.width = pct + '%';
    document.getElementById('progressPct').textContent = pct + '%';
    document.getElementById('stepLabel').textContent = label;
    document.getElementById('progressLog').textContent = label;
  }

  function stopUI() {
    document.getElementById('processBtn').disabled = false;
    document.getElementById('confirmBtn').disabled = false;
    document.getElementById('progressCard').classList.remove('visible');
  }

  function showError(msg) {
    const el = document.getElementById('errorCard');
    el.textContent = '⚠ ' + msg;
    el.classList.add('visible');
  }

  function hideError() {
    document.getElementById('errorCard').classList.remove('visible');
  }

  function resetAll() {
    clearInterval(pollInterval);
    currentJobId = null;
    document.getElementById('resultsCard').classList.remove('visible');
    document.getElementById('resetBtn').style.display = 'none';
    document.getElementById('progressCard').classList.remove('visible');
    document.getElementById('urlInput').value = '';
    document.getElementById('processBtn').disabled = false;
    document.getElementById('confirmBtn').disabled = false;
    hideEditor();
    hideError();
  }

  // ── Init ───────────────────────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', () => {
    loadMusicList();
    document.getElementById('urlInput').addEventListener('keydown', e => {
      if (e.key === 'Enter') startProcess();
    });
  });
</script>
</body>
</html>
