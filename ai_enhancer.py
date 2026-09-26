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


MODEL_FALLBACK_CHAIN = [
    "models/gemini-3.6-flash",
    "models/gemini-3.5-flash-lite",
    "models/gemini-3.5-flash",
    "models/gemini-3.7-flash",
    "models/gemini-3.8-flash",
    "models/gemini-flash-latest",
    "models/gemini-flash-lite-latest",
]


def call_gemini_with_fallback(client, prompt: str, temperature: float = 0.4) -> tuple[str, str]:
    """
    Attempts to generate content using a robust multi-model fallback chain of Gemini AI models.
    Tries each model in order, with automatic retry per model on 429/503/RESOURCE_EXHAUSTED errors.
    Returns (raw_text_response, model_name_used).
    """
    import time
    from google.genai import types

    last_error = None

    for model_name in MODEL_FALLBACK_CHAIN:
        for attempt, wait in enumerate([0, 1.5]):
            if wait:
                time.sleep(wait)
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=temperature),
                )
                if response and response.text and response.text.strip():
                    return response.text.strip(), model_name
            except Exception as exc:
                last_error = exc
                err_str = str(exc)
                if "429" in err_str or "503" in err_str or "RESOURCE_EXHAUSTED" in err_str or "UNAVAILABLE" in err_str or "Quota" in err_str:
                    if attempt < 1:
                        continue
                    break  # Try next model in fallback chain
                elif "404" in err_str or "NOT_FOUND" in err_str:
                    break  # Skip non-supported model name immediately

    if last_error:
        raise last_error
    raise RuntimeError("All fallback AI models were exhausted or unavailable.")


def enhance_resume(
    jd_text: str,
    resume_text: str,
    track_code: str,
    scored_keywords: list[dict],
) -> dict:
    """
    Call Gemini to produce gap analysis + resume suggestions.
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
        warnings.filterwarnings("ignore", category=UserWarning)
        client = genai.Client(api_key=api_key)

        raw, model_used = call_gemini_with_fallback(client, prompt, temperature=0.4)

        # Strip markdown fences if model adds them
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
            if raw.endswith("```"):
                raw = raw.rsplit("```", 1)[0]
        raw = raw.strip()

        data = json.loads(raw)
        data["error"] = None
        data["model_used"] = model_used
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


def inject_candidate_details(markdown_text: str, candidate_info: dict = None) -> str:
    """
    Ensures that full markdown resume headers use the candidate's actual name and contact details,
    replacing placeholder brackets such as [First Name] [Last Name], [Email Address], etc.
    """
    if not markdown_text:
        return ""
    if not candidate_info or not isinstance(candidate_info, dict):
        candidate_info = {}

    name = candidate_info.get("name", "").strip() or "Candidate Name"
    location = candidate_info.get("location", "").strip() or "City, State / Remote"
    phone = candidate_info.get("phone", "").strip() or "Phone Number"
    email = candidate_info.get("email", "").strip() or "Email Address"
    linkedin = candidate_info.get("linkedin", "").strip() or "LinkedIn Profile URL"

    header_line = f"# {name}\n{location} | {phone} | {email} | {linkedin}"

    import re
    replacements = [
        (r"#\s*\[First Name\]\s*\[Last Name\]", f"# {name}"),
        (r"#\s*\[Full Name\]", f"# {name}"),
        (r"#\s*\[Candidate Name\]", f"# {name}"),
        (r"#\s*\[Name\]", f"# {name}"),
        (r"\[First Name\]\s*\[Last Name\]", name),
        (r"\[Full Name\]", name),
        (r"\[Candidate Name\]", name),
        (r"\[Your Name\]", name),
        (r"\[City,\s*State\s*/\s*Remote\]", location),
        (r"\[City,\s*State\]", location),
        (r"\[Phone Number\]", phone),
        (r"\[Phone\]", phone),
        (r"\[Email Address\]", email),
        (r"\[Email\]", email),
        (r"\[LinkedIn Profile URL\]", linkedin),
        (r"\[LinkedIn URL\]", linkedin),
        (r"\[LinkedIn\]", linkedin),
    ]

    result = markdown_text
    for pattern, repl in replacements:
        result = re.sub(pattern, repl, result, flags=re.IGNORECASE)

    # If header name is missing or starts with generic # Resume, fix top line
    lines = result.strip().splitlines()
    if lines:
        first_line = lines[0].strip()
        if not first_line.startswith("# ") or "[First Name]" in first_line or "Candidate Name" in first_line:
            # Replace top header or prepend
            if first_line.startswith("# "):
                lines[0] = f"# {name}"
                if len(lines) > 1 and ("|" in lines[1] or "[" in lines[1]):
                    lines[1] = f"{location} | {phone} | {email} | {linkedin}"
                else:
                    lines.insert(1, f"{location} | {phone} | {email} | {linkedin}")
                result = "\n".join(lines)
            else:
                result = f"{header_line}\n\n" + result

    return result


def tailor_full_resume(jd_text: str, resume_text: str, track_code: str, scored_kws: list[dict], candidate_info: dict = None) -> dict:
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

    cand_name = candidate_info.get('name', '').strip() if candidate_info else ''
    cand_loc = candidate_info.get('location', '').strip() if candidate_info else ''
    cand_phone = candidate_info.get('phone', '').strip() if candidate_info else ''
    cand_email = candidate_info.get('email', '').strip() if candidate_info else ''
    cand_li = candidate_info.get('linkedin', '').strip() if candidate_info else ''

    cand_contact_block = f"""CANDIDATE CONTACT DETAILS TO USE IN RESUME HEADER:
- Name: {cand_name or '[Candidate Name]'}
- Location: {cand_loc or '[City, State / Remote]'}
- Phone: {cand_phone or '[Phone Number]'}
- Email: {cand_email or '[Email Address]'}
- LinkedIn: {cand_li or '[LinkedIn Profile URL]'}

HEADER FORMAT REQUIREMENT:
You MUST start the full_markdown output with:
# {cand_name or '[Candidate Name]'}
{cand_loc or '[City, State / Remote]'} | {cand_phone or '[Phone Number]'} | {cand_email or '[Email Address]'} | {cand_li or '[LinkedIn Profile URL]'}
"""

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
- Use candidate's specified contact details in header.
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

{cand_contact_block}

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
  "full_markdown": "<Complete Full Markdown Resume starting with # {cand_name or '[Candidate Name]'} and headers ## PROFESSIONAL SUMMARY, ## CORE COMPETENCIES, ## PROFESSIONAL EXPERIENCE, ## EDUCATION & CERTIFICATIONS>"
}}"""

    try:
        import warnings
        from google import genai
        warnings.filterwarnings("ignore", category=UserWarning)
        client = genai.Client(api_key=api_key)

        raw, model_used = call_gemini_with_fallback(client, prompt, temperature=0.4)

        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
            if raw.endswith("```"):
                raw = raw.rsplit("```", 1)[0]
        raw = raw.strip()

        data = json.loads(raw)
        data["error"] = None
        data["model_used"] = model_used

        if "full_markdown" in data and data["full_markdown"]:
            data["full_markdown"] = inject_candidate_details(data["full_markdown"], candidate_info)

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


def generate_interview_prep(jd_text: str, resume_text: str, track_code: str, scored_kws: list[dict]) -> dict:
    """
    Generates top 10 JD & role specific interview questions with STAR method answer guides.
    """
    api_key = get_api_key()
    if not api_key:
        return {"error": "NO_API_KEY"}

    from excel_reader import TRACK_LABELS
    track_label = TRACK_LABELS.get(track_code, track_code)
    matched = [k["keyword"] for k in scored_kws if k.get("score", 0) > 0]
    missed = [k["keyword"] for k in scored_kws if k.get("score", 0) == 0]

    resume_input = resume_text.strip()[:3500] if resume_text.strip() else "(No candidate resume provided - ground answers in candidate background placeholders)"

    prompt = f"""You are an executive interviewer and interview coach for the **{track_label}** role.

## Job Description
{jd_text[:3000]}

## Candidate Resume / Background
{resume_input}

## Key Skill Signals
Matched Skills: {", ".join(matched[:10]) if matched else "None"}
Gap Skills: {", ".join(missed[:10]) if missed else "None"}

## Task
Generate a structured JSON object containing 10 high-impact interview questions with tailored STAR method answers.

Categories:
1. Behavioral & Leadership (3 questions)
2. Technical & Methodology (4 questions)
3. Problem-Solving & Scenarios (3 questions)

Respond ONLY with valid JSON (no markdown fences):
{{
  "questions": [
    {{
      "category": "Behavioral / Technical / Scenario",
      "question": "<Specific, highly relevant interview question>",
      "why_asked": "<Brief explanation of what interviewers evaluate>",
      "star_answer": {{
        "situation": "<Situation description incorporating JD context>",
        "task": "<Task / challenge faced>",
        "action": "<Action taken incorporating candidate resume skills & keywords>",
        "result": "<Quantified impact & business outcome>"
      }}
    }}
  ]
}}"""

    try:
        import warnings
        from google import genai
        warnings.filterwarnings("ignore", category=UserWarning)
        client = genai.Client(api_key=api_key)

        raw, model_used = call_gemini_with_fallback(client, prompt, temperature=0.4)

        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
            if raw.endswith("```"):
                raw = raw.rsplit("```", 1)[0]
        raw = raw.strip()

        data = json.loads(raw)
        data["error"] = None
        data["model_used"] = model_used
        return data
    except Exception as e:
        err_str = str(e)
        if "API_KEY_INVALID" in err_str or "API key not valid" in err_str:
            return {"error": "INVALID_API_KEY"}
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "Quota exceeded" in err_str:
            return {"error": "RATE_LIMIT_EXCEEDED"}
        if "503" in err_str or "UNAVAILABLE" in err_str:
            return {"error": "SERVICE_UNAVAILABLE"}
        return {"error": err_str}


