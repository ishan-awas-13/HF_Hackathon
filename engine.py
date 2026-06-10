"""
engine.py — Version Alpha
────────────────────────────────────────────────────────────────────────────
Thin orchestration layer. Wires together the three agents and exposes
the functions that interview_coach.py (Gradio UI) calls directly.

LLM Backend: LOCAL — Ollama running mistral:7b on http://localhost:11434
  Swap to HF InferenceClient before deploying to HF Spaces (see README).
"""

import gradio as gr
import json
import datetime
import os

from config import (
    OLLAMA_URL, OLLAMA_MODEL, HISTORY_FILE,
    INTERVIEW_MODES, TIPS_DB, DEFAULT_TIPS
)
from agents import ValidatorAgent, QuestionGenAgent, ScorerAgent

# ── PDF imports ───────────────────────────────────────────────────────────────
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch

# ── Ollama LLM call ──────────────────────────────────────────────────────────
def ask_llm(prompt: str, temperature: float = 0.7, max_tokens: int = 512) -> str:
    """
    Local Ollama inference call. Injected into all three agents as llm_fn.
    Model: mistral:7b running at http://localhost:11434
    """
    import requests
    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens}
        }
        r = requests.post(OLLAMA_URL, json=payload, timeout=300)
        r.raise_for_status()
        return r.json().get("response", "No response from Ollama.")
    except Exception as e:
        return f"❌ Ollama Error: {str(e)}. Is Ollama running? Try: ollama serve"



# ── Agent instances (singletons, created once at startup) ─────────────────────
_validator   = ValidatorAgent(ask_llm)
_q_gen       = QuestionGenAgent(ask_llm)
_scorer      = ScorerAgent(ask_llm)


