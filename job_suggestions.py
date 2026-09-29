"""
job_suggestions.py
Defines target job titles per track, domain favorability rules, and job search link generators.
"""

import urllib.parse
import re

# Target Job Titles & Domains configuration matching user specifications
TRACK_TARGET_ROLES = {
    "ITDM": {
        "track_name": "Service Delivery (ITDM)",
        "titles": [
            "Service Delivery Manager",
            "Application Support Manager",
            "Salesforce Platform/Service Owner",
            "IT Delivery Manager",
            "Release/Change Manager",
            "Production Support Lead"
        ],
        "target_sectors": ["GCCs", "Salesforce partners", "Telecom / Pharma IT ops"],
        "icon": "💻"
    },
    "TPM": {
        "track_name": "Digital Transformation TPM",
        "titles": [
            "Sr. Technical Program Manager",
            "Digital Transformation Manager",
            "Program/Delivery Manager (projects)",
            "Salesforce Program Manager",
            "CRM Transformation Lead"
        ],
        "target_sectors": ["Enterprise Digital Transformation", "Cloud Migration", "Salesforce Ecosystem"],
        "icon": "📊"
    },
    "AI": {
        "track_name": "AI Delivery",
        "titles": [
            "AI Delivery Manager",
            "AI Program Manager",
            "AI Transformation Lead",
            "Responsible AI PM",
            "GenAI Adoption Lead"
        ],
        "target_sectors": ["Enterprise AI CoE", "GenAI & LLM Programs", "AI Governance"],
        "icon": "🤖"
    },
    "PM": {
        "track_name": "Product Management",
        "titles": [
            "Product Manager",
            "Senior Product Manager",
            "Technical Product Manager",
            "Enterprise Product Lead",
            "CRM Product Owner"
        ],
        "target_sectors": ["Enterprise SaaS", "B2B Platforms", "CRM Products"],
        "icon": "📦"
    }
}

# Domain Favorability Configuration
DOMAIN_RULES = {
    "SUITABLE": {
        "label": "🌟 Suitable / Highly Favorable",
        "domains": ["Telecom", "Pharma", "Bio-Tech", "GCCs", "Salesforce Partners"],
        "keywords": ["telecom", "telecommunication", "pharma", "pharmaceutical", "biotech", "bio-tech", "gcc", "global capability center", "salesforce partner", "sf partner"],
        "badge_class": "favor-high"
    },
    "MEDIUM": {
        "label": "🟡 Medium Favorable",
        "domains": ["Transportation", "Media", "Travel"],
        "keywords": ["transportation", "transport", "logistics", "media", "broadcasting", "entertainment", "travel", "hospitality", "airline"],
        "badge_class": "favor-med"
    },
    "LESS_SUITABLE": {
        "label": "🔴 Less Suitable / Watchout",
        "domains": ["BFSI", "Banking", "Finance"],
        "keywords": ["bfsi", "banking", "finance", "financial services", "investment banking", "fintech", "capital markets", "wealth management"],
        "badge_class": "favor-low"
    }
}


def build_job_search_urls(title: str, location: str = "") -> dict:
    """Generates 1-click search URLs for LinkedIn, Google Jobs, and Indeed."""
    query = f'"{title}"'
    if location:
        query += f' {location}'

    q_encoded = urllib.parse.quote(query)
    title_encoded = urllib.parse.quote(title)

    return {
        "linkedin": f"https://www.linkedin.com/jobs/search/?keywords={q_encoded}",
        "google": f"https://www.google.com/search?q={title_encoded}+jobs",
        "indeed": f"https://www.indeed.com/jobs?q={title_encoded}"
    }


def analyze_domain_suitability(jd_text: str) -> dict:
    """
    Analyzes JD text to classify domain favorability:
    Suitable (Telecom, Pharma, Bio-Tech, GCCs, Salesforce Partners)
    Medium (Transportation, Media, Travel)
    Less Suitable (BFSI, Banking, Finance)
    """
    text_lower = jd_text.lower()
    
    matched_suitable = []
    matched_medium = []
    matched_less = []

    for kw in DOMAIN_RULES["SUITABLE"]["keywords"]:
        if kw in text_lower:
            matched_suitable.append(kw.title())

    for kw in DOMAIN_RULES["MEDIUM"]["keywords"]:
        if kw in text_lower:
            matched_medium.append(kw.title())

    for kw in DOMAIN_RULES["LESS_SUITABLE"]["keywords"]:
        if kw in text_lower:
            matched_less.append(kw.title())

    if matched_suitable:
        tier = "SUITABLE"
        summary = f"🌟 Highly Suitable Domain ({', '.join(set(matched_suitable))})"
        badge_class = "favor-high"
    elif matched_medium:
        tier = "MEDIUM"
        summary = f"🟡 Medium Favorable Domain ({', '.join(set(matched_medium))})"
        badge_class = "favor-med"
    elif matched_less:
        tier = "LESS_SUITABLE"
        summary = f"🔴 Less Suitable Domain ({', '.join(set(matched_less))})"
        badge_class = "favor-low"
    else:
        tier = "NEUTRAL"
        summary = "ℹ️ General / Tech Domain"
        badge_class = "favor-neutral"

    return {
        "tier": tier,
        "summary": summary,
        "badge_class": badge_class,
        "matched_suitable": list(set(matched_suitable)),
        "matched_medium": list(set(matched_medium)),
        "matched_less": list(set(matched_less)),
        "domain_rules": DOMAIN_RULES
    }
