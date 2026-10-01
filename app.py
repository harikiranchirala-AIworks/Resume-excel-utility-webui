"""
app.py  —  Flask application entry point (Phase 2 — URL + Resume + AI)
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, render_template, request, jsonify
from scorer import score_jd
from url_fetcher import fetch_jd_from_url
from resume_parser import parse_resume
from ai_enhancer import enhance_resume, get_api_key

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB max upload

TRACK_ORDER = ["AI", "TPM", "ITDM", "PM"]


@app.route("/")
def index():
    return render_template("index.html")


# ── SCORE JD ──────────────────────────────────────────────────────────────────
@app.route("/score", methods=["POST"])
def score():
    data = request.get_json(force=True)
    jd_text = data.get("jd_text", "").strip()
    if not jd_text:
        return jsonify({"error": "Please paste a Job Description before scoring."}), 400
    try:
        result = score_jd(jd_text)
        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ── FETCH JD FROM URL ─────────────────────────────────────────────────────────
@app.route("/fetch_jd", methods=["POST"])
def fetch_jd():
    data = request.get_json(force=True)
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "Please provide a URL."}), 400
    try:
        result = fetch_jd_from_url(url)
        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ── UPLOAD RESUME ─────────────────────────────────────────────────────────────
@app.route("/upload_resume", methods=["POST"])
def upload_resume():
    track = request.form.get("track", "AI")
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "Empty filename."}), 400
    try:
        text = parse_resume(f.read(), f.filename)
        from master_resumes import update_single_master_resume
        updated_master = update_single_master_resume(track, text)
        return jsonify({"text": text, "track": track, "filename": f.filename, "master_resumes": updated_master})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Could not parse file: {str(e)}"}), 500


# ── AI ENHANCE (single track) ─────────────────────────────────────────────────
@app.route("/enhance", methods=["POST"])
def enhance():
    data = request.get_json(force=True)
    jd_text = data.get("jd_text", "").strip()
    resume_text = data.get("resume_text", "").strip()
    track_code = data.get("track", "AI")

    if not jd_text:
        return jsonify({"error": "Job description is required for AI enhancement."}), 400

    try:
        scoring_result = score_jd(jd_text)
        scored_kws = scoring_result["tracks"].get(track_code, {}).get("keywords", [])
    except Exception:
        scored_kws = []

    result = enhance_resume(jd_text, resume_text, track_code, scored_kws)
    return jsonify(result)


# ── AI ENHANCE ALL TRACKS (parallel) ──────────────────────────────────────────
@app.route("/enhance_all", methods=["POST"])
def enhance_all():
    data = request.get_json(force=True)
    jd_text = data.get("jd_text", "").strip()
    resumes = data.get("resumes", {})   # {track_code: resume_text}

    if not jd_text:
        return jsonify({"error": "Job description is required."}), 400

    # Score once — reuse for all tracks
    try:
        scoring_result = score_jd(jd_text)
    except Exception as exc:
        return jsonify({"error": f"Scoring failed: {str(exc)}"}), 500

    def _enhance_track(track_code):
        scored_kws = scoring_result["tracks"].get(track_code, {}).get("keywords", [])
        resume_text = resumes.get(track_code, "").strip()
        result = enhance_resume(jd_text, resume_text, track_code, scored_kws)
        result["track"] = track_code
        result["score_pct"] = scoring_result["tracks"].get(track_code, {}).get("pct", 0)
        result["score_level"] = scoring_result["tracks"].get(track_code, {}).get("level", "")
        result["score_level_class"] = scoring_result["tracks"].get(track_code, {}).get("level_class", "")
        result["track_label"] = scoring_result["tracks"].get(track_code, {}).get("label", track_code)
        return track_code, result

    combined = {}
    # Run 4 tracks sequentially with a 1.2s delay to respect Gemini Free Tier rate limits (5 RPM)
    import time
    for idx, tc in enumerate(TRACK_ORDER):
        if idx > 0:
            time.sleep(1.2)
        try:
            _, result = _enhance_track(tc)
            combined[tc] = result
        except Exception as exc:
            combined[tc] = {"error": str(exc), "track": tc}

    return jsonify({
        "scoring": scoring_result,
        "enhancements": combined,
    })


# ── AI TAILOR FULL RESUME ─────────────────────────────────────────────────────
@app.route("/tailor_resume", methods=["POST"])
def tailor_resume():
    data = request.get_json(force=True)
    jd_text = data.get("jd_text", "").strip()
    resume_text = data.get("resume_text", "").strip()
    track_code = data.get("track", "AI").strip().upper()
    candidate_info = data.get("candidate_info", {})
    preferred_model = data.get("preferred_model")

    if not jd_text:
        return jsonify({"error": "Job description is required."}), 400

    try:
        from scorer import score_jd
        scoring_result = score_jd(jd_text)
        scored_kws = scoring_result["tracks"].get(track_code, {}).get("keywords", [])
    except Exception:
        scored_kws = []

    from ai_enhancer import tailor_full_resume
    result = tailor_full_resume(jd_text, resume_text, track_code, scored_kws, candidate_info)
    return jsonify(result)


@app.route("/inject_keyword_bullet", methods=["POST"])
def inject_keyword_bullet():
    data = request.get_json(force=True) or {}
    keyword = data.get("keyword", "").strip()
    track_code = data.get("track", "AI").strip().upper()
    jd_text = data.get("jd_text", "").strip()
    resume_text = data.get("resume_text", "").strip()
    candidate_info = data.get("candidate_info", {})
    preferred_model = data.get("preferred_model")

    if not keyword:
        return jsonify({"error": "Keyword parameter is required."}), 400

    from ai_enhancer import generate_single_keyword_bullet
    result = generate_single_keyword_bullet(keyword, track_code, jd_text, resume_text, candidate_info, preferred_model)
    return jsonify(result)


# ── DOWNLOAD DOCX ATTACHMENT ──────────────────────────────────────────────────
@app.route("/download_docx", methods=["POST"])
def download_docx():
    from io import BytesIO
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.style import WD_STYLE_TYPE
    from flask import send_file

    data = request.get_json(force=True)
    markdown_text = data.get("markdown_text", "").strip()
    filename = data.get("filename", "Tailored_Resume.docx")
    template_style = data.get("template_style", "modern").lower()
    accent_hex = data.get("accent_color", "#4f46e5").lstrip("#")
    font_name = data.get("font_family", "Calibri")

    try:
        r = int(accent_hex[0:2], 16)
        g = int(accent_hex[2:4], 16)
        b = int(accent_hex[4:6], 16)
        accent_color = RGBColor(r, g, b)
    except Exception:
        accent_color = RGBColor(79, 70, 229)

    doc = Document()

    # Set document margins
    margin_val = 0.4 if template_style == "compact" else 0.6
    for section in doc.sections:
        section.top_margin = Inches(margin_val)
        section.bottom_margin = Inches(margin_val)
        section.left_margin = Inches(margin_val + 0.05)
        section.right_margin = Inches(margin_val + 0.05)

    # Set base font style
    normal_style = doc.styles['Normal']
    normal_style.font.name = font_name
    normal_style.font.size = Pt(9 if template_style == "compact" else 10)
    normal_style.font.color.rgb = RGBColor(30, 41, 59)

    lines = markdown_text.splitlines()
    for idx, line in enumerate(lines):
        line_str = line.strip()
        if not line_str:
            continue

        if line_str.startswith("# "):
            p = doc.add_paragraph()
            if template_style == "classic":
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(line_str[2:])
            run.font.name = font_name
            run.font.size = Pt(20 if template_style != "compact" else 18)
            run.font.bold = True
            run.font.color.rgb = accent_color
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(2)

        elif line_str.startswith("## "):
            p = doc.add_paragraph()
            run = p.add_run(line_str[3:].upper())
            run.font.name = font_name
            run.font.size = Pt(12)
            run.font.bold = True
            run.font.color.rgb = accent_color
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(4)

        elif line_str.startswith("### "):
            p = doc.add_paragraph()
            run = p.add_run(line_str[4:])
            run.font.name = font_name
            run.font.size = Pt(10.5)
            run.font.bold = True
            run.font.color.rgb = RGBColor(51, 65, 85)
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(2)

        elif line_str.startswith("- ") or line_str.startswith("* "):
            p = doc.add_paragraph(style='List Bullet')
            # Check for bold inline text (e.g. **Title**: text)
            bullet_text = line_str[2:]
            if "**" in bullet_text:
                parts = bullet_text.split("**")
                for i, part in enumerate(parts):
                    if not part:
                        continue
                    r = p.add_run(part)
                    r.font.name = font_name
                    r.font.size = Pt(9.5)
                    if i % 2 == 1:
                        r.font.bold = True
            else:
                r = p.add_run(bullet_text)
                r.font.name = font_name
                r.font.size = Pt(9.5)
            p.paragraph_format.space_after = Pt(2)

        else:
            p = doc.add_paragraph()
            # If line is candidate header contact details line (contains | )
            if "|" in line_str and idx < 4:
                if template_style == "classic":
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = p.add_run(line_str)
                r.font.name = font_name
                r.font.size = Pt(9.5)
                r.font.color.rgb = RGBColor(100, 116, 139)
                p.paragraph_format.space_after = Pt(10)
            else:
                r = p.add_run(line_str)
                r.font.name = font_name
                r.font.size = Pt(10)
                p.paragraph_format.space_after = Pt(4)

    target = BytesIO()
    doc.save(target)
    target.seek(0)
    return send_file(
        target,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=True,
        download_name=filename
    )


# ── JOB APPLICATION CRM (KANBAN BOARD) ENDPOINTS ─────────────────────────────
@app.route("/api/crm/applications", methods=["GET"])
def get_crm_applications():
    from applications_crm import load_applications
    apps = load_applications()
    return jsonify({"applications": apps})


@app.route("/api/crm/applications", methods=["POST"])
def save_crm_application():
    data = request.get_json(force=True) or {}
    if not data.get("title") and not data.get("jd_text"):
        return jsonify({"error": "Job title or JD text is required."}), 400

    from applications_crm import save_application
    saved = save_application(data)
    return jsonify({"success": True, "application": saved})


@app.route("/api/crm/applications/<app_id>", methods=["PUT"])
def update_crm_stage(app_id):
    data = request.get_json(force=True) or {}
    status = data.get("status")
    if not status:
        return jsonify({"error": "New status is required."}), 400

    from applications_crm import update_application_status
    updated = update_application_status(app_id, status)
    if updated:
        return jsonify({"success": True, "application": updated})
    return jsonify({"error": "Application not found."}), 404


@app.route("/api/crm/applications/<app_id>", methods=["DELETE"])
def delete_crm_application_endpoint(app_id):
    from applications_crm import delete_application
    deleted = delete_application(app_id)
    return jsonify({"success": deleted})


# ── SKILL FREQUENCY HEATMAP & CAREER ANALYTICS ENDPOINT ──────────────────────
@app.route("/api/analytics/skill_heatmap", methods=["GET"])
def skill_heatmap_analytics():
    from analytics_manager import get_skill_heatmap_analytics
    data = get_skill_heatmap_analytics()
    return jsonify(data)


# ── ONE-CLICK BOOKMARKLET & BROWSER EXTENSION IMPORT ──────────────────────────
@app.route("/api/import_jd", methods=["POST", "OPTIONS"])
def import_jd():
    if request.method == "OPTIONS":
        res = jsonify({"status": "ok"})
        res.headers.add("Access-Control-Allow-Origin", "*")
        res.headers.add("Access-Control-Allow-Headers", "Content-Type")
        res.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return res

    data = request.get_json(force=True) or {}
    jd_text = data.get("jd_text", "").strip()
    title = data.get("title", "").strip()
    company = data.get("company", "").strip()
    job_url = data.get("job_url", "").strip()

    if not jd_text:
        res = jsonify({"error": "Job description text is empty."})
        res.headers.add("Access-Control-Allow-Origin", "*")
        return res, 400

    # Score JD automatically
    try:
        scoring_result = score_jd(jd_text)
    except Exception:
        scoring_result = {}

    res = jsonify({
        "success": True,
        "title": title,
        "company": company,
        "job_url": job_url,
        "jd_text": jd_text,
        "scoring": scoring_result
    })
    res.headers.add("Access-Control-Allow-Origin", "*")
    return res


# ── MASTER RESUMES (ONE-TIME PERSISTENT RESUMES) ENDPOINTS ───────────────────
@app.route("/api/master_resumes", methods=["GET"])
def get_master_resumes():
    from master_resumes import load_master_resumes
    resumes = load_master_resumes()
    return jsonify({"resumes": resumes})


@app.route("/api/master_resumes/save", methods=["POST"])
def save_master_resumes_endpoint():
    data = request.get_json(force=True) or {}
    resumes = data.get("resumes", {})
    candidate_info = data.get("candidate_info", {})
    if candidate_info:
        resumes["candidate_info"] = candidate_info
    from master_resumes import save_master_resumes
    saved = save_master_resumes(resumes)
    return jsonify({"success": True, "resumes": saved})


@app.route("/batch_upload_resumes", methods=["POST"])
def batch_upload_resumes():
    """Upload multiple resume files for tracks AI, TPM, ITDM, PM in one request."""
    from master_resumes import save_master_resumes, load_master_resumes
    current = load_master_resumes()
    uploaded_counts = 0
    errors = []

    for track in ["AI", "TPM", "ITDM", "PM"]:
        key = f"file_{track}"
        if key in request.files:
            f = request.files[key]
            if f and f.filename:
                try:
                    text = parse_resume(f.read(), f.filename)
                    current[track] = text
                    uploaded_counts += 1
                except Exception as e:
                    errors.append(f"{track} file error: {str(e)}")

    saved = save_master_resumes(current)
    return jsonify({
        "success": True,
        "uploaded_count": uploaded_counts,
        "errors": errors,
        "resumes": saved
    })


# ── ADVANCED FEATURES: INTERVIEW PREP, ATS AUDIT, COVER LETTER, MULTI-JD ────
@app.route("/interview_prep", methods=["POST"])
def interview_prep():
    data = request.get_json(force=True)
    jd_text = data.get("jd_text", "").strip()
    resume_text = data.get("resume_text", "").strip()
    track_code = data.get("track", "AI").strip().upper()

    if not jd_text:
        return jsonify({"error": "Job description is required."}), 400

    from scorer import score_jd
    try:
        scoring_result = score_jd(jd_text)
        scored_kws = scoring_result["tracks"].get(track_code, {}).get("keywords", [])
    except Exception:
        scored_kws = []

    from ai_enhancer import generate_interview_prep
    result = generate_interview_prep(jd_text, resume_text, track_code, scored_kws)
    return jsonify(result)


@app.route("/ats_audit", methods=["POST"])
def ats_audit():
    data = request.get_json(force=True)
    jd_text = data.get("jd_text", "").strip()
    resume_text = data.get("resume_text", "").strip()
    track_code = data.get("track", "AI").strip().upper()

    if not jd_text:
        return jsonify({"error": "Job description is required."}), 400

    from scorer import score_jd
    try:
        scoring_result = score_jd(jd_text)
        scored_kws = scoring_result["tracks"].get(track_code, {}).get("keywords", [])
    except Exception:
        scored_kws = []

    from ai_enhancer import audit_ats_readiness
    result = audit_ats_readiness(jd_text, resume_text, track_code, scored_kws)
    return jsonify(result)


@app.route("/generate_cover_letter", methods=["POST"])
def cover_letter():
    data = request.get_json(force=True)
    jd_text = data.get("jd_text", "").strip()
    resume_text = data.get("resume_text", "").strip()
    track_code = data.get("track", "AI").strip().upper()
    candidate_info = data.get("candidate_info", {})

    if not jd_text:
        return jsonify({"error": "Job description is required."}), 400

    from ai_enhancer import generate_cover_letter
    result = generate_cover_letter(jd_text, resume_text, track_code, candidate_info)
    return jsonify(result)


@app.route("/download_cover_letter_docx", methods=["POST"])
def download_cover_letter_docx():
    from io import BytesIO
    from docx import Document
    from flask import send_file

    data = request.get_json(force=True)
    markdown_text = data.get("markdown_text", "").strip()
    filename = data.get("filename", "Executive_Cover_Letter.docx")

    doc = Document()
    for line in markdown_text.splitlines():
        line_str = line.strip()
        if line_str.startswith("# "):
            doc.add_heading(line_str[2:], level=1)
        elif line_str.startswith("## "):
            doc.add_heading(line_str[3:], level=2)
        elif line_str:
            doc.add_paragraph(line_str)

    target = BytesIO()
    doc.save(target)
    target.seek(0)
    return send_file(
        target,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=True,
        download_name=filename
    )


@app.route("/compare_jds", methods=["POST"])
def compare_jds():
    data = request.get_json(force=True)
    jds = data.get("jds", [])
    if not jds or len(jds) < 2:
        return jsonify({"error": "At least 2 Job Descriptions are required for comparison."}), 400

    from scorer import score_jd
    comparison_results = []
    for idx, jd in enumerate(jds):
        jd_text = jd.get("text", "").strip()
        jd_title = jd.get("title", f"JD #{idx+1}").strip()
        if not jd_text:
            continue
        try:
            res = score_jd(jd_text)
            comparison_results.append({
                "title": jd_title,
                "best_track": res.get("best_track"),
                "best_pct": res.get("tracks", {}).get(res.get("best_track"), {}).get("pct", 0),
                "signals": res.get("signals", {}),
                "tracks": {tc: {"pct": t.get("pct"), "level": t.get("level")} for tc, t in res.get("tracks", {}).items()}
            })
        except Exception as e:
            comparison_results.append({"title": jd_title, "error": str(e)})

    return jsonify({"comparison": comparison_results})



# ── AI PICK BEST TRACK ────────────────────────────────────────────────────────
@app.route("/pick_track", methods=["POST"])
def pick_track():
    data = request.get_json(force=True)
    jd_text = data.get("jd_text", "").strip()
    scored_tracks = data.get("scored_tracks", {})   # {tc: {pct, level, label}}

    if not jd_text:
        return jsonify({"error": "Job description is required."}), 400

    from ai_enhancer import get_api_key
    api_key = get_api_key()
    if not api_key:
        return jsonify({"error": "NO_API_KEY"}), 200

    scores_summary = "\n".join(
        f"- {v.get('label', tc)}: {v.get('pct', 0)}% ({v.get('level', '')})"
        for tc, v in scored_tracks.items()
    )

    prompt = f"""You are a senior career coach and resume strategist.

