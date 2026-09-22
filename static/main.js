/* main.js  —  Resume Utility Web UI (Phase 2) */

const TRACK_ORDER = ["AI", "TPM", "ITDM", "PM"];
const TRACK_EMOJIS = { AI: "🤖", TPM: "📊", ITDM: "💻", PM: "📦" };

let currentData = null;
let activeTab = null;
let jdMode = "paste";           // "paste" | "url"
let activeResumeTrack = "AI";
let resumeTexts = { AI: "", TPM: "", ITDM: "", PM: "" };
let scoreChartInstance = null;
let activeChartType = "radar";  // "radar" | "bar"

/* ═══════════════════════════ JD SECTION ═══════════════════════════ */

function setJdMode(mode) {
  jdMode = mode;
  document.querySelectorAll("#jd-mode-toggle .toggle-btn").forEach(b => {
    b.classList.toggle("active", b.dataset.mode === mode);
  });
  document.getElementById("jd-paste-panel").classList.toggle("hidden", mode !== "paste");
  document.getElementById("jd-url-panel").classList.toggle("hidden", mode !== "url");
}

async function fetchJdFromUrl() {
  const url = document.getElementById("jd-url-input").value.trim();
  const warnEl = document.getElementById("url-warning");
  const okEl = document.getElementById("url-success");
  warnEl.classList.add("hidden"); okEl.classList.add("hidden");

  if (!url) { showUrlWarn("Please enter a URL."); return; }

  const btn = document.getElementById("fetch-btn");
  btn.textContent = "Fetching…"; btn.disabled = true;

  try {
    const resp = await fetch("/fetch_jd", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    const data = await resp.json();

    if (data.error) { showUrlWarn(data.error); return; }
    if (data.warning) { showUrlWarn(data.warning); }

    if (data.text) {
      document.getElementById("jd-url-text").value = data.text;
      if (!data.warning) {
        okEl.textContent = data.title ? `✓ Fetched: "${data.title}"` : "✓ JD text fetched successfully.";
        okEl.classList.remove("hidden");
      }
    }
  } catch (e) {
    showUrlWarn("Network error: " + e.message);
  } finally {
    btn.textContent = "↗ Fetch"; btn.disabled = false;
  }
}

function showUrlWarn(msg) {
  const el = document.getElementById("url-warning");
  el.innerHTML = escHtml(msg).replace(/\n/g, "<br>");
  el.classList.remove("hidden");
}

function getJdText() {
  if (jdMode === "paste") return document.getElementById("jd-input").value.trim();
  return document.getElementById("jd-url-text").value.trim();
}

/* ═══════════════════════════ RESUME SECTION ═══════════════════════ */

function toggleSection(id) {
  const el = document.getElementById(id);
  el.classList.toggle("hidden");
}

function switchResumeTab(track) {
  activeResumeTrack = track;
  document.querySelectorAll(".resume-tab").forEach(b => b.classList.toggle("active", b.dataset.track === track));
  document.querySelectorAll(".resume-panel").forEach(p => p.classList.toggle("hidden", p.dataset.track !== track));
}

function setResumeMode(track, mode) {
  const panel = document.querySelector(`.resume-panel[data-track="${track}"]`);
  panel.querySelectorAll(".resume-input-toggle .toggle-btn").forEach(b => {
    b.classList.toggle("active", b.dataset.rtab === mode);
  });
  panel.querySelector(".resume-textarea").classList.toggle("hidden", mode !== "paste");
  panel.querySelector(".upload-area").classList.toggle("hidden", mode !== "upload");
}

async function uploadResume(input, track) {
  const file = input.files[0];
  if (!file) return;
  const statusEl = document.querySelector(`.upload-status[data-track="${track}"]`);
  statusEl.textContent = "Uploading…";

  const formData = new FormData();
  formData.append("file", file);
  formData.append("track", track);

  try {
    const resp = await fetch("/upload_resume", { method: "POST", body: formData });
    const data = await resp.json();
    if (data.error) { statusEl.textContent = "✗ " + data.error; return; }
    resumeTexts[track] = data.text;
    // Also put in textarea for review
    const ta = document.querySelector(`.resume-textarea[data-track="${track}"]`);
    if (ta) ta.value = data.text;
    statusEl.textContent = `✓ ${file.name} loaded (${data.text.length} chars)`;
  } catch (e) {
    statusEl.textContent = "✗ Upload error: " + e.message;
  }
}

function syncResumeTexts() {
  TRACK_ORDER.forEach(tc => {
    const ta = document.querySelector(`.resume-textarea[data-track="${tc}"]`);
    if (ta) resumeTexts[tc] = ta.value.trim();
  });
}

/* ═══════════════════════════ SCORING ═══════════════════════════════ */

async function submitJD() {
  const jdText = getJdText();
  const errEl = document.getElementById("error-msg");
  errEl.classList.add("hidden");

  if (!jdText) { showError("Please paste or fetch a Job Description before scoring."); return; }

  syncResumeTexts();
  showLoading(true);
  hideResults();

  try {
    const resp = await fetch("/score", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ jd_text: jdText }),
    });
    const data = await resp.json();
    if (data.error) { showError(data.error); showLoading(false); return; }

    currentData = data;
    renderResults(data);
    checkApiKey();
  } catch (e) {
    showError("Network error: " + e.message);
  } finally {
    showLoading(false);
  }
}

async function checkApiKey() {
  try {
    const resp = await fetch("/api_key_status");
    const { configured } = await resp.json();
    document.getElementById("api-key-banner").classList.toggle("hidden", configured);
  } catch (_) {}
}

