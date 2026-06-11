"""
interview_coach.py — Version Alpha
────────────────────────────────────────────────────────────────────────────
Pure Gradio UI layer. Imports all logic from engine.py and config.py.
All business logic lives in engine.py and agents/.

UI Structure (4 Tabs):
  Tab 1 — 🎯 Practice    : JD input + mode selector + Q&A + feedback
  Tab 2 — 📈 History     : Session history + PDF download
  Tab 3 — 💡 Prep Sheet  : AI-generated role-specific preparation guide
  Tab 4 — ℹ️ About       : How scoring works, STAR guide
"""

import gradio as gr
import os
from config import CUSTOM_CSS, INTERVIEW_MODES
from engine import (
    load_history, render_history, generate_all_questions,
    score_answer, next_question, generate_pdf_report,
)

# ── Animated background HTML ──────────────────────────────────────────────────
_BLOBS_HTML = """
<style>
    @keyframes blob1 {
        0%,100% { transform: translate(0px, 0px) scale(1); }
        33%  { transform: translate(-40px, -50px) scale(1.05); }
        66%  { transform: translate(80px, -20px) scale(0.95); }
    }
    @keyframes blob2 {
        0%,100% { transform: translate(0px, 0px) scale(1); }
        33%  { transform: translate(60px, 40px) scale(1.08); }
        66%  { transform: translate(-40px, 60px) scale(0.92); }
    }
    @keyframes blob3 {
        0%,100% { transform: translate(0px, 0px) scale(1); }
        33%  { transform: translate(-50px, 60px) scale(0.95); }
        66%  { transform: translate(40px, -50px) scale(1.05); }
    }
    @keyframes blob4 {
        0%,100% { transform: translate(0px, 0px) scale(1); }
        33%  { transform: translate(70px, 110px) scale(1.03); }
        66%  { transform: translate(20px, -30px) scale(0.97); }
    }
    .blob {
        position: fixed;
        border-radius: 50%;
        filter: blur(90px);
        z-index: 0;
        pointer-events: none;
    }
</style>
<div class="blob" style="width:420px;height:320px;background:#6366f1;opacity:0.28;top:-120px;left:-120px;animation:blob1 22s ease-in-out infinite;"></div>
<div class="blob" style="width:520px;height:400px;background:#8b5cf6;opacity:0.20;top:45%;right:-200px;animation:blob2 28s ease-in-out infinite;"></div>
<div class="blob" style="width:580px;height:360px;background:#f97316;opacity:0.15;bottom:-120px;left:80px;animation:blob3 18s ease-in-out infinite;"></div>
<div class="blob" style="width:480px;height:340px;background:#ec4899;opacity:0.15;top:60px;right:100px;animation:blob4 24s ease-in-out infinite;"></div>
"""

_HEADER_HTML = """
<div style="text-align:center; padding: 2rem 0 1rem; position:relative; z-index:1;">
    <div style="display:inline-flex; align-items:center; gap:12px; margin-bottom:0.5rem;">
        <span style="font-size:2.4rem;">🎙️</span>
        <h1 style="margin:0; font-size:2.5rem; font-weight:800; letter-spacing:-0.5px;
                   background:linear-gradient(135deg,#6366f1 0%,#a78bfa 50%,#ec4899 100%);
                   -webkit-background-clip:text; -webkit-text-fill-color:transparent; line-height:1;">
            AI Interview Coach
        </h1>
    </div>
    <p style="color:#94a3b8; margin:0; font-size:1rem; font-weight:400;">
        <span style="font-weight:600; color:#cbd5e1;">Practice · Get Feedback · Improve</span>
    </p>
    <p style="color:#64748b; margin:0.3rem 0 0; font-size:0.82rem;">
        Powered by <span style="color:#f97316; font-weight:700;">Mistral 7B</span>
    </p>
</div>
"""

