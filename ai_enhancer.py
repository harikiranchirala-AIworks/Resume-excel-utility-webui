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