function clearAll() {
  document.getElementById("jd-input").value = "";
  document.getElementById("jd-url-input").value = "";
  document.getElementById("jd-url-text").value = "";
  document.getElementById("error-msg").classList.add("hidden");
  document.getElementById("url-warning").classList.add("hidden");
  document.getElementById("url-success").classList.add("hidden");
  TRACK_ORDER.forEach(tc => {
    const ta = document.querySelector(`.resume-textarea[data-track="${tc}"]`);
    if (ta) ta.value = "";
    resumeTexts[tc] = "";
  });
  hideResults();
  clearFullAnalysis();
  currentData = null;
}

function showLoading(on) { document.getElementById("loading").classList.toggle("hidden", !on); }
function hideResults() { document.getElementById("results").classList.add("hidden"); }
function showError(msg) {
  const el = document.getElementById("error-msg");
  el.textContent = msg; el.classList.remove("hidden");
}

/* ═══════════════════════════ RENDER RESULTS ════════════════════════ */

function renderResults(data) {
  const { tracks, bullets, matched_keywords, signals } = data;
  if (signals) {
    document.getElementById("sig-salary").textContent = signals.salary || "Not specified";
    document.getElementById("sig-exp").textContent = signals.experience || "Not specified";
    document.getElementById("sig-work").textContent = signals.work_mode || "Not specified";
    document.getElementById("sig-seniority").textContent = signals.seniority || "Not specified";
    document.getElementById("sig-industry").textContent = signals.industry || "Not specified";
  }
  renderSummaryCards(tracks);
  renderTabs(tracks, bullets, matched_keywords);
  renderChart(tracks, activeChartType);
  renderBestTrackBanner(data);
  document.getElementById("results").classList.remove("hidden");
  activateTab(TRACK_ORDER[0]);
  const firstCard = document.querySelector(`.summary-card[data-track="${TRACK_ORDER[0]}"]`);
  if (firstCard) firstCard.classList.add("active");
}

function renderSummaryCards(tracks) {
  const grid = document.getElementById("summary-grid");
  grid.innerHTML = "";
  TRACK_ORDER.forEach(tc => {
    const t = tracks[tc]; if (!t) return;
    const card = document.createElement("div");
    card.className = `summary-card ${t.level_class}`;
    card.dataset.track = tc;
    card.onclick = () => {
      document.querySelectorAll(".summary-card").forEach(c => c.classList.remove("active"));
      card.classList.add("active"); activateTab(tc);
    };
    card.innerHTML = `
      <div class="track-name">${TRACK_EMOJIS[tc]} ${tc}</div>
      <div class="score-num">${t.final_pts} <span style="font-size:0.9rem;font-weight:400;color:var(--muted)">pts</span> <span style="font-size:0.85rem;color:var(--text);font-weight:400">(${t.pct}%)</span></div>
      <span class="level-badge ${t.level_class}">${t.level}</span>
      <div class="progress-bar-wrap"><div class="progress-bar" style="width:${t.pct}%"></div></div>
      <div style="font-size:0.78rem;color:var(--muted);margin-top:0.4rem">${t.label}</div>`;
    grid.appendChild(card);
  });
}

function renderTabs(tracks, bullets, matched_keywords) {
  const bar = document.getElementById("tab-bar");
  bar.innerHTML = "";
  TRACK_ORDER.forEach(tc => {
    if (!tracks[tc]) return;
    const btn = document.createElement("button");
    btn.className = "tab-btn"; btn.dataset.track = tc;
    btn.textContent = `${TRACK_EMOJIS[tc]} ${tracks[tc].label}`;
    btn.onclick = () => activateTab(tc);
    bar.appendChild(btn);
  });
  window._resultsData = { tracks, bullets, matched_keywords };
}

function activateTab(tc) {
  activeTab = tc;
  document.querySelectorAll(".tab-btn").forEach(b => b.classList.toggle("active", b.dataset.track === tc));
  renderTabContent(tc);
}

