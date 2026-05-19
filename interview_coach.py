import gradio as gr
import requests
import json
import datetime

OLLAMA_URL = "http://localhost:11434/api/generate"

# ── Ollama helper ──────────────────────────────────────────────────────────────
def ask_ollama(prompt, model="mistral:7b", temperature=0.7):
    try:
        payload = {"model": model, "prompt": prompt, "stream": False, "temperature": temperature}
        r = requests.post(OLLAMA_URL, json=payload, timeout=300)
        return r.json().get("response", "No response")
    except Exception as e:
        return f"❌ Error: {str(e)}"

# ── Question generation ────────────────────────────────────────────────────────
QUESTION_PROMPTS = [
    "Generate ONE interview question about the candidate's most recent project experience. Question:",
    "Generate ONE follow-up interview question about the specific technologies or tools used. Question:",
    "Generate ONE interview question about a challenge they faced and how they overcame it. Question:",
]

def clean_question(raw):
    if "Question:" in raw:
        raw = raw.split("Question:")[-1].strip()
    if "?" in raw:
        raw = raw.split("?")[0] + "?"
    return raw.strip()

def generate_all_questions(job_desc, history_state):
    if not job_desc or len(job_desc.strip()) < 20:
        return "Please paste a job description (20+ characters).", "", "Ready", history_state, gr.update()

    job_desc = job_desc[:500]
    questions = []
    for p in QUESTION_PROMPTS:
        full_prompt = f"Based on this job description:\n{job_desc}\n\n{p}"
        q = clean_question(ask_ollama(full_prompt, temperature=0.8))
        questions.append(q)

    session = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "job_snippet": job_desc[:60] + "...",
        "questions": questions,
        "answers": ["", "", ""],
        "scores": ["", "", ""],
    }

    history_state = history_state or []
    history_state.append(session)

    tips_md = build_tips(job_desc)

    return questions[0], "0", "Question 1 / 3", history_state, gr.update(value=tips_md)

# ── Answer scoring ─────────────────────────────────────────────────────────────
def score_answer(answer, q_index_str, history_state):
    if not answer or len(answer.strip()) < 15:
        return "Please write a longer answer (15+ characters).", history_state

    idx = int(q_index_str) if q_index_str else 0
    answer = answer[:500]

    prompt = f"""You are a strict but constructive interview coach. Rate this answer 0-10.

Answer: {answer}

Respond in this exact format:
Relevant: YES or NO
Score: X/10
Strength: (one sentence)
Weakness: (one sentence)
Fix: (one specific improvement)"""

    feedback = ask_ollama(prompt, temperature=0.5)

    # Save to history
    if history_state:
        last = history_state[-1]
        if idx < len(last["answers"]):
            last["answers"][idx] = answer[:80] + "..."
            # Extract score
            for line in feedback.splitlines():
                if line.startswith("Score:"):
                    last["scores"][idx] = line.replace("Score:", "").strip()
                    break
        history_state[-1] = last

    return feedback, history_state

# ── Navigation ─────────────────────────────────────────────────────────────────
def next_question(q_index_str, history_state):
    idx = int(q_index_str) if q_index_str else 0
    if not history_state:
        return "Start an interview first.", str(idx), "No session", history_state

    questions = history_state[-1]["questions"]
    next_idx = idx + 1

    if next_idx >= len(questions):
        return "✅ All 3 questions complete! Check your history below.", str(idx), "Interview Complete 🎉", history_state

    progress = f"Question {next_idx + 1} / 3"
    return questions[next_idx], str(next_idx), progress, history_state

# ── History rendering ──────────────────────────────────────────────────────────
def render_history(history_state):
    if not history_state:
        return "No sessions yet. Start your first interview above!"

    lines = []
    for i, s in enumerate(reversed(history_state), 1):
        scores_display = " | ".join(s["scores"]) if any(s["scores"]) else "No feedback yet"
        lines.append(f"### Session {len(history_state) - i + 1} — {s['timestamp']}")
        lines.append(f"**Role:** {s['job_snippet']}")
        lines.append(f"**Scores:** {scores_display}")
        for j, (q, a, sc) in enumerate(zip(s["questions"], s["answers"], s["scores"]), 1):
            lines.append(f"\n**Q{j}:** {q}")
            if a:
                lines.append(f"*Your answer:* {a}")
            if sc:
                lines.append(f"*Score:* {sc}")
        lines.append("---")

    return "\n".join(lines)