# ── History helpers ────────────────────────────────────────────────────────────
def load_history() -> list:
    """Load current-session history from JSON file."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                content = f.read().strip()
                return json.loads(content) if content else []
        except json.JSONDecodeError:
            return []
    return []


def save_history(history: list) -> None:
    """Persist history to JSON file."""
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


# ── Main orchestration functions (called by Gradio UI) ────────────────────────

def generate_all_questions(job_desc: str, mode_label: str,
                           history_state: list, job_profile_state: dict):
    """
    Entry point for the "Start Interview" button.
    Validates the JD, extracts a profile, generates N questions,
    and builds the Prep Sheet for Tab 3.

    Returns:
        (first_question, "0", progress_str, history_state,
         tips_markdown, job_profile_state, score_result_state)
    """
    n_questions = INTERVIEW_MODES.get(mode_label, 3)

    # ── 1. Validate & extract profile ─────────────────────────────────────────
    validation_result = _validator.run(job_desc)

    if not validation_result.get("valid"):
        err = validation_result.get("error_msg", "Please enter a complete job description.")
        gr.Warning(err)
        return (
            "Please enter a valid job description and try again.",
            "0",
            "Ready",
            history_state,
            _build_fallback_tips(job_desc),
            job_profile_state,
            {},
        )

    job_profile_state = validation_result  # Save enriched profile to state

    # ── 2. Generate questions ──────────────────────────────────────────────────
    questions = _q_gen.run(validation_result, job_desc, n_questions=n_questions)

    # ── 3. Build session ───────────────────────────────────────────────────────
    session = {
        "timestamp":    datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "job_snippet":  job_desc[:80] + "...",
        "industry":     validation_result.get("industry", "General"),
        "role_level":   validation_result.get("role_level", "Mid-Level"),
        "mode":         mode_label,
        "questions":    questions,
        "answers":      [""] * n_questions,
        "scores":       [""] * n_questions,
        "numeric_scores": [],
        "score_results":  [],  # Full ScorerAgent result dicts
    }

    # Current-session-only: overwrite history with this single session
    history_state = [session]
    save_history(history_state)

    # ── 4. Build AI-generated Prep Sheet ─────────────────────────────────────
    tips_md = _build_prep_sheet(validation_result)

    return (
        questions[0],
        "0",
        f"Question 1 / {n_questions}",
        history_state,
        tips_md,
        job_profile_state,
        {},  # Reset score_result_state
    )


def score_answer(answer: str, q_index_str: str,
                 history_state: list, job_profile_state: dict):
    """
    Score the candidate's answer using ScorerAgent (keyword-aware).
    Returns the formatted feedback text and updated state.
    """
    idx = int(q_index_str) if q_index_str else 0

    if not history_state:
        return "Start an interview first.", history_state, {}

    session   = history_state[-1]
    questions = session.get("questions", [])
    question  = questions[idx] if idx < len(questions) else "Unknown question"

    # ── Run ScorerAgent ────────────────────────────────────────────────────────
    result = _scorer.run(answer, question, job_profile_state)

    # ── Save to session ────────────────────────────────────────────────────────
    if idx < len(session["answers"]):
        session["answers"][idx]  = answer[:100] + ("..." if len(answer) > 100 else "")
        session["scores"][idx]   = result["score_str"]
        if result["numeric_score"] is not None:
            session["numeric_scores"].append(result["numeric_score"])

        # Store full result dicts (for PDF keyword coverage section)
        while len(session["score_results"]) <= idx:
            session["score_results"].append({})
        session["score_results"][idx] = result

    history_state[-1] = session
    save_history(history_state)

    # ── Build formatted feedback text ─────────────────────────────────────────
    formatted = _format_feedback(result)

    return formatted, history_state, result


def next_question(q_index_str: str, answer: str, history_state: list):
    """Move to the next question; return prev Q+A for the review panel."""
    idx = int(q_index_str) if q_index_str else 0

    if not history_state:
        return "Start an interview first.", "", str(idx), "No session", history_state, "", "", ""

    session   = history_state[-1]
    questions = session["questions"]
    n_total   = len(questions)
    next_idx  = idx + 1

    prev_q     = questions[idx]
    prev_a     = answer or "(no answer given)"
    prev_score = session["scores"][idx] if session["scores"][idx] else "(no feedback yet)"

    if next_idx >= n_total:
        log = _render_session_log(session, up_to=idx)
        return (
            f"✅ All {n_total} questions complete! Go to the History tab to download your PDF report.",
            "",
            str(idx),
            f"Interview Complete 🎉",
            history_state,
            prev_q,
            prev_a,
            log,
        )

    log = _render_session_log(session, up_to=idx)
    return (
        questions[next_idx],
        "",
        str(next_idx),
        f"Question {next_idx + 1} / {n_total}",
        history_state,
        prev_q,
        prev_a,
        log,
    )


# ── History rendering ──────────────────────────────────────────────────────────
def render_history(history_state: list) -> str:
    """Render the session history as Markdown for the History tab."""
    history = history_state or []
    disk = load_history()
    if len(disk) > len(history):
        history = disk

    if not history:
        return "No session yet. Start an interview above!"

    lines = []
    for i, s in enumerate(reversed(history), 1):
        avg_str = ""
        if s.get("numeric_scores"):
            avg = sum(s["numeric_scores"]) / len(s["numeric_scores"])
            avg_str = f" · **Avg: {avg:.1f}/10**"

        mode_badge = s.get("mode", "")
        lines.append(f"### 📋 Session — {s['timestamp']}{avg_str}")
        lines.append(f"**Role:** {s.get('job_snippet','N/A')}  |  **Mode:** {mode_badge}  |  **Industry:** {s.get('industry','N/A')}")

        scores_display = " · ".join(filter(None, s.get("scores", []))) or "No feedback yet"
        lines.append(f"**Scores:** {scores_display}\n")

        for j, (q, a, sc) in enumerate(zip(s["questions"], s["answers"], s["scores"]), 1):
            lines.append(f"**Q{j}:** {q}")
            if a:
                lines.append(f"*Answer:* {a}")
            if sc:
                lines.append(f"*Score:* {sc}")
            lines.append("")
        lines.append("---")

    return "\n".join(lines)


def _render_session_log(session: dict, up_to: int) -> str:
    """Render completed Q+A+Score for the in-Practice session log."""
    if up_to < 0:
        return "No completed questions yet."
    lines = []
    for i in range(up_to + 1):
        q  = session["questions"][i]
        a  = session["answers"][i] or "(no answer saved)"
        sc = session["scores"][i]  or "(no feedback yet)"
        lines.extend([f"**Q{i+1}:** {q}", f"*Answer:* {a}", f"*Score:* {sc}", ""])
    return "\n".join(lines)


# ── Prep Sheet builder (Agenda #2 & #5 — fully AI-generated) ──────────────────
def _build_prep_sheet(profile: dict) -> str:
    """
    Build a rich, AI-tailored preparation sheet using the validated job profile.
    Uses LLM-extracted data — works for ANY industry/role.
    """
    industry  = profile.get("industry", "General")
    level     = profile.get("role_level", "Mid-Level")
    style     = profile.get("interview_style", "Mixed")
    keywords  = profile.get("keywords", [])
    tips      = profile.get("tips", "")

    kw_badges = "  ".join(f"`{k}`" for k in keywords)

    tips_section = ""
    if tips:
        # Ensure each bullet starts on its own line
        tips_lines = [t.strip() for t in tips.replace("•", "\n•").split("\n") if t.strip()]
        tips_section = "\n".join(f"- {t.lstrip('•').strip()}" for t in tips_lines if t)

    # Static resources based on industry (best effort keyword match)
    resources = _get_resources(industry)

    return f"""## 🎯 Prep Sheet: {level} {industry} Role

