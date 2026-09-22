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
  const { tracks, bullets, matched_keywords } = data;
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
      <div class="score-num">${t.pct}%</div>
      <span class="level-badge">${t.level}</span>
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
  const trackBullets = bullets[tc] || [];
  const hitBullets = trackBullets.filter(b => b.jd_hit_computed);
  const otherBullets = trackBullets.filter(b => !b.jd_hit_computed);
  const hasResume = !!resumeTexts[tc];

  content.innerHTML = `
    ${matched.length ? `
    <div class="matched-kw-section">
      <h4>✅ Matched Keywords (${matched.length}/${t.keywords.length})</h4>
      <div class="kw-pills">${matched.map(k => `<span class="kw-pill">${escHtml(k.keyword)}</span>`).join("")}</div>
    </div>` : ""}

    <table class="keyword-table">
      <thead><tr><th>Keyword / Theme</th><th>Weight</th><th>Score</th><th>Weighted</th><th>Matched As</th></tr></thead>
      <tbody>
        ${t.keywords.map(k => `
          <tr class="${k.score > 0 ? "hit" : ""}">
            <td>${escHtml(k.keyword)}</td>
            <td>${k.weight}</td>
            <td><span class="badge-score s${k.score}">${k.score}</span></td>
            <td>${k.weighted}</td>
            <td style="color:var(--muted);font-size:0.82rem">${k.matched_term ? escHtml(k.matched_term) : "—"}</td>
          </tr>`).join("")}
      </tbody>
    </table>

    <hr class="section-divider" />

    ${hitBullets.length ? `<div class="bullets-header">✅ JD-Matching Bullets (${hitBullets.length})</div>${renderBullets(hitBullets)}` : ""}
    ${otherBullets.length ? `<div class="bullets-header" style="color:var(--muted)">📋 Other Bullets</div>${renderBullets(otherBullets)}` : ""}

    <!-- AI Enhancement Panel -->
    <div class="ai-panel">
      <div class="ai-panel-header">
        <div class="ai-panel-title">✨ AI Resume Enhancement — ${t.label}</div>
        <button class="ai-enhance-btn" id="ai-btn-${tc}" onclick="runEnhancement('${tc}')">
          ${hasResume ? "✨ Enhance My Resume" : "✨ Generate Suggestions"}
        </button>
      </div>
      ${!hasResume ? `<p style="color:var(--muted);font-size:0.85rem">No resume provided for this track — AI will generate general suggestions based on the JD. Add your resume above for personalised advice.</p>` : `<p style="color:var(--accent2);font-size:0.85rem">✓ Resume loaded for this track. Click to get personalised suggestions.</p>`}
      <div id="ai-result-${tc}"></div>
    </div>
  `;
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
      html += `<p class="warn-msg" style="font-size:0.85rem">✗ ${escHtml(e.error)}</p>`;
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
    }

    card.innerHTML = html;
    grid.appendChild(card);
  });
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
  document.getElementById("bt-pct").textContent = `${best_pct}%`;

  const levelBadge = document.getElementById("bt-level-badge");
  levelBadge.className = `level-badge ${t.level_class}`;
  levelBadge.textContent = t.level;

  document.getElementById("bt-runner-up").textContent = runnerUpT
    ? `Runner-up: ${TRACK_EMOJIS[runnerUpTc]} ${runnerUpT.label} (${runnerUpT.pct}%)`
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