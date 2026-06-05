# **Main Code Backup:**

import gradio as gr

import requests

import json

import datetime

import os

OLLAMA_URL = "http://localhost:11434/api/generate"

HISTORY_FILE = "interview_history.json"

\# ── Persistent History Helpers ─────────────────────────────────────────────────

def load_history():

&#x20; """Load history from JSON file on disk"""

&#x20; if os.path.exists(HISTORY_FILE):

&#x20; with open(HISTORY_FILE, "r") as f:

&#x20; return json.load(f)

&#x20; return \[]

def save_history(history):

&#x20; """Save history to JSON file on disk"""

&#x20; with open(HISTORY_FILE, "w") as f:

&#x20; json.dump(history, f, indent=2)

\# ── Ollama helper ──────────────────────────────────────────────────────────────

def ask_ollama(prompt, model="mistral:7b", temperature=0.7):

&#x20; try:

&#x20; payload = {

&#x20; "model": model,

&#x20; "prompt": prompt,

&#x20; "stream": False,

&#x20; "temperature": temperature

&#x20; }

&#x20; r = requests.post(OLLAMA_URL, json=payload, timeout=300)

&#x20; return r.json().get("response", "No response")

&#x20; except Exception as e:

&#x20; return f"❌ Error: {str(e)}"

\# ── Question generation ────────────────────────────────────────────────────────

QUESTION_PROMPTS = \[

&#x20; "Generate ONE interview question about the candidate's most recent project experience. Question:",

&#x20; "Generate ONE follow-up interview question about the specific technologies or tools used. Question:",

&#x20; "Generate ONE interview question about a challenge they faced and how they overcame it. Question:",

]

def clean_question(raw):

&#x20; if "Question:" in raw:

&#x20; raw = raw.split("Question:")\[-1].strip()

&#x20; if "?" in raw:

&#x20; raw = raw.split("?")\[0] + "?"

&#x20; return raw.strip()

def generate_all_questions(job_desc, history_state):

&#x20; if not job_desc or len(job_desc.strip()) < 20:

&#x20; return "Please paste a job description (20+ characters).", "", "Ready", history_state, gr.update()

&#x20; job_desc = job_desc\[:500]

&#x20; questions = \[]

&#x20; for p in QUESTION_PROMPTS:

&#x20; full_prompt = f"Based on this job description:\\n{job_desc}\\n\\n{p}"

&#x20; q = clean_question(ask_ollama(full_prompt, temperature=0.8))

&#x20; questions.append(q)

&#x20; session = {

&#x20; "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),

&#x20; "job_snippet": job_desc\[:60] + "...",

&#x20; "questions": questions,

&#x20; "answers": \["", "", ""],

&#x20; "scores": \["", "", ""],

&#x20; "numeric_scores": \[],

&#x20; }

&#x20; history_state = history_state or \[]

&#x20; history_state.append(session)

&#x20; save_history(history_state) # 💾 Save to disk

&#x20; tips_md = build_tips(job_desc)

&#x20; return questions\[0], "0", "Question 1 / 3", history_state, gr.update(value=tips_md)

\# ── Answer scoring ─────────────────────────────────────────────────────────────

def score_answer(answer, q_index_str, history_state):

&#x20; if not answer or len(answer.strip()) < 15:

&#x20; return "Please write a longer answer (15+ characters).", history_state

&#x20; idx = int(q_index_str) if q_index_str else 0

&#x20; answer = answer\[:500]

&#x20; prompt = f"""You are a strict interview coach evaluating a candidate's spoken interview answer.

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

&#x20; feedback = ask_ollama(prompt, temperature=0.5)

&#x20; # Save to history

&#x20; if history_state:

&#x20; last = history_state\[-1]

&#x20; if idx < len(last\["answers"]):

&#x20; last\["answers"]\[idx] = answer\[:80] + "..."

&#x20; for line in feedback.splitlines():

&#x20; if line.startswith("Score:"):

&#x20; score_str = line.replace("Score:", "").strip()

&#x20; last\["scores"]\[idx] = score_str

&#x20; # Extract numeric score

&#x20; try:

&#x20; numeric = float(score_str.split("/")\[0].strip())

&#x20; last\["numeric_scores"].append(numeric)

&#x20; except:

&#x20; pass