function renderTabContent(tc) {
  const { tracks, bullets } = window._resultsData;
  const t = tracks[tc];
  const content = document.getElementById("tab-content");
  if (!t) { content.innerHTML = ""; return; }

  const matched = t.keywords.filter(k => k.score > 0);
  const missing = t.keywords.filter(k => k.score === 0);
  const trackBullets = bullets[tc] || [];
  const hitBullets = trackBullets.filter(b => b.jd_hit_computed);
  const otherBullets = trackBullets.filter(b => !b.jd_hit_computed);
  const hasResume = !!resumeTexts[tc];

  // Default to 'matched' if any hit, otherwise 'all'
  const defaultFilter = matched.length > 0 ? "matched" : "all";

  content.innerHTML = `
    ${matched.length ? `
    <div class="matched-kw-section">
      <h4>✅ Matched Keywords (${matched.length}/${t.keywords.length})</h4>
      <div class="kw-pills">${matched.map(k => `<span class="kw-pill">${escHtml(k.keyword)}</span>`).join("")}</div>
    </div>` : ""}

    <div class="kw-table-header">
      <div class="kw-table-title">
        <span>📋 Keyword Breakdown</span>
        <span class="kw-count-badge" id="kw-count-badge-${tc}"></span>
      </div>
      <div class="kw-filter-group">
        <label for="kw-filter-${tc}">View:</label>
        <select id="kw-filter-${tc}" class="kw-select-filter" onchange="filterKeywordTable('${tc}')">
          <option value="matched" ${defaultFilter === "matched" ? "selected" : ""}>✅ Matched Only (${matched.length})</option>
          <option value="missing" ${defaultFilter === "missing" ? "selected" : ""}>❌ Unmatched / Missing (${missing.length})</option>
          <option value="all" ${defaultFilter === "all" ? "selected" : ""}>🌐 Show All (${t.keywords.length})</option>
        </select>
      </div>
    </div>

    <table class="keyword-table" id="kw-table-${tc}">
      <thead><tr><th>Keyword / Theme</th><th>Weight</th><th>Score</th><th>Weighted</th><th>Matched As</th></tr></thead>
      <tbody id="kw-tbody-${tc}">
        ${t.keywords.map(k => `
          <tr class="kw-row ${k.score > 0 ? "hit" : "miss"}" data-score="${k.score}">
            <td>${escHtml(k.keyword)}</td>
            <td>${k.weight}</td>
            <td><span class="badge-score s${k.score}">${k.score}</span></td>
            <td>${k.weighted}</td>
            <td style="color:var(--muted);font-size:0.82rem">${k.matched_term ? escHtml(k.matched_term) : "—"}</td>
          </tr>`).join("")}
      </tbody>
    </table>
    <div id="kw-empty-${tc}" class="kw-empty-state hidden"></div>

    <hr class="section-divider" />`;

  // Apply initial filter view
  filterKeywordTable(tc);

  content.innerHTML += `
    ${hitBullets.length ? `<div class="bullets-header">✅ JD-Matching Bullets (${hitBullets.length})</div>${renderBullets(hitBullets)}` : ""}
    ${otherBullets.length ? `<div class="bullets-header" style="color:var(--muted)">📋 Other Bullets</div>${renderBullets(otherBullets)}` : ""}

    <!-- AI Enhancement Panel -->
    <div class="ai-panel">
      <div class="ai-panel-header">
        <div class="ai-panel-title">✨ AI Resume Enhancement — ${t.label}</div>
        <div style="display:flex;gap:0.5rem;flex-wrap:wrap">
          <button class="ai-enhance-btn" id="ai-btn-${tc}" onclick="runEnhancement('${tc}')">
            ${hasResume ? "✨ Enhance My Resume" : "✨ Generate Suggestions"}
          </button>
          <button class="tailor-btn" id="tailor-btn-${tc}" onclick="runTailorResume('${tc}')">
            🪄 Tailor Full Resume
          </button>
        </div>
      </div>
      ${!hasResume ? `<p style="color:var(--muted);font-size:0.85rem">No resume provided for this track — AI will generate general suggestions based on the JD. Add your resume above for personalised advice.</p>` : `<p style="color:var(--accent2);font-size:0.85rem">✓ Resume loaded for this track. Click to get personalised suggestions or generate a full tailored ATS resume.</p>`}
      <div id="ai-result-${tc}"></div>
      <div id="tailor-result-${tc}"></div>
    </div>
  `;
}

function filterKeywordTable(tc) {
  const select = document.getElementById(`kw-filter-${tc}`);
  const tbody = document.getElementById(`kw-tbody-${tc}`);
  const badge = document.getElementById(`kw-count-badge-${tc}`);
  const emptyEl = document.getElementById(`kw-empty-${tc}`);
  const table = document.getElementById(`kw-table-${tc}`);
  if (!select || !tbody) return;

  const mode = select.value; // 'matched' | 'missing' | 'all'
  const rows = tbody.querySelectorAll("tr.kw-row");
  let visibleCount = 0;
  const totalCount = rows.length;

  rows.forEach(row => {
    const score = parseInt(row.dataset.score, 10);
    let show = false;
    if (mode === "all") show = true;
    else if (mode === "matched" && score > 0) show = true;
    else if (mode === "missing" && score === 0) show = true;

    row.style.display = show ? "" : "none";
    if (show) visibleCount++;
  });

  if (badge) {
    badge.textContent = `Showing ${visibleCount} of ${totalCount}`;
  }

  if (emptyEl && table) {
    if (visibleCount === 0) {
      table.style.display = "none";
      emptyEl.classList.remove("hidden");
      if (mode === "matched") emptyEl.textContent = "🔍 No matching keywords found in the JD for this track.";
      else if (mode === "missing") emptyEl.textContent = "🎉 Outstanding! All keywords matched for this track!";
      else emptyEl.textContent = "No keywords available.";
    } else {
      table.style.display = "";
      emptyEl.classList.add("hidden");
    }
  }
}

/* ═══════════════════════════ AI ENHANCEMENT ════════════════════════ */

async function runEnhancement(tc) {
  const jdText = getJdText();
  if (!jdText) { alert("Please analyse a JD first."); return; }

  const btn = document.getElementById(`ai-btn-${tc}`);
  const resultEl = document.getElementById(`ai-result-${tc}`);
  btn.disabled = true;
  btn.innerHTML = `<span class="ai-spinner"></span> Analysing…`;
  resultEl.innerHTML = "";

  try {
    const resp = await fetch("/enhance", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ jd_text: jdText, resume_text: resumeTexts[tc] || "", track: tc }),
    });
    const data = await resp.json();

    if (data.error === "NO_API_KEY" || data.error === "INVALID_API_KEY") {
      document.getElementById("api-key-banner").classList.remove("hidden");
      resultEl.innerHTML = `<p class="warn-msg">⚠ ${data.error === "INVALID_API_KEY" ? "API key is invalid. Please check your .env file." : "Gemini API key not configured. See the banner below."}</p>`;
      return;
    }
    if (data.error) {
      resultEl.innerHTML = `<p class="warn-msg">⚠ Error: ${escHtml(data.error)}</p>`;
      return;
    }

    resultEl.innerHTML = renderAiResult(data);
  } catch (e) {
    resultEl.innerHTML = `<p class="warn-msg">✗ Request failed: ${escHtml(e.message)}</p>`;
  } finally {
    btn.disabled = false;
    btn.innerHTML = "✨ Regenerate";
  }
}

