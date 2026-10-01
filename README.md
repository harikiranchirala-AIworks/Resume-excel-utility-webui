# 🚀 OfferCraft AI — Executive Resume & Career Matching Suite

An automated **Job Description (JD) to Resume Matching & AI Enhancement Utility** built with Flask, Chart.js, and Google Gemini 3.6 Flash. 

It scores job descriptions against keyword banks across 4 professional management tracks and uses AI to generate tailored resume bullets, missing keyword analyses, and track recommendations.

---

## 🌟 Key Features

- **📊 4 Professional Tracks**:
  - 🤖 **AI Transformation Manager**
  - 📊 **Technical Program Manager (TPM)**
  - 💻 **IT Delivery Manager (ITDM)**
  - 📦 **Product Manager (PM)**

- **🔗 Flexible JD Input**:
  - Paste raw Job Description text
  - Fetch directly from public job URLs (Indeed, Glassdoor, company careers pages) with intelligent 403/blocking fallback guidance

- **📄 Per-Track Resume Support**:
  - Paste text or upload `.txt`, `.pdf`, or `.docx` resume files for each track

- **📈 Visual Score Analytics**:
  - Toggleable **Radar Chart** & **Horizontal Bar Chart** (Chart.js) comparing match percentages across all 4 tracks

- **🎯 Instant & AI Best-Track Picker**:
  - Automatic top-track recommendation based on keyword match score
  - **"Ask AI Why"**: Deep LLM analysis explaining why a track fits best, highlighting key JD signals, runner-up comparison, and alignment tips

- **✨ Single-Track & One-Click Full Analysis**:
  - AI-driven resume enhancement using **Gemini 3.6 Flash**
  - Generates top missing gap keywords, tailored copy-paste resume bullets, and structural section suggestions
  - **"Full Analysis"**: Scores and AI-enhances all 4 tracks concurrently via parallel threads (`ThreadPoolExecutor`) with automatic retry/backoff rate-limiting protection

---

## 🛠️ Project Architecture

```
Resume-excel-utility-webui/
├── app.py                      # Flask Application Server (/score, /enhance, /enhance_all, /pick_track, /fetch_jd, /upload_resume)
├── excel_reader.py             # Parses Excel sheets (KEYWORDS, scoring sheets, bullets)
├── scorer.py                   # JD keyword matching engine & scoring logic
├── supplementary_keywords.py   # Expanded internet-researched keyword bank (149+ keywords & synonyms)
├── ai_enhancer.py              # Google Gemini 3.6 Flash API integration & prompt builder
├── url_fetcher.py              # Web scraper for fetching JDs from URLs with HTML sanitization
├── resume_parser.py            # Multi-format resume parser (.txt, .pdf via pdfplumber, .docx via python-docx)
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
├── templates/
│   └── index.html              # Main single-page web interface
└── static/
    ├── style.css               # Modern dark-themed CSS styling
    └── main.js                 # Frontend interactions, async API calls, Chart.js rendering
```

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/harikiranchirala-AIworks/Resume-excel-utility-webui.git
cd Resume-excel-utility-webui
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Gemini API Key
Get a free API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

Create a `.env` file in the project root:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 4. Run the Application
```bash
python app.py
```

Open your browser and navigate to **[http://127.0.0.1:5000](http://127.0.0.1:5000)**.

---

## 📜 License

MIT License. Free for personal and professional use.