&#x20; break

&#x20; history_state\[-1] = last

&#x20; save_history(history_state) # 💾 Save to disk

&#x20; return feedback, history_state

\# ── Navigation ─────────────────────────────────────────────────────────────────

def next_question(q_index_str, answer, history_state):

&#x20; """Move to next question, returning previous Q+A for the review panel."""

&#x20; idx = int(q_index_str) if q_index_str else 0

&#x20; if not history_state:

&#x20; return "Start an interview first.", "", str(idx), "No session", history_state, "", "", ""

&#x20; session = history_state\[-1]

&#x20; questions = session\["questions"]

&#x20; next_idx = idx + 1

&#x20; # Capture what the user just answered (for the prev panel)

&#x20; prev_q = questions\[idx]

&#x20; prev_a = answer or "(no answer given)"

&#x20; prev_score = session\["scores"]\[idx] if session\["scores"]\[idx] else "(no feedback yet)"

&#x20; if next_idx >= len(questions):

&#x20; session_log = render_session_log(session, up_to=idx)

&#x20; return (

&#x20; "✅ All 3 questions complete! Check your history.",

&#x20; "", # clear answer box

&#x20; str(idx),

&#x20; "Interview Complete 🎉",

&#x20; history_state,

&#x20; prev_q,

&#x20; prev_a,

&#x20; session_log,

&#x20; )

&#x20; session_log = render_session_log(session, up_to=idx)

&#x20; return (

&#x20; questions\[next_idx],

&#x20; "", # clear answer box

&#x20; str(next_idx),

&#x20; f"Question {next_idx + 1} / 3",

&#x20; history_state,

&#x20; prev_q,

&#x20; prev_a,

&#x20; session_log,

&#x20; )

def render_session_log(session, up_to):

&#x20; """Render completed Q+A+Score pairs for the current session (up to index `up\_to`)."""

&#x20; if up_to < 0:

&#x20; return "No completed questions yet."

&#x20; lines = \[]

&#x20; for i in range(up_to + 1):

&#x20; q = session\["questions"]\[i]

&#x20; a = session\["answers"]\[i] or "(no answer saved)"

&#x20; sc = session\["scores"]\[i] or "(no feedback yet)"

&#x20; lines.append(f"\*\*Q{i+1}:\*\* {q}")

&#x20; lines.append(f"\*Your answer:\* {a}")

&#x20; lines.append(f"\*Score:\* {sc}")

&#x20; lines.append("")

&#x20; return "\\n".join(lines)

\# ── History rendering ──────────────────────────────────────────────────────────

def compute_stats(history):

&#x20; """Compute overall stats across all sessions"""

&#x20; all_scores = \[]

&#x20; for s in history:

&#x20; for score in s.get("numeric_scores", \[]):

&#x20; all_scores.append(score)

&#x20; if not all_scores:

&#x20; return None

&#x20; avg = sum(all_scores) / len(all_scores)

&#x20; best = max(all_scores)

&#x20; # Trend: compare first half vs second half

&#x20; trend = ""

&#x20; if len(all_scores) >= 4:

&#x20; mid = len(all_scores) // 2

&#x20; first_avg = sum(all_scores\[:mid]) / mid

&#x20; second_avg = sum(all_scores\[mid:]) / (len(all_scores) - mid)

&#x20; diff = second_avg - first_avg

&#x20; if diff > 0.5:

&#x20; trend = "📈 Improving!"

&#x20; elif diff < -0.5:

&#x20; trend = "📉 Declining — practice more"

&#x20; else:

&#x20; trend = "➡️ Consistent"

&#x20; return {

&#x20; "total_sessions": len(history),

&#x20; "total_answers": len(all_scores),

&#x20; "avg_score": round(avg, 1),

&#x20; "best_score": round(best, 1),

&#x20; "trend": trend

&#x20; }

def render_history(history_state):

&#x20; """Render full history with stats"""

&#x20; history = history_state or \[]

&#x20; # Load from disk too (in case state and disk diverge)

&#x20; disk_history = load_history()

&#x20; if len(disk_history) > len(history):

&#x20; history = disk_history

&#x20; if not history:

&#x20; return "No sessions yet. Start your first interview above!"

&#x20; lines = \[]

&#x20; # Stats block