function renderAiResult(data) {
  const { summary, gap_keywords, suggested_bullets, section_suggestions } = data;
  let html = `<div class="ai-result-section">`;

  if (summary) {
    html += `<div class="ai-result-label">Assessment</div>
             <div class="ai-summary">${escHtml(summary)}</div>`;
  }
  if (gap_keywords && gap_keywords.length) {
    html += `<div class="ai-result-label">Top Missing Keywords</div>
             <div class="gap-pills">${gap_keywords.map(k => `<span class="gap-pill">✗ ${escHtml(k)}</span>`).join("")}</div>`;
  }
  if (suggested_bullets && suggested_bullets.length) {
    html += `<div class="ai-result-label">AI-Generated Resume Bullets</div>`;
    suggested_bullets.forEach(b => {
      html += `<div class="ai-bullet-item">
        <div class="ai-bullet-text">${escHtml(b)}</div>
        <button class="copy-btn" onclick="copyBullet(this, ${JSON.stringify(b)})">Copy</button>
      </div>`;
    });
  }
  if (section_suggestions && section_suggestions.length) {
    html += `<div class="ai-result-label" style="margin-top:0.9rem">Section Suggestions</div>
             <div>
             ${section_suggestions.map(s => `<div class="suggestion-item"><span class="suggestion-dot">→</span><span>${escHtml(s)}</span></div>`).join("")}
             </div>`;
  }
  html += `</div>`;
  return html;
}

/* ═══════════════════════════ HELPERS ═══════════════════════════════ */

function renderBullets(bullets) {
  return bullets.map(b => `
    <div class="bullet-item ${b.jd_hit_computed ? "hit" : ""}">
      <div style="flex:1">
        <div class="bullet-theme">${escHtml(b.theme)}</div>
        <div class="bullet-text">${escHtml(b.bullet)}</div>
      </div>
      <div style="display:flex;flex-direction:column;gap:0.3rem;align-items:flex-end">
        <span class="bullet-hit-tag ${b.jd_hit_computed ? "hit" : "miss"}">${b.jd_hit_computed ? "✅ JD Hit" : "No Hit"}</span>
        <button class="copy-btn" onclick="copyBullet(this, ${JSON.stringify(b.bullet)})">Copy</button>
      </div>
    </div>`).join("");
}

function copyBullet(btn, text) {
  navigator.clipboard.writeText(text).then(() => {
    btn.textContent = "Copied!";
    setTimeout(() => btn.textContent = "Copy", 1500);
  });
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

/* ═══════════════════════════ CHART ═════════════════════════════════ */

const TRACK_COLORS = {
  AI:   { border: "#6c63ff", bg: "rgba(108,99,255,0.18)" },
  TPM:  { border: "#00d4aa", bg: "rgba(0,212,170,0.18)"  },
  ITDM: { border: "#ffa94d", bg: "rgba(255,169,77,0.18)" },
  PM:   { border: "#ff6b6b", bg: "rgba(255,107,107,0.18)"},
};

function switchChart(type) {
  activeChartType = type;
  document.querySelectorAll("#chart-type-toggle .toggle-btn").forEach(b => {
    b.classList.toggle("active", b.dataset.chart === type);
  });
  if (currentData) renderChart(currentData.tracks, type);
}

function renderChart(tracks, type) {
  const canvas = document.getElementById("scoreChart");
  const wrap = canvas.parentElement;

  // Destroy previous instance
  if (scoreChartInstance) { scoreChartInstance.destroy(); scoreChartInstance = null; }

  const labels = TRACK_ORDER.map(tc => tracks[tc]?.label || tc);
  const scores = TRACK_ORDER.map(tc => tracks[tc]?.pct || 0);
  const borderColors = TRACK_ORDER.map(tc => TRACK_COLORS[tc].border);
  const bgColors    = TRACK_ORDER.map(tc => TRACK_COLORS[tc].bg);

  const gridColor  = "rgba(46,49,85,0.8)";
  const textColor  = "#8b8fa8";
  const fontFamily = "'Segoe UI', system-ui, sans-serif";

  if (type === "radar") {
    wrap.classList.remove("bar-mode");
    scoreChartInstance = new Chart(canvas, {
      type: "radar",
      data: {
        labels,
        datasets: [{
          label: "Match %",
          data: scores,
          borderColor: "#6c63ff",
          backgroundColor: "rgba(108,99,255,0.12)",
          borderWidth: 2,
          pointBackgroundColor: borderColors,
          pointBorderColor: "#1a1d2e",
          pointRadius: 5,
          pointHoverRadius: 7,
        }],
      },
      options: {
        responsive: true,
        animation: { duration: 600, easing: "easeOutQuart" },
        scales: {
          r: {
            min: 0, max: 100,
            ticks: { stepSize: 25, color: textColor, font: { size: 11, family: fontFamily },
                     backdropColor: "transparent" },
            grid:        { color: gridColor },
            angleLines:  { color: gridColor },
            pointLabels: { color: "#e8eaf6", font: { size: 12, weight: "600", family: fontFamily } },
          },
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: ctx => ` ${ctx.raw}% — ${_levelLabel(ctx.raw)}`,
            },
            backgroundColor: "#242740", titleColor: "#e8eaf6", bodyColor: "#8b8fa8",
            borderColor: "#2e3155", borderWidth: 1,
          },
        },
      },
    });

  } else {
    // Bar chart
    wrap.classList.add("bar-mode");
    scoreChartInstance = new Chart(canvas, {
      type: "bar",
      data: {
        labels,
        datasets: [{
          label: "Match %",
          data: scores,
          backgroundColor: bgColors,
          borderColor: borderColors,
          borderWidth: 2,
          borderRadius: 8,
          borderSkipped: false,
        }],
      },
      options: {
        responsive: true,
        animation: { duration: 600, easing: "easeOutQuart" },
        indexAxis: "y",   // horizontal bars
        scales: {
          x: {
            min: 0, max: 100,
            ticks: {
              color: textColor, font: { size: 11, family: fontFamily },
              callback: v => v + "%",
            },
            grid: { color: gridColor },
            border: { color: gridColor },
          },
          y: {
            ticks: { color: "#e8eaf6", font: { size: 12, weight: "600", family: fontFamily } },
            grid:  { display: false },
            border: { display: false },
          },
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: ctx => ` ${ctx.raw}% — ${_levelLabel(ctx.raw)}`,
            },
            backgroundColor: "#242740", titleColor: "#e8eaf6", bodyColor: "#8b8fa8",
            borderColor: "#2e3155", borderWidth: 1,
          },
        },
      },
    });
  }
}

