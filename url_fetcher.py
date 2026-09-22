"""
url_fetcher.py
Fetches and extracts readable text from a job posting URL.
"""
import re
import requests
from bs4 import BeautifulSoup

# Common noise selectors to strip
_NOISE_TAGS = ["script", "style", "nav", "header", "footer",
               "aside", "noscript", "iframe", "svg"]

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

BLOCKED_DOMAINS = [
    "linkedin.com",
    "linkedin.",
    "indeed.com",
    "glassdoor.com",
    "glassdoor.",
    "monster.com",
    "naukri.com",
    "ziprecruiter.com",
    "dice.com",
]

# Domains that commonly return 403 but may still work — give friendly message on failure
JOB_BOARD_NAMES = {
    "indeed.com": "Indeed",
    "glassdoor.com": "Glassdoor",
    "monster.com": "Monster",
    "naukri.com": "Naukri",
    "ziprecruiter.com": "ZipRecruiter",
    "dice.com": "Dice",
    "linkedin.com": "LinkedIn",
}

COPY_PASTE_INSTRUCTIONS = (
    "This job board blocks automated access. "
    "To get the JD text:\n"
    "1. Open the job posting in your browser\n"
    "2. Press Ctrl+A to select all, then Ctrl+C to copy\n"
    "3. Switch to 'Paste JD' tab and paste it there"
)


def fetch_jd_from_url(url: str, timeout: int = 12) -> dict:
    """
    Fetch a job posting URL and return extracted text.
    Returns: {text: str, warning: str|None, title: str}
    """
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    url_lower = url.lower()

    # Check for known blocked domains upfront
    for blocked in BLOCKED_DOMAINS:
        if blocked in url_lower:
            board_name = next((v for k, v in JOB_BOARD_NAMES.items() if k in url_lower), "This site")
            return {
                "text": "",
                "title": "",
                "warning": f"{board_name} blocks automated access.\n"
                           "To get the JD text:\n"
                           "1. Open the job posting in your browser\n"
                           "2. Select all text (Ctrl+A) → Copy (Ctrl+C)\n"
                           "3. Switch to the 'Paste JD' tab and paste it there",
            }

    try:
        resp = requests.get(url, headers=_HEADERS, timeout=timeout)
        resp.raise_for_status()
    except requests.exceptions.Timeout:
        return {"text": "", "title": "", "warning": "⏱ Request timed out. The site took too long to respond."}
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code
        if status == 403:
            # Identify if it's a known job board even if not pre-listed
            board_name = next((v for k, v in JOB_BOARD_NAMES.items() if k in url_lower), "This site")
            return {
                "text": "", "title": "",
                "warning": f"{board_name} blocks automated access (403 Forbidden).\n"
                           "To get the JD text:\n"
                           "1. Open the job posting in your browser\n"
                           "2. Select all text (Ctrl+A) → Copy (Ctrl+C)\n"
                           "3. Switch to the 'Paste JD' tab and paste it there",
            }
        if status == 404:
            return {"text": "", "title": "", "warning": "⚠ Page not found (404). Check the URL and try again."}
        return {"text": "", "title": "", "warning": f"⚠ Could not fetch the page (HTTP {status})."}
    except requests.exceptions.RequestException as e:
        return {"text": "", "title": "", "warning": f"⚠ Could not fetch URL: {str(e)}"}

    soup = BeautifulSoup(resp.text, "html.parser")

    # Get page title
    title = soup.title.string.strip() if soup.title and soup.title.string else ""

    # Remove noisy tags
    for tag in _NOISE_TAGS:
        for el in soup.find_all(tag):
            el.decompose()

    # Try to find main content area
    main_content = (
        soup.find("main")
        or soup.find(attrs={"role": "main"})
        or soup.find("article")
        or soup.find(id=re.compile(r"job|description|content|details", re.I))
        or soup.find(class_=re.compile(r"job|description|content|details", re.I))
        or soup.body
    )

    raw_text = main_content.get_text(separator="\n") if main_content else soup.get_text(separator="\n")

    # Clean up whitespace
    lines = [line.strip() for line in raw_text.splitlines()]
    lines = [l for l in lines if l]
    text = "\n".join(lines)

    # Trim extremely long extracts
    if len(text) > 8000:
        text = text[:8000] + "\n\n[... text truncated to 8000 chars ...]"

    if not text:
        return {"text": "", "title": title, "warning": "Could not extract text from this page. Please paste the JD manually."}

    return {"text": text, "title": title, "warning": None}