# ── Tips & Resources ───────────────────────────────────────────────────────────
TIPS_DB = {
    "python": {
        "label": "Python / Backend",
        "leetcode": [
            ("Two Sum", "https://leetcode.com/problems/two-sum/", "Easy"),
            ("LRU Cache", "https://leetcode.com/problems/lru-cache/", "Medium"),
            ("Word Search II", "https://leetcode.com/problems/word-search-ii/", "Hard"),
        ],
        "concepts": ["OOP principles", "Decorators & generators", "Async / await", "REST API design"],
    },
    "react": {
        "label": "React / Frontend",
        "leetcode": [
            ("Valid Parentheses", "https://leetcode.com/problems/valid-parentheses/", "Easy"),
            ("Flatten Nested List", "https://leetcode.com/problems/flatten-nested-list-iterator/", "Medium"),
        ],
        "concepts": ["Virtual DOM", "Hooks & state management", "Component lifecycle", "Web performance"],
    },
    "machine learning": {
        "label": "Machine Learning",
        "leetcode": [
            ("Find Peak Element", "https://leetcode.com/problems/find-peak-element/", "Medium"),
            ("Kth Largest Element", "https://leetcode.com/problems/kth-largest-element-in-an-array/", "Medium"),
        ],
        "concepts": ["Bias-variance tradeoff", "Overfitting & regularisation", "Gradient descent", "Model evaluation metrics"],
    },
    "sql": {
        "label": "SQL / Databases",
        "leetcode": [
            ("Employees Earning More Than Manager", "https://leetcode.com/problems/employees-earning-more-than-their-managers/", "Easy"),
            ("Department Top 3 Salaries", "https://leetcode.com/problems/department-top-three-salaries/", "Hard"),
        ],
        "concepts": ["JOINs & subqueries", "Indexing strategies", "Transactions & ACID", "Query optimisation"],
    },
}

DEFAULT_TIPS = {
    "label": "General Software Engineering",
    "leetcode": [
        ("Two Sum", "https://leetcode.com/problems/two-sum/", "Easy"),
        ("Merge Intervals", "https://leetcode.com/problems/merge-intervals/", "Medium"),
        ("Trapping Rain Water", "https://leetcode.com/problems/trapping-rain-water/", "Hard"),
    ],
    "concepts": ["STAR answer format", "System design basics", "Time & space complexity", "Behavioural questions"],
}

def build_tips(job_desc=""):
    jd_lower = job_desc.lower()
    matched = DEFAULT_TIPS
    for key, data in TIPS_DB.items():
        if key in jd_lower:
            matched = data
            break

    lc_rows = "\n".join(
        f"| [{p}]({url}) | {diff} |"
        for p, url, diff in matched["leetcode"]
    )
    concept_rows = "\n".join(f"- ✅ {c}" for c in matched["concepts"])

    return f"""## 🎯 Tips for: {matched['label']}

### 📚 Key Concepts to Revise
{concept_rows}

### 💻 Recommended LeetCode Problems
| Problem | Difficulty |
|---------|-----------|
{lc_rows}

### 🧠 General Interview Advice
- Use the **STAR format** (Situation → Task → Action → Result) for behavioural questions
- Always quantify impact: *"reduced load time by 40%"* beats *"made it faster"*
- It's okay to take 30 seconds to think before answering
- Ask clarifying questions — interviewers reward curiosity

### 🔗 Useful Resources
- [Grokking the System Design Interview](https://www.educative.io/courses/grokking-the-system-design-interview)
- [NeetCode Roadmap](https://neetcode.io/roadmap)
- [Tech Interview Handbook](https://www.techinterviewhandbook.org/)
- [Pramp — Free Mock Interviews](https://www.pramp.com/)
"""

# ── Custom CSS ─────────────────────────────────────────────────────────────────
CUSTOM_CSS = """
/* Google Font */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* { font-family: 'Inter', sans-serif !important; }

/* Accent gradient on primary buttons */
.gr-button-primary {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
    transition: transform 0.15s, box-shadow 0.15s !important;
}
.gr-button-primary:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(99,102,241,0.4) !important;
}

/* Secondary buttons */
.gr-button-secondary {
    border: 2px solid #6366f1 !important;
    color: #6366f1 !important;
    font-weight: 600 !important;
    transition: all 0.15s !important;
}
.gr-button-secondary:hover {
    background: #6366f1 !important;
    color: white !important;
}

/* Progress badge */
#progress_box textarea {
    font-weight: 700 !important;
    font-size: 1rem !important;
    color: #6366f1 !important;
    text-align: center !important;
}

/* Feedback box */
#feedback_box textarea {
    font-size: 0.95rem !important;
    line-height: 1.6 !important;
}

/* Tabs */
.tab-nav button {
    font-weight: 600 !important;
    font-size: 0.9rem !important;
}

/* Header */
.app-header {
    text-align: center;
    padding: 1.5rem 0 0.5rem;
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a78bfa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
"""

