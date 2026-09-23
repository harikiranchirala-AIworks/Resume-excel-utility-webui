"""
ai_enhancer.py
Uses Google Gemini to generate resume enhancement suggestions.
"""
import os
import json
from dotenv import load_dotenv

load_dotenv()

TRACK_LABELS = {
    "AI": "AI Transformation Manager",
    "TPM": "Technical Program Manager",
    "ITDM": "IT Delivery Manager",
    "PM": "Product Manager",
}


def get_api_key() -> str | None:
    return os.getenv("GEMINI_API_KEY", "").strip() or None


def enhance_resume(
    jd_text: str,
    resume_text: str,
    track_code: str,
    scored_keywords: list[dict],
) -> dict:
    """
    Call Gemini to produce gap analysis + resume suggestions.

    Returns:
      {
        gap_keywords: [str],
        suggested_bullets: [str],
        section_suggestions: [str],
        summary: str,
        error: str | None
      }
    """
    api_key = get_api_key()
    if not api_key:
        return {
            "gap_keywords": [],
            "suggested_bullets": [],
            "section_suggestions": [],
            "summary": "",
            "error": "NO_API_KEY",
        }

    track_label = TRACK_LABELS.get(track_code, track_code)
    missed = [k["keyword"] for k in scored_keywords if k["score"] == 0]
    hit = [k["keyword"] for k in scored_keywords if k["score"] > 0]

    prompt = f"""You are an expert resume coach specialising in the **{track_label}** role.

## Job Description
{jd_text[:3000]}

## Candidate's Existing Resume (for the {track_label} track)
{resume_text[:3000] if resume_text.strip() else "(No resume provided — generate general suggestions based on the JD.)"}

## Keyword Analysis
- Keywords ALREADY in resume / matched: {", ".join(hit) if hit else "None"}
- Keywords MISSING from resume: {", ".join(missed) if missed else "None"}

## Your Task
Respond ONLY with a valid JSON object (no markdown fences, no extra text) with these exact keys:

{{
  "summary": "<2-3 sentence overall assessment>",
  "gap_keywords": ["<keyword1>", "<keyword2>", ...],
  "suggested_bullets": [
    "<bullet 1 — strong action verb, quantified where possible>",
    "<bullet 2>",
    "<bullet 3>",
    "<bullet 4>",
    "<bullet 5>"
  ],
  "section_suggestions": [
    "<e.g. Add a Skills section listing X, Y, Z>",
    "<e.g. In your Summary, mention your experience with A>",
    "<e.g. Rename your Experience heading to highlight B>"
  ]
}}

Rules:
- suggested_bullets must be COPY-PASTE ready for a resume — professional, specific, using strong verbs
- gap_keywords should be the top 5-8 highest-priority keywords missing from the resume
- section_suggestions should be 3-5 actionable structural improvements
- Keep all text concise and professional
"""

    try:
        import warnings
        from google import genai
        from google.genai import types
        warnings.filterwarnings("ignore", category=UserWarning)
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model="models/gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.4),
        )

        raw = response.text.strip()

        # Strip markdown fences if model adds them
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
            if raw.endswith("```"):
                raw = raw.rsplit("```", 1)[0]
        raw = raw.strip()

        data = json.loads(raw)
        data["error"] = None
        return data

    except json.JSONDecodeError as e:
        return {
            "gap_keywords": missed[:8],
            "suggested_bullets": [],
            "section_suggestions": [],
            "summary": "Could not parse AI response. Please try again.",
            "error": f"JSON_PARSE_ERROR: {str(e)}",
        }
    except Exception as e:
        err_str = str(e)
        if "API_KEY_INVALID" in err_str or "API key not valid" in err_str or "INVALID_ARGUMENT" in err_str:
            return {
                "gap_keywords": [],
                "suggested_bullets": [],
                "section_suggestions": [],
                "summary": "",
                "error": "INVALID_API_KEY",
            }
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "Quota exceeded" in err_str:
            return {
                "gap_keywords": missed[:5],
                "suggested_bullets": [],
                "section_suggestions": [],
                "summary": "Gemini Free-Tier rate limit reached (5 requests/min limit). Please wait ~30-45 seconds before trying again.",
                "error": "RATE_LIMIT_EXCEEDED",
            }
        if "503" in err_str or "UNAVAILABLE" in err_str:
            return {
                "gap_keywords": missed[:5],
                "suggested_bullets": [],
                "section_suggestions": [],
                "summary": "Google AI service is currently busy. Please wait a few seconds and try again.",
                "error": "SERVICE_UNAVAILABLE",
            }
        return {
            "gap_keywords": [],
            "suggested_bullets": [],
            "section_suggestions": [],
            "summary": "",
            "error": err_str,
        }


