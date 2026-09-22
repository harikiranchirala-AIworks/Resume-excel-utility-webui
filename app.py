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
        return jsonify({"text": text, "track": track, "filename": f.filename})
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

    if not jd_text:
        return jsonify({"error": "Job description is required."}), 400

    try:
        from scorer import score_jd
        scoring_result = score_jd(jd_text)
        scored_kws = scoring_result["tracks"].get(track_code, {}).get("keywords", [])
    except Exception:
        scored_kws = []

    from ai_enhancer import tailor_full_resume
    result = tailor_full_resume(jd_text, resume_text, track_code, scored_kws)
    return jsonify(result)


# ── DOWNLOAD DOCX ATTACHMENT ──────────────────────────────────────────────────
@app.route("/download_docx", methods=["POST"])
def download_docx():
    from io import BytesIO
    from docx import Document
    from flask import send_file

    data = request.get_json(force=True)
    markdown_text = data.get("markdown_text", "").strip()
    filename = data.get("filename", "Tailored_Resume.docx")

    doc = Document()
    for line in markdown_text.splitlines():
        line_str = line.strip()
        if line_str.startswith("# "):
            doc.add_heading(line_str[2:], level=1)
        elif line_str.startswith("## "):
            doc.add_heading(line_str[3:], level=2)
        elif line_str.startswith("### "):
            doc.add_heading(line_str[4:], level=3)
        elif line_str.startswith("- ") or line_str.startswith("* "):
            doc.add_paragraph(line_str[2:], style='List Bullet')
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


# ── API KEY STATUS ────────────────────────────────────────────────────────────
@app.route("/api_key_status", methods=["GET"])
def api_key_status():
    return jsonify({"configured": bool(get_api_key())})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
