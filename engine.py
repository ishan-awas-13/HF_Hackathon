import gradio as gr
import requests
import json
import datetime
import os
from config import *

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