&#x20; stats = compute_stats(history)

&#x20; if stats:

&#x20; lines.append("## 📊 Your Progress")

&#x20; lines.append(f"| Metric | Value |")

&#x20; lines.append(f"|--------|-------|")

&#x20; lines.append(f"| Total Sessions | {stats\['total_sessions']} |")

&#x20; lines.append(f"| Total Answers | {stats\['total_answers']} |")

&#x20; lines.append(f"| Average Score | {stats\['avg_score']}/10 |")

&#x20; lines.append(f"| Best Score | {stats\['best_score']}/10 |")

&#x20; if stats\['trend']:

&#x20; lines.append(f"| Trend | {stats\['trend']} |")

&#x20; lines.append("")

&#x20; # Sessions

&#x20; lines.append("## 📝 Session History")

&#x20; for i, s in enumerate(reversed(history), 1):

&#x20; scores_display = " | ".join(s\["scores"]) if any(s\["scores"]) else "No feedback yet"

&#x20; avg = ""

&#x20; if s.get("numeric_scores"):

&#x20; avg = f" · Avg: {round(sum(s\['numeric_scores'])/len(s\['numeric_scores']), 1)}/10"

&#x20; lines.append(f"### Session {len(history) - i + 1} — {s\['timestamp']}{avg}")

&#x20; lines.append(f"\*\*Role:\*\* {s\['job_snippet']}")

&#x20; lines.append(f"\*\*Scores:\*\* {scores_display}")

&#x20; for j, (q, a, sc) in enumerate(zip(s\["questions"], s\["answers"], s\["scores"]), 1):

&#x20; lines.append(f"\\n### \*\*Q{j}:\*\* {q}\\n")

&#x20; if a:

&#x20; lines.append(f"\*\*Answer:\*\* {a}\\n")

&#x20; if sc:

&#x20; lines.append(f"\*\*Score:\*\* {sc}\\n")

&#x20; lines.append("\\n---")

&#x20; return "\\n".join(lines)

\# ── Tips \& Resources ───────────────────────────────────────────────────────────

TIPS_DB = {

&#x20; "python": {

&#x20; "label": "Python / Backend",

&#x20; "leetcode": \[

&#x20; ("Two Sum", "https://leetcode.com/problems/two-sum/", "Easy"),

&#x20; ("LRU Cache", "https://leetcode.com/problems/lru-cache/", "Medium"),

&#x20; ("Word Search II", "https://leetcode.com/problems/word-search-ii/", "Hard"),

&#x20; ],

&#x20; "concepts": \["OOP principles", "Decorators \& generators", "Async / await", "REST API design"],

&#x20; },

&#x20; "react": {

&#x20; "label": "React / Frontend",

&#x20; "leetcode": \[

&#x20; ("Valid Parentheses", "https://leetcode.com/problems/valid-parentheses/", "Easy"),

&#x20; ("Flatten Nested List", "https://leetcode.com/problems/flatten-nested-list-iterator/", "Medium"),

&#x20; ],

&#x20; "concepts": \["Virtual DOM", "Hooks \& state management", "Component lifecycle", "Web performance"],

&#x20; },

&#x20; "machine learning": {

&#x20; "label": "Machine Learning",

&#x20; "leetcode": \[

&#x20; ("Find Peak Element", "https://leetcode.com/problems/find-peak-element/", "Medium"),

&#x20; ("Kth Largest Element", "https://leetcode.com/problems/kth-largest-element-in-an-array/", "Medium"),

&#x20; ],

&#x20; "concepts": \["Bias-variance tradeoff", "Overfitting \& regularisation", "Gradient descent", "Model evaluation metrics"],

&#x20; },

&#x20; "sql": {

&#x20; "label": "SQL / Databases",

&#x20; "leetcode": \[

&#x20; ("Employees Earning More Than Manager", "https://leetcode.com/problems/employees-earning-more-than-their-managers/", "Easy"),

&#x20; ("Department Top 3 Salaries", "https://leetcode.com/problems/department-top-three-salaries/", "Hard"),

&#x20; ],

&#x20; "concepts": \["JOINs \& subqueries", "Indexing strategies", "Transactions \& ACID", "Query optimisation"],

&#x20; },

}