function _levelLabel(pct) {
  if (pct >= 70) return "Strong Match";
  if (pct >= 40) return "Moderate Match";
  return "Weak Match";
}

/* ═══════════════════════════ FULL ANALYSIS ═════════════════════════ */

async function runFullAnalysis() {
  const jdText = getJdText();
  if (!jdText) { showError("Please paste or fetch a Job Description first."); return; }

  syncResumeTexts();

  const btn = document.getElementById("full-analysis-btn");
  const scoreBtn = document.getElementById("score-btn");
  btn.disabled = true; scoreBtn.disabled = true;
  btn.innerHTML = '<span class="ai-spinner"></span> Analysing…';

  // Show loading panel, hide old grid
  document.getElementById("full-analysis-results").classList.remove("hidden");
  document.getElementById("full-analysis-loading").classList.remove("hidden");
  document.getElementById("full-analysis-grid").classList.add("hidden");

  // Animate statuses to "Running"
  TRACK_ORDER.forEach(tc => setFaStatus(tc, "running", "⟳ Running…"));

  try {
    const resp = await fetch("/enhance_all", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ jd_text: jdText, resumes: resumeTexts }),
    });
    const data = await resp.json();

    if (data.error) {
      TRACK_ORDER.forEach(tc => setFaStatus(tc, "error", "✗ Failed"));
      showError(data.error);
      return;
    }

    // Check API key
    if (data.enhancements) {
      const firstErr = Object.values(data.enhancements).find(e => e.error === "NO_API_KEY" || e.error === "INVALID_API_KEY");
      if (firstErr) {
        document.getElementById("api-key-banner").classList.remove("hidden");
        TRACK_ORDER.forEach(tc => setFaStatus(tc, "error", "✗ No API key"));
        return;
      }
    }

    // Mark all done and show scoring results first
    TRACK_ORDER.forEach(tc => setFaStatus(tc, "done", "✓ Done"));
    currentData = data.scoring;
    renderResults(data.scoring);
    checkApiKey();

    // Short delay so user sees "done" status before grid appears
    await new Promise(r => setTimeout(r, 400));

    renderFullAnalysisGrid(data.enhancements);
    document.getElementById("full-analysis-loading").classList.add("hidden");
    document.getElementById("full-analysis-grid").classList.remove("hidden");
    document.getElementById("full-analysis-grid").scrollIntoView({ behavior: "smooth", block: "start" });

  } catch (e) {
    TRACK_ORDER.forEach(tc => setFaStatus(tc, "error", "✗ Error"));
    showError("Full analysis failed: " + e.message);
  } finally {
    btn.disabled = false; scoreBtn.disabled = false;
    btn.innerHTML = "✨ Full Analysis";
  }
}

function setFaStatus(track, cls, text) {
  const el = document.querySelector(`.fa-track-status[data-track="${track}"]`);
  if (!el) return;
  el.className = `fa-track-status ${cls}`;
  el.textContent = text;
}

