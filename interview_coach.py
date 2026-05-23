import gradio as gr
import requests
import json
import datetime
import os

OLLAMA_URL = "http://localhost:11434/api/generate"
HISTORY_FILE = "interview_history.json"

# ── Persistent History Helpers ─────────────────────────────────────────────────
def load_history():
    """Load history from JSON file on disk"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_history(history):
    """Save history to JSON file on disk"""
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

# ── Ollama helper ──────────────────────────────────────────────────────────────
def ask_ollama(prompt, model="mistral:7b", temperature=0.7):
    try:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "temperature": temperature
        }
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
        "numeric_scores": [],
    }

    history_state = history_state or []
    history_state.append(session)
    save_history(history_state)  # 💾 Save to disk

    tips_md = build_tips(job_desc)
    return questions[0], "0", "Question 1 / 3", history_state, gr.update(value=tips_md)

# ── Answer scoring ─────────────────────────────────────────────────────────────
def score_answer(answer, q_index_str, history_state):
    if not answer or len(answer.strip()) < 15:
        return "Please write a longer answer (15+ characters).", history_state

    idx = int(q_index_str) if q_index_str else 0
    answer = answer[:500]

    prompt = f"""You are a strict interview coach evaluating a candidate's spoken interview answer.

Candidate's answer: {answer}

STEP 1 — Relevance check:
Is this a genuine attempt at answering an interview question? 
It is NOT relevant if it is: random text, mix of random text, code, gibberish, a single word, copy-pasted content, or completely off-topic, only partially meaningful or relevant.

STEP 2 - 
If NOT relevant, respond with ONLY these two lines and nothing else:
Relevant: NO
Score: NIL/10
Warning: ⚠️ Irrelevant response detected. Please answer the interview question properly using the STAR format.