## Job Description (first 2500 chars)
{jd_text[:2500]}

## Keyword Match Scores
{scores_summary}

## Your Task
Analyze the JD carefully — look at the role title, responsibilities, required skills, and seniority signals.
Then decide which of the 4 professional resume tracks is the BEST fit for this JD.

Tracks available:
- AI: AI Transformation Manager
- TPM: Technical Program Manager
- ITDM: IT Delivery Manager
- PM: Product Manager

Respond ONLY with valid JSON (no markdown fences):
{{
  "recommended_track": "<one of: AI, TPM, ITDM, PM>",
  "confidence": "<High | Medium | Low>",
  "reason": "<2-3 sentence explanation of why this track is the best fit>",
  "runner_up": "<second best track code>",
  "runner_up_reason": "<1 sentence why it's a close second>",
  "jd_signals": ["<key phrase or signal from the JD that drove your recommendation>", "..."],
  "strengthen_tips": [
    "<specific tip to better align resume to this JD>",
    "<tip 2>",
    "<tip 3>"
  ]
}}"""

    import warnings, time, json as _json
    from google import genai
    from google.genai import types
    warnings.filterwarnings("ignore", category=UserWarning)

    try:
        client = genai.Client(api_key=api_key)
        last_exc = None
        for attempt, wait in enumerate([0, 3, 7]):
            if wait:
                time.sleep(wait)
            try:
                response = client.models.generate_content(
                    model="models/gemini-3.6-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.3),
                )
                break
            except Exception as exc:
                last_exc = exc
                if "503" in str(exc) or "UNAVAILABLE" in str(exc) or "429" in str(exc):
                    if attempt < 2:
                        continue
                raise last_exc
        else:
            raise last_exc

        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
            if raw.endswith("```"):
                raw = raw.rsplit("```", 1)[0]
        result = _json.loads(raw.strip())
        result["error"] = None
        return jsonify(result)

    except _json.JSONDecodeError:
        return jsonify({"error": "AI response could not be parsed. Please try again."}), 500
    except Exception as e:
        err = str(e)
        if "API_KEY_INVALID" in err or "API key not valid" in err:
            return jsonify({"error": "INVALID_API_KEY"}), 200
        return jsonify({"error": err}), 500


# ── JOB SEARCH & ROLE SUGGESTIONS ENDPOINT ─────────────────────────────────
@app.route("/api/job_suggestions", methods=["GET"])
def get_job_suggestions():
    from job_suggestions import TRACK_TARGET_ROLES, DOMAIN_RULES, build_job_search_urls
    
    track = request.args.get("track", "ALL").upper()
    location = request.args.get("location", "").strip()

    roles_data = {}
    if track == "ALL" or track not in TRACK_TARGET_ROLES:
        for tc, info in TRACK_TARGET_ROLES.items():
            roles_data[tc] = {
                **info,
                "role_links": [
                    {
                        "title": title,
                        "urls": build_job_search_urls(title, location)
                    }
                    for title in info["titles"]
                ]
            }
    else:
        info = TRACK_TARGET_ROLES[track]
        roles_data[track] = {
            **info,
            "role_links": [
                {
                    "title": title,
                    "urls": build_job_search_urls(title, location)
                }
                for title in info["titles"]
            ]
        }

    return jsonify({
        "tracks": roles_data,
        "domain_rules": DOMAIN_RULES
    })


# ── RECRUITER INMAIL / ELEVATOR PITCH ENDPOINT ──────────────────────────────
@app.route("/generate_recruiter_pitch", methods=["POST"])
def generate_pitch_route():
    data = request.get_json(force=True) or {}
    jd_text = data.get("jd_text", "").strip()
    track_code = data.get("track", "AI").upper()
    resume_text = data.get("resume_text", "").strip()
    candidate_info = data.get("candidate_info", {})
    preferred_model = data.get("preferred_model")

    if not jd_text:
        return jsonify({"error": "Job description text is required."}), 400

    from ai_enhancer import generate_recruiter_pitch
    res = generate_recruiter_pitch(jd_text, track_code, resume_text, candidate_info, preferred_model)
    return jsonify(res)


# ── API KEY STATUS ────────────────────────────────────────────────────────────
@app.route("/api_key_status", methods=["GET"])
def api_key_status():
    return jsonify({"configured": bool(get_api_key())})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