function renderFullAnalysisGrid(enhancements) {
  const grid = document.getElementById("fa-grid");
  grid.innerHTML = "";

  TRACK_ORDER.forEach(tc => {
    const e = enhancements[tc] || {};
    const levelClass = e.score_level_class || "weak";
    const pct = e.score_pct ?? 0;
    const label = e.track_label || tc;

    const card = document.createElement("div");
    card.className = `fa-card ${levelClass}`;

    // Header
    let html = `
      <div class="fa-card-header">
        <div class="fa-card-title">${TRACK_EMOJIS[tc]} ${escHtml(label)}</div>
        <div class="fa-score-badge">
          <span class="fa-pct">${pct}%</span>
          <span class="level-badge ${levelClass}">${escHtml(e.score_level || _levelLabel(pct))}</span>
        </div>
      </div>`;

    if (e.error && e.error !== "NO_API_KEY" && e.error !== "INVALID_API_KEY") {
      if (e.error === "RATE_LIMIT_EXCEEDED" || e.error.includes("429") || e.error.includes("RESOURCE_EXHAUSTED")) {
        html += `
          <div style="background:rgba(255,169,77,0.1);border:1px solid rgba(255,169,77,0.35);border-radius:8px;padding:0.75rem 0.9rem;margin-top:0.5rem;font-size:0.83rem">
            <div style="font-weight:600;color:var(--warn);margin-bottom:0.25rem">⏱ Gemini Rate Limit Reached (Free Tier)</div>
            <div style="color:var(--text);line-height:1.4">${escHtml(e.summary || "Google AI free tier limit reached (5 req/min). Please wait ~30 seconds and click '✨ Enhance My Resume' on this tab.")}</div>
          </div>`;
      } else if (e.error === "SERVICE_UNAVAILABLE" || e.error.includes("503")) {
        html += `
          <div style="background:rgba(255,169,77,0.1);border:1px solid rgba(255,169,77,0.35);border-radius:8px;padding:0.75rem 0.9rem;margin-top:0.5rem;font-size:0.83rem">
            <div style="font-weight:600;color:var(--warn);margin-bottom:0.25rem">⚡ AI Service Busy</div>
            <div style="color:var(--text);line-height:1.4">${escHtml(e.summary || "Google AI service is currently busy. Please wait a moment and try again.")}</div>
          </div>`;
      } else {
        html += `<p class="warn-msg" style="font-size:0.85rem">⚠ ${escHtml(e.error)}</p>`;
      }
    } else {
      // Summary
      if (e.summary) {
        html += `<div class="fa-section-label">Assessment</div>
                 <div class="fa-summary">${escHtml(e.summary)}</div>`;
      }
      // Gap keywords
      if (e.gap_keywords?.length) {
        html += `<div class="fa-section-label">Top Missing Keywords</div>
                 <div class="fa-gap-pills">
                   ${e.gap_keywords.map(k => `<span class="fa-gap-pill">✗ ${escHtml(k)}</span>`).join("")}
                 </div>`;
      }
      // AI bullets
      if (e.suggested_bullets?.length) {
        html += `<div class="fa-section-label">AI-Generated Bullets</div>`;
        e.suggested_bullets.forEach(b => {
          html += `<div class="fa-bullet">
            <span class="fa-bullet-text">${escHtml(b)}</span>
            <button class="copy-btn" onclick="copyBullet(this, ${JSON.stringify(b)})">Copy</button>
          </div>`;
        });
      }
      // Section suggestions
      if (e.section_suggestions?.length) {
        html += `<div class="fa-section-label">Section Suggestions</div>`;
        e.section_suggestions.forEach(s => {
          html += `<div class="suggestion-item"><span class="suggestion-dot">→</span><span>${escHtml(s)}</span></div>`;
        });
      }

      // Action button to tailor full resume directly for this track
      html += `
        <div style="margin-top:1rem;padding-top:0.85rem;border-top:1px solid var(--border);display:flex;justify-content:flex-end">
          <button class="tailor-btn" style="font-size:0.8rem;padding:0.4rem 0.85rem" onclick="activateTrackAndTailor('${tc}')">
            🪄 Tailor Full Resume (${tc})
          </button>
        </div>`;
    }

    card.innerHTML = html;
    grid.appendChild(card);
  });
}

function activateTrackAndTailor(tc) {
  activateTab(tc);
  const tabEl = document.getElementById("tab-content");
  if (tabEl) tabEl.scrollIntoView({ behavior: "smooth", block: "start" });
  runTailorResume(tc);
}

function clearFullAnalysis() {
  document.getElementById("full-analysis-results").classList.add("hidden");
  document.getElementById("full-analysis-loading").classList.add("hidden");
  document.getElementById("full-analysis-grid").classList.add("hidden");
  document.getElementById("fa-grid").innerHTML = "";
  TRACK_ORDER.forEach(tc => setFaStatus(tc, "", "○ Queued"));
}

/* ═══════════════════════════ BEST TRACK PICKER ═════════════════════ */

function renderBestTrackBanner(data) {
  const { best_track, best_pct, ranked_tracks, tracks } = data;
  if (!best_track) return;

  const t = tracks[best_track];
  const runnerUpTc = ranked_tracks[1];
  const runnerUpT = tracks[runnerUpTc];

  document.getElementById("bt-track-name").textContent =
    `${TRACK_EMOJIS[best_track]} ${t.label}`;
  document.getElementById("bt-pct").textContent = `${t.final_pts} pts (${t.pct}%)`;

  const levelBadge = document.getElementById("bt-level-badge");
  levelBadge.className = `level-badge ${t.level_class}`;
  levelBadge.textContent = t.level;

  document.getElementById("bt-runner-up").textContent = runnerUpT
    ? `Runner-up: ${TRACK_EMOJIS[runnerUpTc]} ${runnerUpT.label} (${runnerUpT.final_pts} pts)`
    : "";

  // Reset AI result panel
  document.getElementById("bt-ai-result").classList.add("hidden");
  document.getElementById("bt-ai-content").innerHTML = "";
  const aiBtn = document.getElementById("bt-ai-btn");
  aiBtn.disabled = false;
  aiBtn.innerHTML = "🧠 Ask AI Why";
}