DEFAULT_TIPS = {

&#x20; "label": "General Software Engineering",

&#x20; "leetcode": \[

&#x20; ("Two Sum", "https://leetcode.com/problems/two-sum/", "Easy"),

&#x20; ("Merge Intervals", "https://leetcode.com/problems/merge-intervals/", "Medium"),

&#x20; ("Trapping Rain Water", "https://leetcode.com/problems/trapping-rain-water/", "Hard"),

&#x20; ],

&#x20; "concepts": \["STAR answer format", "System design basics", "Time \& space complexity", "Behavioural questions"],

}

def build_tips(job_desc=""):

&#x20; jd_lower = job_desc.lower()

&#x20; matched = DEFAULT_TIPS

&#x20; for key, data in TIPS_DB.items():

&#x20; if key in jd_lower:

&#x20; matched = data

&#x20; break

&#x20; lc_rows = "\\n".join(

&#x20; f"| \[{p}]({url}) | {diff} |"

&#x20; for p, url, diff in matched\["leetcode"]

&#x20; )

&#x20; concept_rows = "\\n".join(f"- ✅ {c}" for c in matched\["concepts"])

&#x20; return f"""## 🎯 Tips for: {matched\['label']}

\### 📚 Key Concepts to Revise

{concept_rows}

\### 💻 Recommended LeetCode Problems

| Problem | Difficulty |

|---------|-----------|

{lc_rows}

\### 🧠 General Interview Advice

\- Use the \*\*STAR format\*\* (Situation → Task → Action → Result) for behavioural questions

\- Always quantify impact: \*"reduced load time by 40%"\* beats \*"made it faster"\*

\- It's okay to take 30 seconds to think before answering

\- Ask clarifying questions — interviewers reward curiosity

\### 🔗 Useful Resources