### 🔑 Expected Keywords in Your Answers
> Hit these terms to score above 5/10. The AI coach checks for them.

{kw_badges}

### 💡 Interview Preparation Tips
*Tailored for this specific role by AI*

{tips_section or "- Review the job description carefully and prepare examples using STAR format."}

### 📐 Interview Style: {style}
{_style_advice(style)}

### 🧠 STAR Format Reminder
Use this structure for every behavioral or situational answer:
- **S**ituation — Set the scene (brief context)
- **T**ask — What were you responsible for?
- **A**ction — What did YOU specifically do? (most important)
- **R**esult — Quantify the outcome where possible

### 🔗 Useful Resources
{resources}
"""


def _style_advice(style: str) -> str:
    guides = {
        "Technical":   "- Expect coding problems, system design, or domain-specific technical questions\n- Think aloud — interviewers evaluate your reasoning process\n- Clarify requirements before diving into solutions",
        "Behavioral":  "- Every answer should use the STAR format\n- Prepare 5–7 strong stories from your past that cover teamwork, conflict, leadership, failure\n- Be specific — avoid vague generalities",
        "Case-Based":  "- Structure your approach before answering: clarify, hypothesise, analyse, recommend\n- Practice frameworks: MECE, Porter's 5 Forces, SWOT\n- Show quantitative reasoning wherever possible",
        "Mixed":       "- Prepare for both behavioral STAR stories AND domain-specific technical questions\n- Research the company's tech stack / domain before the interview\n- Have questions ready to ask the interviewer",
    }
    return guides.get(style, guides["Mixed"])


def _get_resources(industry: str) -> str:
    il = industry.lower()
    if any(w in il for w in ["software", "engineer", "developer", "python", "data", "ml", "ai"]):
        return "- [NeetCode Roadmap](https://neetcode.io/roadmap)\n- [Tech Interview Handbook](https://www.techinterviewhandbook.org/)\n- [System Design Primer](https://github.com/donnemartin/system-design-primer)\n- [Pramp — Free Mock Interviews](https://www.pramp.com/)"
    elif any(w in il for w in ["finance", "banking", "investment", "accounting"]):
        return "- [Breaking Into Wall Street](https://breakingintowallstreet.com/)\n- [Investopedia](https://www.investopedia.com/)\n- [Wall Street Oasis Forums](https://www.wallstreetoasis.com/)"
    elif any(w in il for w in ["market", "brand", "digital", "content", "seo"]):
        return "- [HubSpot Marketing Blog](https://blog.hubspot.com/marketing)\n- [Google Skillshop](https://skillshop.withgoogle.com/)\n- [Moz Beginner's Guide to SEO](https://moz.com/beginners-guide-to-seo)"
    elif any(w in il for w in ["health", "medical", "clinical", "nurse", "pharma"]):
        return "- [Interview Coach for Healthcare](https://www.indeed.com/career-advice/interviewing)\n- [NHS Interview Tips](https://www.healthcareers.nhs.uk/)"
    else:
        return "- [Indeed Interview Tips](https://www.indeed.com/career-advice/interviewing)\n- [Glassdoor Interview Questions](https://www.glassdoor.com/Interview/)\n- [LinkedIn Interview Prep](https://www.linkedin.com/interview-prep/)\n- [Big Interview](https://biginterview.com/)"


def _build_fallback_tips(job_desc: str) -> str:
    """Keyword-matched static tips as a fallback when validation fails."""
    jd_lower = job_desc.lower()
    matched = DEFAULT_TIPS
    for key, data in TIPS_DB.items():
        if key in jd_lower:
            matched = data
            break
    lc_rows = "\n".join(f"| [{p}]({url}) | {diff} |" for p, url, diff in matched["leetcode"])
    concept_rows = "\n".join(f"- ✅ {c}" for c in matched["concepts"])
    return f"""## 🎯 Tips: {matched['label']}\n\n### 📚 Key Concepts\n{concept_rows}\n\n### 💻 LeetCode Problems\n| Problem | Difficulty |\n|---------|------------|\n{lc_rows}\n"""