async function runPickTrack() {
  const jdText = getJdText();
  if (!jdText || !currentData) { showError("Please analyse a JD first."); return; }

  const btn = document.getElementById("bt-ai-btn");
  btn.disabled = true;
  btn.innerHTML = '<span class="ai-spinner"></span> Analysing…';

  // Build scored_tracks payload
  const scoredTracks = {};
  TRACK_ORDER.forEach(tc => {
    const t = currentData.tracks[tc];
    if (t) scoredTracks[tc] = { pct: t.pct, level: t.level, label: t.label };
  });

  try {
    const resp = await fetch("/pick_track", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ jd_text: jdText, scored_tracks: scoredTracks }),
    });
    const data = await resp.json();

    if (data.error === "NO_API_KEY" || data.error === "INVALID_API_KEY") {
      document.getElementById("api-key-banner").classList.remove("hidden");
      return;
    }
    if (data.error) {
      document.getElementById("bt-ai-content").innerHTML =
        `<p class="warn-msg">⚠ ${escHtml(data.error)}</p>`;
      document.getElementById("bt-ai-result").classList.remove("hidden");
      return;
    }

    renderBtAiResult(data);

    // If AI's pick differs from score-based pick, update banner name
    if (data.recommended_track && data.recommended_track !== currentData.best_track) {
      const tc = data.recommended_track;
      const t = currentData.tracks[tc];
      if (t) {
        document.getElementById("bt-track-name").textContent =
          `${TRACK_EMOJIS[tc]} ${t.label} ✦ AI pick`;
      }
    }

  } catch (e) {
    document.getElementById("bt-ai-content").innerHTML =
      `<p class="warn-msg">✗ ${escHtml(e.message)}</p>`;
    document.getElementById("bt-ai-result").classList.remove("hidden");
  } finally {
    btn.disabled = false;
    btn.innerHTML = "🔄 Regenerate";
  }
}

function renderBtAiResult(data) {
  const { recommended_track, confidence, reason, runner_up,
          runner_up_reason, jd_signals, strengthen_tips } = data;

  const tc = recommended_track;
  const t = currentData?.tracks?.[tc];
  const confCls = (confidence || "low").toLowerCase();

  let html = `
    <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.75rem;flex-wrap:wrap">
      <strong style="font-size:1rem">🧠 AI Recommends: ${TRACK_EMOJIS[tc] || ""} ${escHtml(t?.label || tc)}</strong>
      <span class="bt-confidence ${confCls}">
        ${ confCls === "high" ? "●●●" : confCls === "medium" ? "●●○" : "●○○" }
        ${escHtml(confidence || "Low")} Confidence
      </span>
    </div>`;

  if (reason) {
    html += `<div class="bt-reason">${escHtml(reason)}</div>`;
  }

  if (jd_signals?.length) {
    html += `<div class="fa-section-label">Key JD Signals</div>
             <div class="bt-signals">
               ${jd_signals.map(s => `<span class="bt-signal-pill">"${escHtml(s)}"</span>`).join("")}
             </div>`;
  }

  if (runner_up) {
    const ruT = currentData?.tracks?.[runner_up];
    html += `<div class="fa-section-label">Runner-Up</div>
             <div class="bt-runner-card">
               <div class="bt-runner-label">${TRACK_EMOJIS[runner_up] || ""} ${escHtml(ruT?.label || runner_up)}</div>
               <div>${escHtml(runner_up_reason || "")}</div>
             </div>`;
  }

  if (strengthen_tips?.length) {
    html += `<div class="fa-section-label">Tips to Strengthen Your Resume for This Role</div>
             <div>
               ${strengthen_tips.map((tip, i) =>
                 `<div class="bt-tip-item">
                    <span class="bt-tip-num">${i + 1}</span>
                    <span>${escHtml(tip)}</span>
                  </div>`
               ).join("")}
             </div>`;
  }

  document.getElementById("bt-ai-content").innerHTML = html;
  document.getElementById("bt-ai-result").classList.remove("hidden");
  document.getElementById("bt-ai-result").scrollIntoView({ behavior: "smooth", block: "nearest" });
}

/* ═══════════════════════════ AI FULL RESUME TAILORER ════════════════ */

window._tailoredResumes = {};

async function runTailorResume(tc) {
  const jdText = getJdText();
  if (!jdText) { alert("Please analyse a JD first."); return; }

  const btn = document.getElementById(`tailor-btn-${tc}`);
  const resultEl = document.getElementById(`tailor-result-${tc}`);
  btn.disabled = true;
  btn.innerHTML = `<span class="ai-spinner"></span> Tailoring Full Resume…`;
  resultEl.innerHTML = "";

  try {
    const resp = await fetch("/tailor_resume", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ jd_text: jdText, resume_text: resumeTexts[tc] || "", track: tc }),
    });
    const data = await resp.json();

    if (data.error === "NO_API_KEY" || data.error === "INVALID_API_KEY") {
      document.getElementById("api-key-banner").classList.remove("hidden");
      resultEl.innerHTML = `<p class="warn-msg">⚠ ${data.error === "INVALID_API_KEY" ? "API key is invalid." : "Gemini API key not configured."}</p>`;
      return;
    }
    if (data.error === "RATE_LIMIT_EXCEEDED") {
      resultEl.innerHTML = `<div style="background:rgba(255,169,77,0.1);border:1px solid rgba(255,169,77,0.35);border-radius:8px;padding:0.75rem 0.9rem;margin-top:0.75rem;font-size:0.83rem"><div style="font-weight:600;color:var(--warn);margin-bottom:0.25rem">⏱ Gemini Rate Limit Reached (Free Tier)</div><div>Please wait ~30 seconds and try again.</div></div>`;
      return;
    }
    if (data.error) {
      resultEl.innerHTML = `<p class="warn-msg">⚠ Error: ${escHtml(data.error)}</p>`;
      return;
    }

    window._tailoredResumes[tc] = data;
    renderTailoredResume(tc, data);

  } catch (e) {
    resultEl.innerHTML = `<p class="warn-msg">✗ Request failed: ${escHtml(e.message)}</p>`;
  } finally {
    btn.disabled = false;
    btn.innerHTML = "🪄 Regenerate Full Resume";
  }
}