def _score_badge_html(score_result: dict) -> str:
    """Render keyword coverage badges as inline HTML."""
    if not score_result:
        return ""
    hit    = score_result.get("hit_keywords", [])
    missed = score_result.get("missed_keywords", [])
    cov    = score_result.get("coverage_pct", 0)

    color = "#10b981" if cov >= 70 else ("#f59e0b" if cov >= 40 else "#ef4444")
    badge_style = "display:inline-block;padding:3px 9px;border-radius:20px;font-size:0.78rem;font-weight:600;margin:3px 3px;"

    hit_badges    = "".join(f'<span style="{badge_style}background:rgba(16,185,129,0.15);color:#10b981;border:1px solid rgba(16,185,129,0.3);">✅ {k}</span>' for k in hit)
    missed_badges = "".join(f'<span style="{badge_style}background:rgba(239,68,68,0.12);color:#ef4444;border:1px solid rgba(239,68,68,0.25);">❌ {k}</span>' for k in missed)

    return f"""
<div style="background:rgba(15,15,40,0.6);border:1px solid rgba(99,102,241,0.2);border-radius:12px;padding:14px 18px;margin-top:10px;">
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
        <span style="font-size:0.85rem;font-weight:700;color:#94a3b8;">🔑 KEYWORD COVERAGE</span>
        <span style="background:{color};color:white;padding:3px 12px;border-radius:20px;font-size:0.82rem;font-weight:700;">{cov:.0f}%</span>
    </div>
    <div style="line-height:2.2;">{hit_badges}{missed_badges}</div>
</div>
"""

def _progress_bar_html(current: int, total: int) -> str:
    """Render an HTML progress bar for question progress."""
    if total == 0:
        return ""
    pct = int((current / total) * 100)
    return f"""
<div style="margin:6px 0 10px;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">
        <span style="font-size:0.82rem;font-weight:600;color:#94a3b8;">Progress</span>
        <span style="font-size:0.82rem;font-weight:700;color:#a5b4fc;">Q{current} of {total}</span>
    </div>
    <div style="height:6px;background:rgba(99,102,241,0.15);border-radius:3px;overflow:hidden;">
        <div style="height:100%;width:{pct}%;background:linear-gradient(90deg,#6366f1,#a78bfa);border-radius:3px;transition:width 0.4s ease;"></div>
    </div>
</div>
"""

_ABOUT_MD = """
## 🎙️ About AI Interview Coach

**AI Interview Coach** is an intelligent interview preparation tool powered by **Mistral 7B** via the HuggingFace Inference API.

---

### 🔄 How It Works

1. **Paste** your target job description
2. **Choose** your interview depth (Quick / Standard / Deep Dive)
3. **Answer** AI-generated questions tailored to that specific role
4. **Get feedback** with scores, strengths, weaknesses, and keyword analysis
5. **Download** a PDF report of your session

---

### 📊 How Scoring Works

| Score | Meaning |
|-------|---------|
| 8–10 | Excellent — strong STAR structure, good keyword coverage |
| 5–7 | Good — solid effort, but missing some key terms or depth |
| 1–4 | Needs work — expand your answers and use role-specific language |
| NIL | Irrelevant — answer must be a genuine attempt at the question |

> **Keyword Coverage Rule:** The AI extracts 5–7 key terms from the job description. If your answer uses fewer than 40% of them, your score is capped at **5/10**. Use the Prep Sheet to learn which terms to include.

---

### ⭐ The STAR Format

Use this structure for behavioral and situational answers:

| Part | What to Say | Example |
|------|-------------|---------|
| **S**ituation | Set the context | "At my previous company, we had a critical deadline..." |
| **T**ask | Your role/responsibility | "I was responsible for..." |
| **A**ction | What YOU did | "I specifically implemented..." |
| **R**esult | Outcome (quantified if possible) | "This reduced load time by 40%..." |

---

### 🚀 Interview Modes

| Mode | Questions | Best For |
|------|-----------|---------|
| ⚡ Quick | 3 | Final-hour revision, confidence check |
| 📋 Standard | 5 | Regular practice sessions |
| 🔬 Deep Dive | 7 | Thorough preparation for important interviews |

---

*Built for the HuggingFace Hackathon 2026 · Model: mistralai/Mistral-7B-Instruct-v0.3 (7B params)*
"""