\- \[Grokking the System Design Interview](https://www.educative.io/courses/grokking-the-system-design-interview)

\- \[NeetCode Roadmap](https://neetcode.io/roadmap)

\- \[Tech Interview Handbook](https://www.techinterviewhandbook.org/)

\- \[Pramp — Free Mock Interviews](https://www.pramp.com/)

"""

\# ── Custom CSS ─────────────────────────────────────────────────────────────────

CUSTOM_CSS = """

@import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700\&display=swap');

\* { font-family: 'Google Sans', 'Product Sans', sans-serif !important; }

.gr-button-primary {

&#x20; background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;

&#x20; border: none !important;

&#x20; color: white !important;

&#x20; font-weight: 600 !important;

&#x20; transition: transform 0.15s, box-shadow 0.15s !important;

}

.gr-button-primary:hover {

&#x20; transform: translateY(-2px) !important;

&#x20; box-shadow: 0 6px 20px rgba(99,102,241,0.4) !important;

}

.gr-button-secondary {

&#x20; border: 2px solid #6366f1 !important;

&#x20; color: #6366f1 !important;

&#x20; font-weight: 600 !important;

&#x20; transition: all 0.15s !important;

}

.gr-button-secondary:hover {

&#x20; background: #6366f1 !important;

&#x20; color: white !important;

}

\#progress_box textarea {

&#x20; font-weight: 700 !important;

&#x20; font-size: 1rem !important;

&#x20; color: #6366f1 !important;

&#x20; text-align: center !important;

}

\#feedback_box textarea {

&#x20; font-size: 0.95rem !important;

&#x20; line-height: 1.6 !important;

}

.tab-nav button { font-weight: 600 !important; }

/\* ── Animated blob background ── \*/

body {

&#x20; background: #0d0d1f !important;

}

gradio-app {

&#x20; background: transparent !important;

}

.gradio-container {

&#x20; background: transparent !important;

}

"""

\# ── Build UI ───────────────────────────────────────────────────────────────────

with gr.Blocks(

&#x20; title="AI Interview Coach",

&#x20; theme=gr.themes.Soft(

&#x20; primary_hue=gr.themes.colors.violet,

&#x20; secondary_hue=gr.themes.colors.purple,

&#x20; neutral_hue=gr.themes.colors.slate,

&#x20; font=\[gr.themes.GoogleFont("Google Sans"), "ui-sans-serif", "sans-serif"],

&#x20; ),

&#x20; css=CUSTOM_CSS

) as demo:

&#x20; # Load history from disk on startup

&#x20; history_state = gr.State(load_history())

&#x20; q_index = gr.State("0")

&#x20; gr.HTML("""

&#x20; `<div style="text-align:center; padding: 1.8rem 0 0.8rem;">`

&#x20; <h1 style="font-size:2.2rem; font-weight:800; margin:0; font-size: 2.2rem;

&#x20; background: linear-gradient(135deg,#6366f1,#a78bfa);

&#x20; -webkit-background-clip:text; -webkit-text-fill-color:transparent;">

&#x20; AI Interview Coach

&#x20; `</h1>`

&#x20; `<p style="color:#64748b; margin-top:0.4rem; font-size:1rem;">`

&#x20; `<b>`Practice · Get Feedback · Improve `</b><br>`

&#x20; `<span style="font-size:0.8rem; color:#808080;">`Powered by `<span style="color:#f97316; font-weight:600;">`Mistral 7B

&#x20; `</p>`

&#x20; `</div>`

&#x20; """)

&#x20; gr.HTML("""

&#x20; `<style>`

&#x20; @keyframes floatBlob1 {

&#x20; 0% { transform: translate(0px, 0px); }

&#x20; 33% { transform: translate(-30px, -40px); }

&#x20; 66% { transform: translate(40px, -20px); }

&#x20; 100% { transform: translate(0px, 0px); }

&#x20; }

&#x20; @keyframes floatBlob2 {

&#x20; 0% { transform: translate(0px, 0px); }

&#x20; 33% { transform: translate(50px, 30px); }

&#x20; 66% { transform: translate(-30px, 50px); }

&#x20; 100% { transform: translate(0px, 0px); }

&#x20; }

&#x20; @keyframes floatBlob3 {

&#x20; 0% { transform: translate(0px, 0px); }

&#x20; 33% { transform: translate(-40px, 50px); }

&#x20; 66% { transform: translate(30px, -40px); }

&#x20; 100% { transform: translate(0px, 0px); }

&#x20; }

&#x20; `</style>`

&#x20; <div style="

&#x20; position: fixed; width: 400px; height: 300px;

&#x20; border-radius: 50%; background: #6366f1;

&#x20; filter: blur(80px); opacity: 0.35;

&#x20; top: -100px; left: -100px;

&#x20; z-index: 0; pointer-events: none;

&#x20; animation: floatBlob1 20s ease-in-out infinite;

&#x20; ">`</div>`

&#x20; <div style="

&#x20; position: fixed; width: 500px; height: 400px;

&#x20; border-radius: 50%; background: #8b5cf6;

&#x20; filter: blur(100px); opacity: 0.25;

&#x20; top: 50%; right: -200px;

&#x20; z-index: 0; pointer-events: none;

&#x20; animation: floatBlob2 25s ease-in-out infinite;

&#x20; ">`</div>`

&#x20; <div style="

&#x20; position: fixed; width: 600px; height: 350px;

&#x20; border-radius: 50%; background: #f97316;

&#x20; filter: blur(90px); opacity: 0.2;

&#x20; bottom: -100px; left: 100px;

&#x20; z-index: 0; pointer-events: none;

&#x20; animation: floatBlob3 15s ease-in-out infinite;

&#x20; ">`</div>`

&#x20; """)

&#x20; with gr.Tabs():

&#x20; # ── Tab 1: Practice ───────────────────────────────────────────────────

&#x20; with gr.Tab("🎯 Practice"):

&#x20; with gr.Row():

&#x20; with gr.Column(scale=1):

&#x20; gr.Markdown("### 📋 Step 1 — Paste the Job Description")

&#x20; job_desc_box = gr.Textbox(

&#x20; label="Job Description",

&#x20; lines=6,

&#x20; placeholder="Paste from LinkedIn, company careers page, etc.",

&#x20; )

&#x20; start_btn = gr.Button("🚀 Start Interview", variant="primary", size="lg")

&#x20; with gr.Column(scale=1):

&#x20; gr.Markdown("### 💬 Step 2 — Answer Questions")

&#x20; progress_box = gr.Textbox(

&#x20; label="Progress",

&#x20; value="Ready to start",

&#x20; interactive=False,

&#x20; elem_id="progress_box",

&#x20; )

&#x20; question_box = gr.Textbox(

&#x20; label="Interview Question",

&#x20; lines=3,

&#x20; interactive=False,

&#x20; )

&#x20; answer_box = gr.Textbox(

&#x20; label="Your Answer",

&#x20; lines=5,

&#x20; placeholder="Be specific — use the STAR format (Situation, Task, Action, Result).",

&#x20; )

&#x20; with gr.Row():

&#x20; feedback_btn = gr.Button("📊 Get Feedback", variant="primary")

&#x20; next_btn = gr.Button("➡️ Next Question", variant="secondary")

&#x20; # ── Previous answer review panel ──────────────────────────────────

&#x20; with gr.Accordion("🔁 Previous Question Review", open=False) as prev_accordion:

&#x20; with gr.Row():

&#x20; prev_question_box = gr.Textbox(

&#x20; label="Previous Question",

&#x20; interactive=False,

&#x20; lines=2,

&#x20; placeholder="Will show the last question after you click Next Question...",

&#x20; )

&#x20; prev_answer_box = gr.Textbox(

&#x20; label="Your Previous Answer",

&#x20; interactive=False,

&#x20; lines=3,

&#x20; placeholder="Will show your last answer here...",

&#x20; )

&#x20; # ── Full session log accordion ─────────────────────────────────────

&#x20; with gr.Accordion("📋 This Session's Log", open=False):

&#x20; session_log_display = gr.Markdown("Complete questions to see your session log here.")

&#x20; gr.Markdown("### 🏆 Step 3 — Coach Feedback")

&#x20; feedback_box = gr.Textbox(

&#x20; label="AI Coach Feedback",

&#x20; interactive=False,

&#x20; lines=7,

&#x20; elem_id="feedback_box",

&#x20; )

&#x20; # ── Tab 2: History ────────────────────────────────────────────────────

&#x20; with gr.Tab("📈 History \& Progress"):

&#x20; gr.Markdown("""

&#x20; ### Your Interview Sessions

&#x20; History is \*\*saved to disk\*\* — persists across restarts! 💾

&#x20; """)

&#x20; with gr.Row():

&#x20; refresh_btn = gr.Button("🔄 Refresh History", variant="secondary")

&#x20; clear_btn = gr.Button("🗑️ Clear History", variant="secondary")

&#x20; history_display = gr.Markdown(

&#x20; render_history(load_history()) # Load from disk on startup

&#x20; )

&#x20; # ── Tab 3: Tips ───────────────────────────────────────────────────────

&#x20; with gr.Tab("💡 Tips \& Resources"):

&#x20; tips_display = gr.Markdown(build_tips())

&#x20; # ── Wire up events ─────────────────────────────────────────────────────────

&#x20; start_btn.click(

&#x20; fn=generate_all_questions,

&#x20; inputs=\[job_desc_box, history_state],

&#x20; outputs=\[question_box, q_index, progress_box, history_state, tips_display],

&#x20; ).then(

&#x20; fn=render_history,

&#x20; inputs=\[history_state],

&#x20; outputs=\[history_display],

&#x20; )

&#x20; feedback_btn.click(

&#x20; fn=score_answer,

&#x20; inputs=\[answer_box, q_index, history_state],

&#x20; outputs=\[feedback_box, history_state],

&#x20; ).then(

&#x20; fn=render_history,

&#x20; inputs=\[history_state],

&#x20; outputs=\[history_display],

&#x20; )

&#x20; next_btn.click(

&#x20; fn=next_question,

&#x20; inputs=\[q_index, answer_box, history_state],

&#x20; outputs=\[question_box, answer_box, q_index, progress_box, history_state, prev_question_box, prev_answer_box, session_log_display],

&#x20; )

&#x20; refresh_btn.click(

&#x20; fn=render_history,

&#x20; inputs=\[history_state],

&#x20; outputs=\[history_display],

&#x20; )

&#x20; def clear_history(history_state):

&#x20; """Clear all history"""

&#x20; if os.path.exists(HISTORY_FILE):

&#x20; os.remove(HISTORY_FILE)

&#x20; return \[], "History cleared! Start a new interview above."

&#x20; clear_btn.click(

&#x20; fn=clear_history,

&#x20; inputs=\[history_state],

&#x20; outputs=\[history_state, history_display],

&#x20; )

demo.launch(share = True)