If it IS a genuine interview answer, respond with ALL of the following lines and NOTHING else:
Relevant: YES
Score: X/10
Strength: (one sentence about what was done well)
Weakness: (one sentence about the biggest gap)
Fix: (one specific, actionable improvement the candidate can make to their spoken answer — no code)"""

    feedback = ask_ollama(prompt, temperature=0.5)

    # Save to history
    if history_state:
        last = history_state[-1]
        if idx < len(last["answers"]):
            last["answers"][idx] = answer[:80] + "..."
            for line in feedback.splitlines():
                if line.startswith("Score:"):
                    score_str = line.replace("Score:", "").strip()
                    last["scores"][idx] = score_str
                    # Extract numeric score
                    try:
                        numeric = float(score_str.split("/")[0].strip())
                        last["numeric_scores"].append(numeric)
                    except:
                        pass
                    break
        history_state[-1] = last
        save_history(history_state)  # 💾 Save to disk

    return feedback, history_state

# ── Navigation ─────────────────────────────────────────────────────────────────
def next_question(q_index_str, answer, history_state):
    """Move to next question, returning previous Q+A for the review panel."""
    idx = int(q_index_str) if q_index_str else 0
    if not history_state:
        return "Start an interview first.", "", str(idx), "No session", history_state, "", "", ""

    session = history_state[-1]
    questions = session["questions"]
    next_idx = idx + 1

    # Capture what the user just answered (for the prev panel)
    prev_q = questions[idx]
    prev_a = answer or "(no answer given)"
    prev_score = session["scores"][idx] if session["scores"][idx] else "(no feedback yet)"

    if next_idx >= len(questions):
        session_log = render_session_log(session, up_to=idx)
        return (
            "✅ All 3 questions complete! Check your history.",
            "",           # clear answer box
            str(idx),
            "Interview Complete 🎉",
            history_state,
            prev_q,
            prev_a,
            session_log,
        )

    session_log = render_session_log(session, up_to=idx)
    return (
        questions[next_idx],
        "",            # clear answer box
        str(next_idx),
        f"Question {next_idx + 1} / 3",
        history_state,
        prev_q,
        prev_a,
        session_log,
    )

def render_session_log(session, up_to):
    """Render completed Q+A+Score pairs for the current session (up to index `up_to`)."""
    if up_to < 0:
        return "No completed questions yet."
    lines = []
    for i in range(up_to + 1):
        q = session["questions"][i]
        a = session["answers"][i] or "(no answer saved)"
        sc = session["scores"][i] or "(no feedback yet)"
        lines.append(f"**Q{i+1}:** {q}")
        lines.append(f"*Your answer:* {a}")
        lines.append(f"*Score:* {sc}")
        lines.append("")
    return "\n".join(lines)

# ── History rendering ──────────────────────────────────────────────────────────
def compute_stats(history):
    """Compute overall stats across all sessions"""
    all_scores = []
    for s in history:
        for score in s.get("numeric_scores", []):
            all_scores.append(score)

    if not all_scores:
        return None

    avg = sum(all_scores) / len(all_scores)
    best = max(all_scores)

    # Trend: compare first half vs second half
    trend = ""
    if len(all_scores) >= 4:
        mid = len(all_scores) // 2
        first_avg = sum(all_scores[:mid]) / mid
        second_avg = sum(all_scores[mid:]) / (len(all_scores) - mid)
        diff = second_avg - first_avg
        if diff > 0.5:
            trend = "📈 Improving!"
        elif diff < -0.5:
            trend = "📉 Declining — practice more"
        else:
            trend = "➡️ Consistent"

    return {
        "total_sessions": len(history),
        "total_answers": len(all_scores),
        "avg_score": round(avg, 1),
        "best_score": round(best, 1),
        "trend": trend
    }

def render_history(history_state):
    """Render full history with stats"""
    history = history_state or []

    # Load from disk too (in case state and disk diverge)
    disk_history = load_history()
    if len(disk_history) > len(history):
        history = disk_history

    if not history:
        return "No sessions yet. Start your first interview above!"

    lines = []

    # Stats block
    stats = compute_stats(history)
    if stats:
        lines.append("## 📊 Your Progress")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Total Sessions | {stats['total_sessions']} |")
        lines.append(f"| Total Answers | {stats['total_answers']} |")
        lines.append(f"| Average Score | {stats['avg_score']}/10 |")
        lines.append(f"| Best Score | {stats['best_score']}/10 |")
        if stats['trend']:
            lines.append(f"| Trend | {stats['trend']} |")
        lines.append("")

    # Sessions
    lines.append("## 📝 Session History")
    for i, s in enumerate(reversed(history), 1):
        scores_display = " | ".join(s["scores"]) if any(s["scores"]) else "No feedback yet"
        avg = ""
        if s.get("numeric_scores"):
            avg = f" · Avg: {round(sum(s['numeric_scores'])/len(s['numeric_scores']), 1)}/10"

        lines.append(f"### Session {len(history) - i + 1} — {s['timestamp']}{avg}")
        lines.append(f"**Role:** {s['job_snippet']}")
        lines.append(f"**Scores:** {scores_display}")

        for j, (q, a, sc) in enumerate(zip(s["questions"], s["answers"], s["scores"]), 1):
            lines.append(f"\n### **Q{j}:** {q}\n")
            if a:
                lines.append(f"**Answer:** {a}\n")
            if sc:
                lines.append(f"**Score:** {sc}\n")
        lines.append("\n---")

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
@import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&display=swap');
* { font-family: 'Google Sans', 'Product Sans', sans-serif !important; }

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
#progress_box textarea {
    font-weight: 700 !important;
    font-size: 1rem !important;
    color: #6366f1 !important;
    text-align: center !important;
}
#feedback_box textarea {
    font-size: 0.95rem !important;
    line-height: 1.6 !important;
}
.tab-nav button { font-weight: 600 !important; }

/* ── Animated blob background ── */
body {
    background: #0d0d1f !important;
}
gradio-app {
    background: transparent !important;
}
.gradio-container {
    background: transparent !important;
}
"""