def generate_cover_letter(jd_text: str, resume_text: str, track_code: str, candidate_info: dict = None) -> dict:
    """
    Generates a tailored 3-paragraph executive cover letter.
    """
    api_key = get_api_key()
    if not api_key:
        return {"error": "NO_API_KEY"}

    from excel_reader import TRACK_LABELS
    track_label = TRACK_LABELS.get(track_code, track_code)
    resume_input = resume_text.strip()[:3500] if resume_text.strip() else "(No candidate resume provided)"

    cand_name = candidate_info.get('name', '').strip() if candidate_info else ''

    prompt = f"""You are an executive career strategist.

## Target Role
{track_label}

## Job Description
{jd_text[:3000]}

## Candidate Resume / Profile
{resume_input}

## Candidate Name
{cand_name or '[Your Name]'}

## Task
Generate a highly persuasive, 3-paragraph executive cover letter connecting candidate achievements directly to the job description requirements.

Strict Rule: Preserve candidate's real company names if provided; sign off with Sincerely, {cand_name or '[Your Name]'}.

Respond ONLY with valid JSON:
{{
  "job_title": "<target job title>",
  "cover_letter_markdown": "<Formatted 3-paragraph cover letter starting with Dear Hiring Manager, ... ending with Sincerely,\\n\\n{cand_name or '[Your Name]'}>"
}}"""

    try:
        import warnings
        from google import genai
        warnings.filterwarnings("ignore", category=UserWarning)
        client = genai.Client(api_key=api_key)

        raw, model_used = call_gemini_with_fallback(client, prompt, temperature=0.4)

        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
            if raw.endswith("```"):
                raw = raw.rsplit("```", 1)[0]
        raw = raw.strip()

        data = json.loads(raw)
        data["error"] = None
        data["model_used"] = model_used

        if "cover_letter_markdown" in data and data["cover_letter_markdown"]:
            data["cover_letter_markdown"] = inject_candidate_details(data["cover_letter_markdown"], candidate_info)

        return data
    except Exception as e:
        err_str = str(e)
        if "API_KEY_INVALID" in err_str or "API key not valid" in err_str:
            return {"error": "INVALID_API_KEY"}
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "Quota exceeded" in err_str:
            return {"error": "RATE_LIMIT_EXCEEDED"}
        if "503" in err_str or "UNAVAILABLE" in err_str:
            return {"error": "SERVICE_UNAVAILABLE"}
        return {"error": err_str}