# ── Feedback formatter (for Gradio textbox display) ───────────────────────────
def _format_feedback(result: dict) -> str:
    """Convert ScorerAgent result dict into a human-readable string."""
    raw = result.get("raw_feedback", "")
    if not raw:
        return "No feedback generated."

    # Append keyword coverage summary
    hit   = result.get("hit_keywords", [])
    missed = result.get("missed_keywords", [])
    cov   = result.get("coverage_pct", 0)
    star_hint = result.get("star_hint", False)

    coverage_line = f"\n\n─────────────────────────\n🔑 Keyword Coverage: {cov:.0f}%"
    if hit:
        coverage_line += f"\n✅ Found: {', '.join(hit)}"
    if missed:
        coverage_line += f"\n❌ Missing: {', '.join(missed)}"
    if star_hint:
        coverage_line += "\n\n💡 STAR Tip: Try to structure your answer — Situation → Task → Action → Result"

    return raw + coverage_line


# ── PDF Report generation ──────────────────────────────────────────────────────
def generate_pdf_report(history_state: list) -> str:
    """
    Generate a timestamped, styled PDF report from the current session.
    Returns the file path string.
    """
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"Interview_Report_{ts}.pdf"

    if not history_state:
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        doc.build([Paragraph("No interview data available.", styles["Heading2"])])
        return filename

    doc    = SimpleDocTemplate(filename, pagesize=letter,
                               leftMargin=0.75*inch, rightMargin=0.75*inch,
                               topMargin=0.85*inch, bottomMargin=0.85*inch)
    styles = getSampleStyleSheet()
    story  = []

    # ── Styles ────────────────────────────────────────────────────────────────
    title_s = ParagraphStyle("Title", parent=styles["Heading1"], alignment=TA_CENTER,
                             fontSize=22, spaceAfter=6, textColor=HexColor("#0f172a"),
                             fontName="Helvetica-Bold")
    sub_s   = ParagraphStyle("Sub",   parent=styles["Normal"],  alignment=TA_CENTER,
                             fontSize=10, spaceAfter=24, textColor=HexColor("#64748b"))
    h2_s    = ParagraphStyle("H2",    parent=styles["Heading2"], fontSize=14,
                             spaceBefore=18, spaceAfter=8,
                             textColor=HexColor("#1e293b"), fontName="Helvetica-Bold")
    h3_s    = ParagraphStyle("H3",    parent=styles["Heading3"], fontSize=11,
                             spaceBefore=12, spaceAfter=4,
                             textColor=HexColor("#334155"), fontName="Helvetica-Bold")
    body_s  = ParagraphStyle("Body",  parent=styles["BodyText"], fontSize=9.5,
                             spaceBefore=3, spaceAfter=3, leading=14,
                             textColor=HexColor("#475569"))
    meta_s  = ParagraphStyle("Meta",  parent=body_s, fontSize=9,
                             textColor=HexColor("#64748b"))

    # ── Title block ───────────────────────────────────────────────────────────
    story.append(Paragraph("AI Interview Coach", title_s))
    story.append(Paragraph("Interview Session Report", sub_s))
    story.append(Paragraph('<hr/>', ParagraphStyle("sep")))
    story.append(Spacer(1, 0.15*inch))

    # ── Sessions ──────────────────────────────────────────────────────────────
    for s_idx, session in enumerate(reversed(history_state)):
        n = len(history_state) - s_idx
        story.append(Paragraph(f"Session #{n}", h2_s))

        # Metadata table
        meta_data = [
            [Paragraph("<b>Date:</b>", meta_s),     Paragraph(session.get("timestamp","N/A"), meta_s)],
            [Paragraph("<b>Role:</b>", meta_s),     Paragraph(session.get("job_snippet","N/A"), meta_s)],
            [Paragraph("<b>Industry:</b>", meta_s), Paragraph(session.get("industry","N/A"), meta_s)],
            [Paragraph("<b>Mode:</b>", meta_s),     Paragraph(session.get("mode","N/A"), meta_s)],
        ]
        meta_tbl = Table(meta_data, colWidths=[1.2*inch, 5.3*inch])
        meta_tbl.setStyle(TableStyle([
            ("ALIGN",  (0,0), (-1,-1), "LEFT"),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING",  (0,0), (-1,-1), 0),
            ("RIGHTPADDING", (0,0), (-1,-1), 4),
            ("TOPPADDING",   (0,0), (-1,-1), 2),
            ("BOTTOMPADDING",(0,0), (-1,-1), 2),
        ]))
        story.append(meta_tbl)

        # Overall score badge
        num_scores = session.get("numeric_scores", [])
        if num_scores:
            avg = sum(num_scores) / len(num_scores)
            color = "#10b981" if avg >= 8 else ("#f59e0b" if avg >= 5 else "#ef4444")
            badge_s = ParagraphStyle("Badge", parent=styles["Normal"], alignment=TA_CENTER,
                                     fontSize=12, fontName="Helvetica-Bold",
                                     textColor=HexColor("#ffffff"),
                                     backColor=HexColor(color),
                                     spaceBefore=10, spaceAfter=10,
                                     borderPadding=6)
            story.append(Paragraph(f"Overall Score: {avg:.1f}/10", badge_s))

        # Q&A breakdown
        story.append(Paragraph("Questions & Answers", h2_s))
        questions    = session.get("questions", [])
        answers      = session.get("answers", [])
        scores       = session.get("scores", [])
        score_results = session.get("score_results", [])

        for i, (q, a, sc) in enumerate(zip(questions, answers, scores), 1):
            story.append(Paragraph(f"Q{i}: {q}", h3_s))
            a_text  = a if a.strip() else "(No answer provided)"
            sc_text = sc if sc.strip() else "(No feedback)"
            story.append(Paragraph(f"<b>Answer:</b> {a_text}", body_s))
            story.append(Paragraph(f"<b>Score:</b> {sc_text}", body_s))

            # Keyword coverage row
            if i-1 < len(score_results) and score_results[i-1]:
                sr   = score_results[i-1]
                cov  = sr.get("coverage_pct", 0)
                hit  = ", ".join(sr.get("hit_keywords", [])) or "None"
                miss = ", ".join(sr.get("missed_keywords", [])) or "None"
                story.append(Paragraph(
                    f"<b>Keyword Coverage:</b> {cov:.0f}%  ·  "
                    f"<b>Found:</b> {hit}  ·  <b>Missing:</b> {miss}",
                    body_s
                ))
            story.append(Spacer(1, 0.08*inch))

        # Summary & recommendations
        story.append(Paragraph("Summary & Recommendations", h2_s))
        if num_scores:
            avg = sum(num_scores) / len(num_scores)
            if avg >= 8:
                rec = "Excellent performance! Strong technical knowledge and clear structured answers. Maintain this depth and confidence."
            elif avg >= 5:
                rec = "Good effort. Solid understanding but focus on incorporating more industry keywords and structuring responses with the STAR format."
            else:
                rec = "Practice needed. Expand your answers, use industry-specific terminology, and structure responses more effectively using STAR."
            story.append(Paragraph(rec, body_s))
        else:
            story.append(Paragraph("Complete more questions to receive coaching recommendations.", body_s))

        if s_idx < len(history_state) - 1:
            story.append(PageBreak())

    doc.build(story)
    return filename