def tailor_full_resume(jd_text: str, resume_text: str, track_code: str, scored_kws: list[dict]) -> dict:
    """
    Uses Gemini 3.6 Flash to rewrite the candidate's entire resume tailored specifically to the JD.
    Returns structured dict with tailored summary, skills, experience, and full markdown text.
    """
    from excel_reader import TRACK_LABELS
    track_label = TRACK_LABELS.get(track_code, track_code)

    api_key = get_api_key()
    if not api_key:
        return {"error": "NO_API_KEY"}

    matched = [k["keyword"] for k in scored_kws if k.get("score", 0) > 0]
    missed = [k["keyword"] for k in scored_kws if k.get("score", 0) == 0]

    has_resume = bool(resume_text.strip())

    if has_resume:
        resume_input = resume_text.strip()[:4000]
        resume_guidance = """STRICT FACT-PRESERVATION MANDATE:
- The candidate HAS provided their actual resume text below.
- YOU MUST PRESERVE the candidate's ACTUAL company names, employer history, job titles, employment dates, university names, and degrees EXACTLY as stated in candidate's original resume.
- ABSOLUTELY NEVER replace the candidate's real company names with the target hiring company name from the JD (e.g. do NOT invent that the candidate worked at the hiring company in the JD unless explicitly stated in candidate's resume).
- ABSOLUTELY NEVER hallucinate or invent fake company names (e.g. Synchrony, UnitedHealth, Acetech), fake universities, or fake employment dates.
- Rephrase and enhance bullet points and summary to highlight relevant JD keywords and achievements while staying 100% faithful to candidate's real work history."""
    else:
        resume_input = "(No candidate resume provided)"
        resume_guidance = """NO RESUME PROVIDED MANDATE:
- The candidate did NOT provide their original resume text.
- Use explicit brackets/placeholders for all personal metadata: e.g., '[Company Name]', '[Employment Dates]', '[University / Degree]', '[City, State / Remote]'.
- ABSOLUTELY NEVER invent real company names (such as the target hiring company in the JD or third-party corporations) or fake university names."""

    prompt = f"""You are an elite executive resume writer, ATS optimization specialist, and strict factual editor.

## Target Role Track
{track_label}

## Job Description (Target Hiring Role)
{jd_text[:3500]}

## Candidate Original Resume / Profile
{resume_input}

## Keyword Signals
Matched Keywords: {", ".join(matched[:12]) if matched else "None"}
Top Missing Gaps: {", ".join(missed[:12]) if missed else "None"}

## CRITICAL INSTRUCTIONS & RULES:
{resume_guidance}

Additional Instructions:
1. Professional Summary: 3-4 sentence impactful executive summary matching the target role title and JD priorities.
2. Core Competencies: Categorized skills incorporating key JD keywords.
3. Experience Bullets: Strong action-oriented bullet points tailored to target role with achievements.
4. Full Markdown Resume: Complete formatted resume ready for review and editing with headers ## PROFESSIONAL SUMMARY, ## CORE COMPETENCIES, ## PROFESSIONAL EXPERIENCE, ## EDUCATION & CERTIFICATIONS.

Respond ONLY with valid JSON (no markdown fences):
{{
  "job_title": "<aligned target job title>",
  "tailored_summary": "<3-4 sentence executive summary>",
  "core_competencies": [
    {{"category": "<Category Name>", "skills": ["<Skill 1>", "<Skill 2>", "<Skill 3>"]}}
  ],
  "experience_highlights": [
    {{"role": "<Role Title>", "company": "<Actual Company from Candidate Resume or [Company Name]>", "bullets": ["<Bullet 1>", "<Bullet 2>", "<Bullet 3>"]}}
  ],
  "full_markdown": "<Complete Full Markdown Resume with headers ## PROFESSIONAL SUMMARY, ## CORE COMPETENCIES, ## PROFESSIONAL EXPERIENCE, ## EDUCATION & CERTIFICATIONS>"
}}"""

    try:
        import warnings, time
        from google import genai
        from google.genai import types
        warnings.filterwarnings("ignore", category=UserWarning)
        client = genai.Client(api_key=api_key)

        response = None
        last_exc = None
        for attempt, wait in enumerate([0, 2, 4]):
            if wait:
                time.sleep(wait)
            try:
                response = client.models.generate_content(
                    model="models/gemini-3.6-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.4),
                )
                break
            except Exception as exc:
                last_exc = exc
                err_str = str(exc)
                if "429" in err_str or "503" in err_str or "UNAVAILABLE" in err_str:
                    if attempt < 2:
                        continue
                raise exc

        if response is None and last_exc is not None:
            raise last_exc

        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
            if raw.endswith("```"):
                raw = raw.rsplit("```", 1)[0]
        raw = raw.strip()

        data = json.loads(raw)
        data["error"] = None
        return data

    except json.JSONDecodeError as e:
        return {"error": f"JSON_PARSE_ERROR: {str(e)}"}
    except Exception as e:
        err_str = str(e)
        if "API_KEY_INVALID" in err_str or "API key not valid" in err_str:
            return {"error": "INVALID_API_KEY"}
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
            return {"error": "RATE_LIMIT_EXCEEDED"}
        if "503" in err_str or "UNAVAILABLE" in err_str:
            return {"error": "SERVICE_UNAVAILABLE"}
        return {"error": err_str}