# ── Build UI ───────────────────────────────────────────────────────────────────
with gr.Blocks(
    title="AI Interview Coach",
    theme=gr.themes.Soft(
        primary_hue=gr.themes.colors.violet,
        secondary_hue=gr.themes.colors.purple,
        neutral_hue=gr.themes.colors.slate,
        font=[gr.themes.GoogleFont("Google Sans"), "ui-sans-serif", "sans-serif"],
    ),
    css=CUSTOM_CSS
) as demo:

    # Load history from disk on startup
    history_state = gr.State(load_history())
    q_index = gr.State("0")

    gr.HTML("""
    <div style="text-align:center; padding: 1.8rem 0 0.8rem;">
        <h1 style="font-size:2.2rem; font-weight:800; margin:0; font-size: 2.2rem;
                   background: linear-gradient(135deg,#6366f1,#a78bfa);
                   -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
            AI Interview Coach
        </h1>
        <p style="color:#64748b; margin-top:0.4rem; font-size:1rem;">
            <b>Practice · Get Feedback · Improve</b><br>
            <span style="font-size:0.8rem; color:#808080;">Powered by <span style="color:#f97316; font-weight:600;">Mistral 7B</span></span>
        </p>
    </div>
    """)

    gr.HTML("""
        <style>
            @keyframes floatBlob1 {
                0%   { transform: translate(0px,   0px);  }
                33%  { transform: translate(-30px, -40px); }
                66%  { transform: translate(40px,  -20px); }
                100% { transform: translate(0px,   0px);  }
            }
            @keyframes floatBlob2 {
                0%   { transform: translate(0px,  0px);  }
                33%  { transform: translate(50px, 30px);  }
                66%  { transform: translate(-30px, 50px); }
                100% { transform: translate(0px,  0px);  }
            }
            @keyframes floatBlob3 {
                0%   { transform: translate(0px,   0px);  }
                33%  { transform: translate(-40px, 50px); }
                66%  { transform: translate(30px, -40px); }
                100% { transform: translate(0px,   0px);  }
            }
        </style>

        <div style="
            position: fixed; width: 400px; height: 300px;
            border-radius: 50%; background: #6366f1;
            filter: blur(80px); opacity: 0.35;
            top: -100px; left: -100px;
            z-index: 0; pointer-events: none;
            animation: floatBlob1 20s ease-in-out infinite;
        "></div>

        <div style="
            position: fixed; width: 500px; height: 400px;
            border-radius: 50%; background: #8b5cf6;
            filter: blur(100px); opacity: 0.25;
            top: 50%; right: -200px;
            z-index: 0; pointer-events: none;
            animation: floatBlob2 25s ease-in-out infinite;
        "></div>

        <div style="
            position: fixed; width: 600px; height: 350px;
            border-radius: 50%; background: #f97316;
            filter: blur(90px); opacity: 0.2;
            bottom: -100px; left: 100px;
            z-index: 0; pointer-events: none;
            animation: floatBlob3 15s ease-in-out infinite;
        "></div>
    """)

    with gr.Tabs():

        # ── Tab 1: Practice ───────────────────────────────────────────────────
        with gr.Tab("🎯 Practice"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 📋 Step 1 — Paste the Job Description")
                    job_desc_box = gr.Textbox(
                        label="Job Description",
                        lines=6,
                        placeholder="Paste from LinkedIn, company careers page, etc.",
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
                    )
                    answer_box = gr.Textbox(
                        label="Your Answer",
                        lines=5,
                        placeholder="Be specific — use the STAR format (Situation, Task, Action, Result).",
                    )
                    with gr.Row():
                        feedback_btn = gr.Button("📊 Get Feedback", variant="primary")
                        next_btn = gr.Button("➡️ Next Question", variant="secondary")

            # ── Previous answer review panel ──────────────────────────────────
            with gr.Accordion("🔁 Previous Question Review", open=False) as prev_accordion:
                with gr.Row():
                    prev_question_box = gr.Textbox(
                        label="Previous Question",
                        interactive=False,
                        lines=2,
                        placeholder="Will show the last question after you click Next Question...",
                    )
                    prev_answer_box = gr.Textbox(
                        label="Your Previous Answer",
                        interactive=False,
                        lines=3,
                        placeholder="Will show your last answer here...",
                    )

            # ── Full session log accordion ─────────────────────────────────────
            with gr.Accordion("📋 This Session's Log", open=False):
                session_log_display = gr.Markdown("Complete questions to see your session log here.")

            gr.Markdown("### 🏆 Step 3 — Coach Feedback")
            feedback_box = gr.Textbox(
                label="AI Coach Feedback",
                interactive=False,
                lines=7,
                elem_id="feedback_box",
            )

        # ── Tab 2: History ────────────────────────────────────────────────────
        with gr.Tab("📈 History & Progress"):
            gr.Markdown("""
            ### Your Interview Sessions
            History is **saved to disk** — persists across restarts! 💾
            """)
            with gr.Row():
                refresh_btn = gr.Button("🔄 Refresh History", variant="secondary")
                clear_btn = gr.Button("🗑️ Clear History", variant="secondary")
            history_display = gr.Markdown(
                render_history(load_history())  # Load from disk on startup
            )

        # ── Tab 3: Tips ───────────────────────────────────────────────────────
        with gr.Tab("💡 Tips & Resources"):
            tips_display = gr.Markdown(build_tips())

    # ── Wire up events ─────────────────────────────────────────────────────────
    start_btn.click(
        fn=generate_all_questions,
        inputs=[job_desc_box, history_state],
        outputs=[question_box, q_index, progress_box, history_state, tips_display],
    ).then(
        fn=render_history,
        inputs=[history_state],
        outputs=[history_display],
    )

    feedback_btn.click(
        fn=score_answer,
        inputs=[answer_box, q_index, history_state],
        outputs=[feedback_box, history_state],
    ).then(
        fn=render_history,
        inputs=[history_state],
        outputs=[history_display],
    )

    next_btn.click(
        fn=next_question,
        inputs=[q_index, answer_box, history_state],
        outputs=[question_box, answer_box, q_index, progress_box, history_state, prev_question_box, prev_answer_box, session_log_display],
    )

    refresh_btn.click(
        fn=render_history,
        inputs=[history_state],
        outputs=[history_display],
    )

    def clear_history(history_state):
        """Clear all history"""
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        return [], "History cleared! Start a new interview above."

    clear_btn.click(
        fn=clear_history,
        inputs=[history_state],
        outputs=[history_state, history_display],
    )

demo.launch()