# ── Build UI ───────────────────────────────────────────────────────────────────
with gr.Blocks(title="AI Interview Coach") as demo:

    # ── State ──────────────────────────────────────────────────────────────────
    history_state = gr.State([])
    q_index = gr.State("0")

    # ── Header ─────────────────────────────────────────────────────────────────
    gr.HTML("""
    <div style="text-align:center; padding: 1.8rem 0 0.8rem;">
        <h1 style="font-size:2.2rem; font-weight:800; margin:0;
                   background: linear-gradient(135deg,#6366f1,#a78bfa);
                   -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
            🎤 AI Interview Coach
        </h1>
        <p style="color:#64748b; margin-top:0.4rem; font-size:1rem;">
            Powered by a local Mistral 7B model · Practice · Get Feedback · Improve
        </p>
    </div>
    """)

    # ── Tabs ───────────────────────────────────────────────────────────────────
    with gr.Tabs():

        # ── Tab 1: Practice ───────────────────────────────────────────────────
        with gr.Tab("🎯 Practice"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 📋 Step 1 — Paste the Job Description")
                    job_desc_box = gr.Textbox(
                        label="Job Description",
                        lines=6,
                        placeholder="Paste from LinkedIn, company careers page, etc.\nInclude role title, required skills, and responsibilities...",
                    )
                    start_btn = gr.Button("🚀 Start Interview", variant="primary", size="lg")

                with gr.Column(scale=1):
                    gr.Markdown("### 💬 Step 2 — Answer Questions")
                    progress_box = gr.Textbox(
                        label="Progress",
                        value="Ready to start",
                        interactive=False,
                        elem_id="progress_box",
                    )
                    question_box = gr.Textbox(
                        label="Interview Question",
                        lines=3,
                        interactive=False,
                        placeholder="Your question will appear here after clicking Start...",
                    )
                    answer_box = gr.Textbox(
                        label="Your Answer",
                        lines=5,
                        placeholder="Type your answer here. Be specific — use the STAR format (Situation, Task, Action, Result).",
                    )
                    with gr.Row():
                        feedback_btn = gr.Button("📊 Get Feedback", variant="primary")
                        next_btn = gr.Button("➡️ Next Question", variant="secondary")

            gr.Markdown("### 🏆 Step 3 — Coach Feedback")
            feedback_box = gr.Textbox(
                label="AI Coach Feedback",
                interactive=False,
                lines=7,
                placeholder="Feedback will appear here after you click 'Get Feedback'...",
                elem_id="feedback_box",
            )

        # ── Tab 2: History ────────────────────────────────────────────────────
        with gr.Tab("📈 History & Progress"):
            gr.Markdown("""
            ### Your Interview Sessions
            All sessions are stored locally during this browser session.
            """)
            refresh_btn = gr.Button("🔄 Refresh History", variant="secondary")
            history_display = gr.Markdown("No sessions yet. Start your first interview!")

        # ── Tab 3: Tips & Resources ───────────────────────────────────────────
        with gr.Tab("💡 Tips & Resources"):
            tips_display = gr.Markdown(build_tips())

    # ── Wire up events ─────────────────────────────────────────────────────────
    start_btn.click(
        fn=generate_all_questions,
        inputs=[job_desc_box, history_state],
        outputs=[question_box, q_index, progress_box, history_state, tips_display],
    )

    feedback_btn.click(
        fn=score_answer,
        inputs=[answer_box, q_index, history_state],
        outputs=[feedback_box, history_state],
    )

    next_btn.click(
        fn=next_question,
        inputs=[q_index, history_state],
        outputs=[question_box, q_index, progress_box, history_state],
    )

    refresh_btn.click(
        fn=render_history,
        inputs=[history_state],
        outputs=[history_display],
    )

    # Auto-refresh history whenever a session is updated
    start_btn.click(
        fn=render_history,
        inputs=[history_state],
        outputs=[history_display],
    )
    feedback_btn.click(
        fn=render_history,
        inputs=[history_state],
        outputs=[history_display],
    )

demo.launch(
    theme=gr.themes.Soft(
        primary_hue=gr.themes.colors.violet,
        secondary_hue=gr.themes.colors.purple,
        neutral_hue=gr.themes.colors.slate,
        font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "sans-serif"],
    ),
    css=CUSTOM_CSS,
)