def audit_ats_readiness(jd_text: str, resume_text: str, track_code: str, scored_kws: list[dict]) -> dict:
    """
    Audits candidate resume against ATS scannability gatekeeper standards.
    """
    import re
    matched = [k["keyword"] for k in scored_kws if k.get("score", 0) > 0]
    missed = [k["keyword"] for k in scored_kws if k.get("score", 0) == 0]
    total_kws = len(scored_kws)

    keyword_coverage_pct = round((len(matched) / total_kws * 100)) if total_kws else 0

    has_resume = bool(resume_text.strip())
    text_lower = resume_text.lower() if has_resume else ""

    headers_check = sum(1 for h in ["summary", "experience", "education", "skills"] if h in text_lower)
    has_metrics = len(re.findall(r"\b\d+%\b|\$\d+|\b\d+\s*years?\b|\b\d+\+\b", text_lower)) > 2 if has_resume else False
    has_power_verbs = len(re.findall(r"\b(led|managed|spearheaded|architected|engineered|delivered|directed|built|drove|implemented|instituted)\b", text_lower)) > 3 if has_resume else False

    score = 0
    score += min(45, keyword_coverage_pct * 0.45)
    score += 20 if headers_check >= 3 else 10
    score += 20 if has_metrics else 5
    score += 15 if has_power_verbs else 5

    final_score = min(100, round(score))
    status = "Strong ATS Scannability" if final_score >= 80 else "Moderate Scannability Risk" if final_score >= 60 else "High ATS Gatekeeper Risk"

    fix_checklist = []
    if keyword_coverage_pct >= 60:
        fix_checklist.append({
            "type": "pass",
            "check": "Keyword Density",
            "tip": f"Strong keyword coverage ({keyword_coverage_pct}% matched).",
            "resolution": "Your resume already includes a healthy density of core track keywords."
        })
    else:
        top_missed_str = ", ".join(missed[:5])
        fix_checklist.append({
            "type": "fail",
            "check": "Keyword Density",
            "tip": f"Incorporate missing core keywords: {top_missed_str}",
            "resolution": f"Add a 'Core Competencies' section or copy/paste this tailored bullet into your experience:\n\"• Spearheaded {top_missed_str} across enterprise initiatives, delivering high-impact business outcomes.\""
        })

    if headers_check >= 3:
        fix_checklist.append({
            "type": "pass",
            "check": "Standard Headings",
            "tip": "Standard ATS section headings detected.",
            "resolution": "Your resume uses standard ATS-parseable section headers."
        })
    else:
        fix_checklist.append({
            "type": "fail",
            "check": "Standard Headings",
            "tip": "Use standard ATS section headings.",
            "resolution": "Rename any non-standard headers (e.g. 'About Me', 'Background') to standard ATS titles:\n• ## PROFESSIONAL SUMMARY\n• ## CORE COMPETENCIES\n• ## PROFESSIONAL EXPERIENCE\n• ## EDUCATION & CERTIFICATIONS"
        })

    if has_metrics:
        fix_checklist.append({
            "type": "pass",
            "check": "Quantified Impact",
            "tip": "Quantified metrics (% / $ / scale) found in bullets.",
            "resolution": "Good use of quantitative data in your bullet points."
        })
    else:
        fix_checklist.append({
            "type": "warn",
            "check": "Quantified Impact",
            "tip": "Quantify achievements in bullets with % improvements, team sizes, and budget metrics.",
            "resolution": "Transform passive bullets into measured outcomes:\n• Before: 'Responsible for managing project delivery.'\n• Recommended Fix: '• Managed end-to-end delivery of 8+ simultaneous enterprise projects, improving on-time release rate by 35% across a $2.5M budget.'"
        })

    if has_power_verbs:
        fix_checklist.append({
            "type": "pass",
            "check": "Power Action Verbs",
            "tip": "Bullet points begin with strong action verbs.",
            "resolution": "Strong active verbs used throughout bullet points."
        })
    else:
        fix_checklist.append({
            "type": "warn",
            "check": "Power Action Verbs",
            "tip": "Begin bullet points with strong action verbs (e.g. Spearheaded, Engineered, Directed, Delivered).",
            "resolution": "Replace weak verbs like 'Helped', 'Worked on', or 'Responsible for' with active verbs:\n• Recommended Action Verbs: Spearheaded, Architected, Engineered, Orchestrated, Instituted, Delivered.\n• Example Fix: '• Spearheaded cross-functional technical alignment, accelerating project milestones by 25%.'"
        })

    return {
        "score": final_score,
        "status": status,
        "keyword_coverage_pct": keyword_coverage_pct,
        "matched_count": len(matched),
        "total_keywords": total_kws,
        "has_metrics": has_metrics,
        "has_power_verbs": has_power_verbs,
        "fix_checklist": fix_checklist
    }