# ── Build UI ────────────────────────────────────────────────────────────────── 
with gr.Blocks(title="AI Interview Coach", fill_width=True) as demo:

    # ── Shared State ──────────────────────────────────────────────────────────
    history_state     = gr.State(load_history())
    q_index           = gr.State("0")
    job_profile_state = gr.State({
        "valid": False, "industry": "General",
        "role_level": "Mid-Level", "keywords": [],
        "tips": "", "interview_style": "Mixed",
    })
    score_result_state = gr.State({})  # Latest ScorerAgent result for badge rendering
    n_questions_state  = gr.State(3)   # Resolved question count for progress bar

    # ── Background + Header ───────────────────────────────────────────────────
    gr.HTML(_BLOBS_HTML)
    gr.HTML(_HEADER_HTML)

    with gr.Tabs():

        # ══════════════════════════════════════════════════════════════════════
        # TAB 1: PRACTICE
        # ══════════════════════════════════════════════════════════════════════
        with gr.Tab("🎯 Practice"):

            with gr.Row(equal_height=False):

                # ── LEFT COLUMN: Job Input + Mode ─────────────────────────────
                with gr.Column(scale=1, min_width=340):
                    gr.HTML('<p style="color:#94a3b8;font-size:0.78rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;margin:0 0 6px;">Step 1</p>')
                    gr.Markdown("### 📋 Paste the Job Description")

                    job_desc_box = gr.Textbox(
                        label="Job Description",
                        lines=9,
                        placeholder="Paste from LinkedIn, a company's careers page, etc.\n\nTip: A longer, more detailed JD = better tailored questions.",
                    )

                    gr.HTML('<p style="color:#94a3b8;font-size:0.78rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;margin:12px 0 6px;">Step 2</p>')
                    gr.Markdown("### 🎚️ Choose Interview Depth")

                    mode_selector = gr.Radio(
                        choices=list(INTERVIEW_MODES.keys()),
                        value="⚡ Quick (3 Questions)",
                        label="Interview Mode",
                        info="How many questions do you want to answer?",
                    )

                    start_btn = gr.Button(
                        "🚀 Start Interview", variant="primary", size="lg",
                    )

                    gr.HTML("""
                    <div style="margin-top:16px;padding:12px 16px;background:rgba(99,102,241,0.07);
                                border:1px solid rgba(99,102,241,0.2);border-radius:10px;">
                        <p style="margin:0;font-size:0.82rem;color:#94a3b8;line-height:1.6;">
                            <strong style="color:#a5b4fc;">💡 Tips for a better session:</strong><br>
                            • Paste the <em>full</em> job posting (350+ characters)<br>
                            • Answer in complete sentences<br>
                            • Use STAR format for behavioral questions
                        </p>
                    </div>
                    """)

                # ── RIGHT COLUMN: Q&A ─────────────────────────────────────────
                with gr.Column(scale=1, min_width=400):
                    gr.HTML('<p style="color:#94a3b8;font-size:0.78rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;margin:0 0 6px;">Step 3</p>')
                    gr.Markdown("### 💬 Answer Questions")

                    progress_bar_display = gr.HTML('<div style="display:none"></div>')

                    question_box = gr.Textbox(
                        label="Interview Question",
                        lines=3,
                        interactive=False,
                        placeholder="Your question will appear here after you click Start Interview...",
                    )

                    answer_box = gr.Textbox(
                        label="Your Answer",
                        lines=5,
                        placeholder=(
                            "Answer in complete sentences.\n\n"
                            "💡 STAR Format: Situation → Task → Action → Result"
                        ),
                    )

                    with gr.Row():
                        feedback_btn = gr.Button("📊 Get Feedback", variant="primary")
                        next_btn     = gr.Button("➡️ Next Question", variant="secondary")

            # ── Keyword Coverage Badge Area ───────────────────────────────────
            keyword_badges_display = gr.HTML('<div style="display:none"></div>')

            # ── Feedback ──────────────────────────────────────────────────────
            gr.HTML('<div style="margin-top:8px;"><p style="color:#94a3b8;font-size:0.78rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;margin:0 0 6px;">Step 4</p></div>')
            gr.Markdown("### 🏆 AI Coach Feedback")
            feedback_box = gr.Textbox(
                label="AI Coach Feedback",
                interactive=False,
                lines=8,
                elem_id="feedback_box",
                placeholder="Feedback will appear here after you click Get Feedback...",
            )

            # ── Review Panels ─────────────────────────────────────────────────
            with gr.Accordion("🔁 Previous Question Review", open=False):
                with gr.Row():
                    prev_question_box = gr.Textbox(
                        label="Previous Question", interactive=False, lines=2,
                        placeholder="Appears after clicking Next Question...",
                    )
                    prev_answer_box = gr.Textbox(
                        label="Your Previous Answer", interactive=False, lines=3,
                        placeholder="Your last answer...",
                    )

            with gr.Accordion("📋 This Session's Log", open=False):
                session_log_display = gr.Markdown("Complete questions to see your session log here.")

        # ══════════════════════════════════════════════════════════════════════
        # TAB 2: HISTORY & PDF
        # ══════════════════════════════════════════════════════════════════════
        with gr.Tab("📈 History & Report"):
            gr.HTML("""
            <div style="padding:8px 0 16px;">
                <h3 style="color:#e2e8f0;margin:0 0 6px;font-size:1.1rem;">📄 Download Your Interview Report</h3>
                <p style="color:#94a3b8;margin:0;font-size:0.88rem;">
                    Generate a professionally formatted PDF containing your questions, answers, AI feedback, keyword analysis, and coaching recommendations.
                </p>
            </div>
            """)

            with gr.Row():
                download_report_btn = gr.Button("📥 Generate PDF Report", variant="primary", size="lg")
                refresh_btn         = gr.Button("🔄 Refresh Preview", variant="secondary")
                clear_btn           = gr.Button("🗑️ Clear Session", variant="secondary")

            report_file_output = gr.File(label="Your PDF Report — click to download", interactive=False)

            gr.HTML('<hr style="border:none;border-top:1px solid rgba(99,102,241,0.15);margin:20px 0;"/>')
            gr.Markdown("### 📝 Session Summary")
            history_display = gr.Markdown(render_history(load_history()))

        # ══════════════════════════════════════════════════════════════════════
        # TAB 3: PREP SHEET
        # ══════════════════════════════════════════════════════════════════════
        with gr.Tab("💡 Prep Sheet"):
            gr.HTML("""
            <div style="padding:8px 0 16px;">
                <h3 style="color:#e2e8f0;margin:0 0 4px;font-size:1.1rem;">💡 AI-Generated Preparation Guide</h3>
                <p style="color:#94a3b8;margin:0;font-size:0.88rem;">
                    This guide is generated specifically for your target role after you click <strong>Start Interview</strong>.
                    It includes expected keywords, interview style tips, and curated resources.
                </p>
            </div>
            """)
            tips_display = gr.Markdown(
                "*Start an interview on the Practice tab to generate your personalised prep sheet.*"
            )

        # ══════════════════════════════════════════════════════════════════════
        # TAB 4: ABOUT
        # ══════════════════════════════════════════════════════════════════════
        with gr.Tab("ℹ️ About"):
            gr.Markdown(_ABOUT_MD)

    # ── Event wiring ──────────────────────────────────────────────────────────

    def _handle_start(job_desc, mode_label, history_state, job_profile_state):
        """Wrapper: calls engine, then updates progress bar HTML."""
        result = generate_all_questions(job_desc, mode_label, history_state, job_profile_state)
        # result = (question, "0", progress_str, history_state, tips_md, job_profile, score_result)
        first_q, idx_str, _prog_str, new_hist, tips_md, new_profile, new_score_res = result

        n = INTERVIEW_MODES.get(mode_label, 3)
        prog_html = _progress_bar_html(1, n) if "Please" not in first_q else '<div style="display:none"></div>'
        empty_html = '<div style="display:none"></div>'

        return first_q, idx_str, new_hist, tips_md, new_profile, new_score_res, n, prog_html, empty_html

    start_btn.click(
        fn=_handle_start,
        inputs=[job_desc_box, mode_selector, history_state, job_profile_state],
        outputs=[
            question_box, q_index, history_state,
            tips_display, job_profile_state, score_result_state,
            n_questions_state, progress_bar_display, keyword_badges_display,
        ],
    ).then(
        fn=render_history,
        inputs=[history_state],
        outputs=[history_display],
    )

    def _handle_feedback(answer, q_index_str, history_state, job_profile_state, n_total):
        """Wrapper: calls engine scorer, then renders keyword badge HTML."""
        feedback_text, new_hist, result = score_answer(
            answer, q_index_str, history_state, job_profile_state
        )
        badges_html = _score_badge_html(result)
        idx = int(q_index_str) if q_index_str else 0
        prog_html = _progress_bar_html(idx + 1, n_total)
        return feedback_text, new_hist, result, badges_html, prog_html

    feedback_btn.click(
        fn=_handle_feedback,
        inputs=[answer_box, q_index, history_state, job_profile_state, n_questions_state],
        outputs=[feedback_box, history_state, score_result_state, keyword_badges_display, progress_bar_display],
    ).then(
        fn=render_history,
        inputs=[history_state],
        outputs=[history_display],
    )

    def _handle_next(q_index_str, answer, history_state, n_total):
        """Wrapper: calls engine next_question, updates progress bar."""
        result = next_question(q_index_str, answer, history_state)
        # result = (question, answer, idx_str, progress_str, history, prev_q, prev_a, log)
        new_q, new_a, new_idx, prog_str, new_hist, prev_q, prev_a, log = result
        idx = int(new_idx) if new_idx else 0
        prog_html = _progress_bar_html(idx + 1, n_total) if "Complete" not in prog_str else _progress_bar_html(n_total, n_total)
        empty_html = '<div style="display:none"></div>'  # collapse badge area between questions
        return new_q, new_a, new_idx, new_hist, prev_q, prev_a, log, prog_html, empty_html

    next_btn.click(
        fn=_handle_next,
        inputs=[q_index, answer_box, history_state, n_questions_state],
        outputs=[
            question_box, answer_box, q_index, history_state,
            prev_question_box, prev_answer_box, session_log_display,
            progress_bar_display, keyword_badges_display,
        ],
    )

    download_report_btn.click(
        fn=generate_pdf_report,
        inputs=[history_state],
        outputs=[report_file_output],
    )

    refresh_btn.click(
        fn=render_history,
        inputs=[history_state],
        outputs=[history_display],
    )

    def clear_history_fn(history_state):
        with open("interview_history.json", "w") as f:
            f.write("[]")
        return [], "Session cleared! Start a new interview above."

    clear_btn.click(
        fn=clear_history_fn,
        inputs=[history_state],
        outputs=[history_state, history_display],
    )

# ── Launch ────────────────────────────────────────────────────────────────────
custom_theme = gr.themes.Soft(
    primary_hue=gr.themes.colors.violet,
    secondary_hue=gr.themes.colors.purple,
    neutral_hue=gr.themes.colors.slate,
    font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "sans-serif"],
)

demo.launch(theme=custom_theme, css=CUSTOM_CSS)