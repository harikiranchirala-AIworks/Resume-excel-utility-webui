"""
supplementary_keywords.py
Extra keyword bank from internet research on 2024-2025 job postings.
Merged with the Excel KEYWORDS sheet at startup (no Excel edits needed).

Tier -> weight: HIGH=3, MEDIUM=2, LOW=1
track: AI | TPM | ITDM | PM | ALL
"""

SUPPLEMENTARY_KEYWORDS = [

    # ── AI TRACK ─────────────────────────────────────────────
    {"keyword":"Generative AI",          "synonyms":["GenAI","Gen AI","generative artificial intelligence"],          "tier":"HIGH",   "track":"AI"},
    {"keyword":"Large Language Model",   "synonyms":["LLM","LLMs","foundation model","language model"],              "tier":"HIGH",   "track":"AI"},
    {"keyword":"AI Strategy",            "synonyms":["AI roadmap","artificial intelligence strategy","AI vision"],    "tier":"HIGH",   "track":"AI"},
    {"keyword":"AI Transformation",      "synonyms":["AI-led transformation","enterprise AI transformation"],          "tier":"HIGH",   "track":"AI"},
    {"keyword":"AI Governance",          "synonyms":["AI policy","responsible AI governance","AI risk management"],   "tier":"HIGH",   "track":"AI"},
    {"keyword":"Responsible AI",         "synonyms":["ethical AI","trustworthy AI","AI ethics","AI fairness"],        "tier":"HIGH",   "track":"AI"},
    {"keyword":"AI Adoption",            "synonyms":["AI rollout","AI deployment","AI enablement","AI scaling"],      "tier":"HIGH",   "track":"AI"},
    {"keyword":"AI Center of Excellence","synonyms":["AI CoE","Centre of Excellence AI","AI hub"],                    "tier":"HIGH",   "track":"AI"},
    {"keyword":"MLOps",                  "synonyms":["ML operations","machine learning operations","model ops"],       "tier":"HIGH",   "track":"AI"},
    {"keyword":"Prompt Engineering",     "synonyms":["prompt design","prompt optimisation","prompt tuning"],           "tier":"HIGH",   "track":"AI"},
    {"keyword":"RAG",                    "synonyms":["retrieval augmented generation","retrieval-augmented generation"],"tier":"MEDIUM","track":"AI"},
    {"keyword":"AI Use Cases",           "synonyms":["AI applications","AI pilots","AI proof of concept","AI PoC"],   "tier":"MEDIUM", "track":"AI"},
    {"keyword":"Azure OpenAI",           "synonyms":["Azure AI","Microsoft AI","OpenAI on Azure"],                    "tier":"MEDIUM", "track":"AI"},
    {"keyword":"Vertex AI",              "synonyms":["Google AI","Google Cloud AI","GCP AI","Gemini API"],            "tier":"MEDIUM", "track":"AI"},
    {"keyword":"AWS AI",                 "synonyms":["Amazon Bedrock","SageMaker","AWS machine learning"],            "tier":"MEDIUM", "track":"AI"},
    {"keyword":"AI ROI",                 "synonyms":["AI business value","AI return on investment","AI benefits"],    "tier":"MEDIUM", "track":"AI"},
    {"keyword":"AI Change Management",   "synonyms":["AI people change","AI culture change","AI upskilling"],         "tier":"MEDIUM", "track":"AI"},
    {"keyword":"Data Strategy",          "synonyms":["data roadmap","data governance strategy","data architecture"],  "tier":"MEDIUM", "track":"AI"},
    {"keyword":"Copilot",                "synonyms":["Microsoft Copilot","GitHub Copilot","AI copilot","Copilot 365"],"tier":"MEDIUM","track":"AI"},
    {"keyword":"NLP",                    "synonyms":["natural language processing","text analytics","conversational AI"],"tier":"MEDIUM","track":"AI"},
    {"keyword":"Agentic AI",             "synonyms":["AI agents","autonomous agents","agentic workflows"],             "tier":"MEDIUM", "track":"AI"},
    {"keyword":"AI Operating Model",     "synonyms":["AI delivery model","AI operating framework"],                   "tier":"MEDIUM", "track":"AI"},
    {"keyword":"Multimodal AI",          "synonyms":["multimodal models","vision-language models"],                   "tier":"LOW",    "track":"AI"},
    {"keyword":"Fine-tuning",            "synonyms":["model fine-tuning","RLHF","instruction tuning"],                "tier":"LOW",    "track":"AI"},
    {"keyword":"Vector Database",        "synonyms":["Pinecone","Weaviate","ChromaDB","embedding store"],             "tier":"LOW",    "track":"AI"},
    {"keyword":"AI Safety",              "synonyms":["model safety","AI red teaming","adversarial testing"],          "tier":"LOW",    "track":"AI"},
    {"keyword":"Synthetic Data",         "synonyms":["data augmentation","AI-generated data"],                        "tier":"LOW",    "track":"AI"},

    # ── TPM TRACK ─────────────────────────────────────────────
    {"keyword":"Program Management",     "synonyms":["programme management","technical programme management"],         "tier":"HIGH",   "track":"TPM"},
    {"keyword":"Agile",                  "synonyms":["agile methodology","agile delivery","agile framework"],          "tier":"HIGH",   "track":"TPM"},
    {"keyword":"SAFe",                   "synonyms":["scaled agile framework","safe agile","release train"],           "tier":"HIGH",   "track":"TPM"},
    {"keyword":"Cross-functional",       "synonyms":["cross functional","multi-team","cross-team coordination"],       "tier":"HIGH",   "track":"TPM"},
    {"keyword":"OKRs",                   "synonyms":["objectives and key results","OKR framework"],                   "tier":"HIGH",   "track":"TPM"},
    {"keyword":"Dependency Management",  "synonyms":["dependency tracking","inter-team dependencies","blockers"],      "tier":"HIGH",   "track":"TPM"},
    {"keyword":"Release Management",     "synonyms":["release planning","release engineering","release cadence"],      "tier":"HIGH",   "track":"TPM"},
    {"keyword":"Risk Mitigation",        "synonyms":["risk management","risk register","issue management"],            "tier":"HIGH",   "track":"TPM"},
    {"keyword":"Technical Delivery",     "synonyms":["engineering delivery","software delivery","platform delivery"],  "tier":"HIGH",   "track":"TPM"},
    {"keyword":"JIRA",                   "synonyms":["Jira Software","Atlassian Jira","issue tracking","Confluence"],  "tier":"MEDIUM", "track":"TPM"},
    {"keyword":"Scrum",                  "synonyms":["scrum master","sprint planning","sprint review","retrospective"],"tier":"MEDIUM", "track":"TPM"},
    {"keyword":"Kanban",                 "synonyms":["kanban board","flow management","WIP limits"],                   "tier":"MEDIUM", "track":"TPM"},
    {"keyword":"DevOps",                 "synonyms":["CI/CD","continuous integration","continuous delivery"],          "tier":"MEDIUM", "track":"TPM"},
    {"keyword":"API Integration",        "synonyms":["API management","REST API","microservices integration"],         "tier":"MEDIUM", "track":"TPM"},
    {"keyword":"Cloud Migration",        "synonyms":["cloud transformation","cloud adoption","lift and shift"],        "tier":"MEDIUM", "track":"TPM"},
    {"keyword":"Stakeholder Management", "synonyms":["stakeholder engagement","executive communication","C-suite"],    "tier":"MEDIUM", "track":"TPM"},
    {"keyword":"Technical Roadmap",      "synonyms":["engineering roadmap","platform roadmap","product roadmap"],      "tier":"MEDIUM", "track":"TPM"},
    {"keyword":"Portfolio Management",   "synonyms":["programme portfolio","project portfolio","PPM"],                 "tier":"MEDIUM", "track":"TPM"},
    {"keyword":"SLA",                    "synonyms":["service level agreement","SLO","service level objective"],       "tier":"MEDIUM", "track":"TPM"},
    {"keyword":"KPI",                    "synonyms":["key performance indicator","metrics","delivery metrics"],        "tier":"MEDIUM", "track":"TPM"},
    {"keyword":"Microservices",          "synonyms":["service-oriented architecture","SOA","distributed systems"],     "tier":"LOW",    "track":"TPM"},
    {"keyword":"Platform Engineering",   "synonyms":["developer platform","internal developer platform","IDP"],        "tier":"LOW",    "track":"TPM"},
    {"keyword":"Incident Response",      "synonyms":["incident management","on-call","post-mortem"],                   "tier":"LOW",    "track":"TPM"},

    # ── ITDM TRACK ────────────────────────────────────────────
    {"keyword":"ITIL",                   "synonyms":["ITIL 4","ITIL framework","ITIL v3","ITIL certification"],        "tier":"HIGH",   "track":"ITDM"},
    {"keyword":"ITSM",                   "synonyms":["IT service management","ServiceNow","IT service delivery"],      "tier":"HIGH",   "track":"ITDM"},
    {"keyword":"Service Delivery",       "synonyms":["IT service delivery","managed services","service operations"],   "tier":"HIGH",   "track":"ITDM"},
    {"keyword":"Vendor Management",      "synonyms":["supplier management","third party management","MSP management"], "tier":"HIGH",   "track":"ITDM"},
    {"keyword":"IT Governance",          "synonyms":["governance framework","IT controls","technology governance"],     "tier":"HIGH",   "track":"ITDM"},
    {"keyword":"Incident Management",    "synonyms":["incident resolution","P1 incident","major incident management"], "tier":"HIGH",   "track":"ITDM"},
    {"keyword":"Change Management",      "synonyms":["change advisory board","CAB","change control","change requests"],"tier":"HIGH",   "track":"ITDM"},
    {"keyword":"IT Budget",              "synonyms":["budget management","cost management","IT cost optimisation"],     "tier":"HIGH",   "track":"ITDM"},
    {"keyword":"COBIT",                  "synonyms":["COBIT 2019","COBIT 5","governance framework"],                   "tier":"MEDIUM", "track":"ITDM"},
    {"keyword":"Problem Management",     "synonyms":["root cause analysis","RCA","problem resolution"],                "tier":"MEDIUM", "track":"ITDM"},
    {"keyword":"ServiceNow",             "synonyms":["ServiceNow ITSM","snow platform","SNOW"],                        "tier":"MEDIUM", "track":"ITDM"},
    {"keyword":"Infrastructure Management","synonyms":["IT infrastructure","data centre","network management"],        "tier":"MEDIUM", "track":"ITDM"},
    {"keyword":"Outsourcing",            "synonyms":["IT outsourcing","offshore delivery","nearshore","ITO"],          "tier":"MEDIUM", "track":"ITDM"},
    {"keyword":"Capacity Planning",      "synonyms":["resource planning","capacity management","demand management"],   "tier":"MEDIUM", "track":"ITDM"},
    {"keyword":"Cloud Operations",       "synonyms":["cloud management","cloud governance","FinOps","cloud cost"],     "tier":"MEDIUM", "track":"ITDM"},
    {"keyword":"Disaster Recovery",      "synonyms":["DR","business continuity","BCM","BCP"],                         "tier":"MEDIUM", "track":"ITDM"},
    {"keyword":"Compliance",             "synonyms":["regulatory compliance","ISO 27001","SOC 2","audit"],             "tier":"MEDIUM", "track":"ITDM"},
    {"keyword":"Service Level Management","synonyms":["SLA management","OLA","underpinning contract"],                "tier":"MEDIUM", "track":"ITDM"},
    {"keyword":"CMDB",                   "synonyms":["configuration management database","asset management"],          "tier":"LOW",    "track":"ITDM"},
    {"keyword":"Prince2",                "synonyms":["PRINCE2 practitioner","PRINCE2 certification"],                  "tier":"LOW",    "track":"ITDM"},
    {"keyword":"Automation",             "synonyms":["process automation","RPA","runbook automation"],                 "tier":"LOW",    "track":"ITDM"},

    # ── PM TRACK ──────────────────────────────────────────────
    {"keyword":"Product Roadmap",        "synonyms":["product strategy","product vision","product plan"],              "tier":"HIGH",   "track":"PM"},
    {"keyword":"Product-Market Fit",     "synonyms":["PMF","market fit","customer problem-solution fit"],              "tier":"HIGH",   "track":"PM"},
    {"keyword":"Go-to-Market",           "synonyms":["GTM strategy","launch strategy","market entry"],                 "tier":"HIGH",   "track":"PM"},
    {"keyword":"User Stories",           "synonyms":["user requirements","epics","acceptance criteria","backlog"],     "tier":"HIGH",   "track":"PM"},
    {"keyword":"Customer Discovery",     "synonyms":["user research","customer interviews","design thinking"],         "tier":"HIGH",   "track":"PM"},
    {"keyword":"Feature Prioritisation", "synonyms":["feature prioritization","MoSCoW","RICE scoring","Kano model"],  "tier":"HIGH",   "track":"PM"},
    {"keyword":"A/B Testing",            "synonyms":["experimentation","split testing","hypothesis testing"],          "tier":"HIGH",   "track":"PM"},
    {"keyword":"Product Analytics",      "synonyms":["DAU","MAU","product metrics","activation rate","retention"],    "tier":"HIGH",   "track":"PM"},
    {"keyword":"PRD",                    "synonyms":["product requirements document","product spec","functional spec"],"tier":"MEDIUM", "track":"PM"},
    {"keyword":"NPS",                    "synonyms":["net promoter score","customer satisfaction","CSAT","CES"],       "tier":"MEDIUM", "track":"PM"},
    {"keyword":"MVP",                    "synonyms":["minimum viable product","prototype","pilot product"],            "tier":"MEDIUM", "track":"PM"},
    {"keyword":"SaaS",                   "synonyms":["software as a service","cloud product","B2B SaaS"],              "tier":"MEDIUM", "track":"PM"},
    {"keyword":"B2B",                    "synonyms":["business to business","enterprise product","B2B product"],       "tier":"MEDIUM", "track":"PM"},
    {"keyword":"Revenue Growth",         "synonyms":["P&L","revenue targets","monetisation","ARR","MRR"],             "tier":"MEDIUM", "track":"PM"},
    {"keyword":"Competitive Analysis",   "synonyms":["market research","competitive intelligence","market landscape"], "tier":"MEDIUM", "track":"PM"},
    {"keyword":"Customer Journey",       "synonyms":["user journey","customer experience","CX","journey mapping"],     "tier":"MEDIUM", "track":"PM"},
    {"keyword":"Product Launch",         "synonyms":["go-live","feature release","product release","launch plan"],     "tier":"MEDIUM", "track":"PM"},
    {"keyword":"North Star Metric",      "synonyms":["north star","primary KPI","success metric","leading indicator"], "tier":"MEDIUM", "track":"PM"},
    {"keyword":"Conversion Rate",        "synonyms":["funnel optimisation","conversion optimisation","CRO"],           "tier":"MEDIUM", "track":"PM"},
    {"keyword":"API Product",            "synonyms":["API strategy","developer product","platform API"],               "tier":"LOW",    "track":"PM"},
    {"keyword":"Growth Hacking",         "synonyms":["growth loops","viral coefficient","PLG","product-led growth"],   "tier":"LOW",    "track":"PM"},
    {"keyword":"Jobs to be Done",        "synonyms":["JTBD","customer outcomes","outcome-driven innovation"],          "tier":"LOW",    "track":"PM"},

    # ── ALL TRACKS — Senior leadership cross-track keywords ───
    {"keyword":"Digital Transformation", "synonyms":["digital change","digital strategy","digitalisation"],           "tier":"HIGH",   "track":"ALL"},
    {"keyword":"Executive Stakeholder",  "synonyms":["C-suite","board","CXO","senior leadership","executive sponsor"],"tier":"HIGH",   "track":"ALL"},
    {"keyword":"Strategic Planning",     "synonyms":["strategy development","long-term planning","strategic roadmap"], "tier":"HIGH",   "track":"ALL"},
    {"keyword":"Leadership",             "synonyms":["people leadership","team leadership","servant leadership"],      "tier":"HIGH",   "track":"ALL"},
    {"keyword":"Communication",          "synonyms":["executive communication","storytelling","presentation skills"],  "tier":"MEDIUM", "track":"ALL"},
    {"keyword":"Collaboration",          "synonyms":["team collaboration","cross-functional collaboration"],           "tier":"MEDIUM", "track":"ALL"},
    {"keyword":"Data-driven",            "synonyms":["data driven","evidence-based","insight-led","analytics-led"],   "tier":"MEDIUM", "track":"ALL"},
    {"keyword":"Innovation",             "synonyms":["innovation culture","continuous improvement","disruptive thinking"],"tier":"MEDIUM","track":"ALL"},
    {"keyword":"Agile Mindset",          "synonyms":["agile culture","growth mindset","adaptability"],                "tier":"LOW",    "track":"ALL"},
]

TIER_WEIGHTS = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}


def get_supplementary_keywords(track_code: str) -> list[dict]:
    """Return supplementary keywords for a track (includes ALL-track entries)."""
    results = []
    for entry in SUPPLEMENTARY_KEYWORDS:
        if entry["track"] in (track_code, "ALL"):
            results.append({
                "keyword":  entry["keyword"],
                "synonyms": entry["synonyms"],
                "tier":     entry["tier"],
                "track":    entry["track"],
                "weight":   TIER_WEIGHTS.get(entry["tier"], 1),
                "source":   "supplementary",
            })
    return results