function renderTailoredResume(tc, data) {
  const resultEl = document.getElementById(`tailor-result-${tc}`);
  const md = data.full_markdown || "";
  const origResume = resumeTexts[tc] || "(No candidate resume uploaded for this track)";

  let html = `
    <div class="tailor-res-card">
      <div class="tailor-header">
        <div class="tailor-title-badge">🎯 AI-Tailored Executive Resume (${escHtml(data.job_title || tc)})</div>
        <div class="tailor-actions">
          <button class="tailor-action-btn" onclick="copyTailoredMd('${tc}')">📋 Copy Markdown</button>
          <button class="tailor-action-btn" onclick="downloadDocxFile('${tc}')">📥 Download Word (.docx)</button>
          <button class="tailor-action-btn" onclick="downloadTxtFile('${tc}')">📄 Download Text (.txt)</button>
          <button class="tailor-action-btn" onclick="window.print()">🖨️ Print / Save PDF</button>
        </div>
      </div>

      <div class="tailor-view-bar">
        <button class="tailor-view-btn active" id="tv-btn-md-${tc}" onclick="switchTailorView('${tc}', 'md')">💻 Formatted Resume</button>
        <button class="tailor-view-btn" id="tv-btn-split-${tc}" onclick="switchTailorView('${tc}', 'split')">⚔️ Side-by-Side View</button>
        <button class="tailor-view-btn" id="tv-btn-edit-${tc}" onclick="switchTailorView('${tc}', 'edit')">✏️ Edit & Customise</button>
      </div>

      <!-- View 1: Formatted Resume Box -->
      <div id="tv-box-md-${tc}" class="tailor-md-box">${escHtml(md)}</div>

      <!-- View 2: Side-by-Side Comparison -->
      <div id="tv-box-split-${tc}" class="tailor-split-grid hidden">
        <div class="tailor-split-col">
          <div class="tailor-col-title">📄 Original Candidate Resume</div>
          <div class="tailor-md-box" style="max-height:340px">${escHtml(origResume)}</div>
        </div>
        <div class="tailor-split-col">
          <div class="tailor-col-title">✨ AI-Tailored Resume (${escHtml(data.job_title || tc)})</div>
          <div class="tailor-md-box" style="max-height:340px">${escHtml(md)}</div>
        </div>
      </div>

      <!-- View 3: Live Editable Textarea -->
      <div id="tv-box-edit-${tc}" class="hidden">
        <p style="font-size:0.82rem;color:var(--muted);margin-bottom:0.5rem">💡 Tip: Any edits you make here will be saved live and included when you click "Download Word (.docx)" or "Copy Markdown".</p>
        <textarea id="tv-textarea-${tc}" class="tailor-edit-textarea" oninput="onTailorEdit('${tc}')">${escHtml(md)}</textarea>
      </div>
    </div>`;

  resultEl.innerHTML = html;
  resultEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function switchTailorView(tc, mode) {
  document.querySelectorAll(`.tailor-view-btn[id^="tv-btn-"][id$="-${tc}"]`).forEach(b => b.classList.remove("active"));
  document.getElementById(`tv-btn-${mode}-${tc}`)?.classList.add("active");

  document.getElementById(`tv-box-md-${tc}`)?.classList.toggle("hidden", mode !== "md");
  document.getElementById(`tv-box-split-${tc}`)?.classList.toggle("hidden", mode !== "split");
  document.getElementById(`tv-box-edit-${tc}`)?.classList.toggle("hidden", mode !== "edit");
}

function onTailorEdit(tc) {
  const textarea = document.getElementById(`tv-textarea-${tc}`);
  if (!textarea) return;
  const newMd = textarea.value;
  if (window._tailoredResumes[tc]) {
    window._tailoredResumes[tc].full_markdown = newMd;
  }
  const boxMd = document.getElementById(`tv-box-md-${tc}`);
  if (boxMd) boxMd.textContent = newMd;
}

async function downloadDocxFile(tc) {
  const data = window._tailoredResumes[tc];
  if (!data || !data.full_markdown) return;

  const filename = `${tc}_Tailored_Resume.docx`;
  try {
    const resp = await fetch("/download_docx", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ markdown_text: data.full_markdown, filename: filename }),
    });
    const blob = await resp.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  } catch(e) {
    alert("Download failed: " + e.message);
  }
}

function downloadTxtFile(tc) {
  const data = window._tailoredResumes[tc];
  if (!data || !data.full_markdown) return;
  const blob = new Blob([data.full_markdown], { type: "text/plain;charset=utf-8" });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${tc}_Tailored_Resume.txt`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

function copyTailoredMd(tc) {
  const data = window._tailoredResumes[tc];
  if (!data || !data.full_markdown) return;
  navigator.clipboard.writeText(data.full_markdown).then(() => {
    alert("Tailored Resume copied to clipboard!");
  });
}