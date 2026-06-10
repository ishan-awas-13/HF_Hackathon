# AI Interview Coach — Session Handoff Summary (June 11, 2026)

## 1. Project Overview

An **AI-powered Interview Coach** built with **Gradio + Ollama (Mistral 7B)**. The user pastes a job description, the app validates it, generates tailored interview questions, scores the candidate's answers using LLM-based evaluation, and produces a downloadable PDF report of the session.

**GitHub Repo:** `ishan-awas-13/HF_Hackathon`
**Active Branch:** `Primarily-Vibe-Coded` (branched from `feature/job-analyzer-pipeline`)

---

## 2. Architecture (3-File Modular Design)

| File | Role | Lines |
|---|---|---|
| `config.py` (104 lines) | All static config: `OLLAMA_URL`, `HISTORY_FILE`, `QUESTION_PROMPTS`, `TIPS_DB`, `DEFAULT_TIPS`, `CUSTOM_CSS` |
| `engine.py` (632 lines) | All backend logic: Ollama API calls, job description validation pipeline, question generation, answer scoring, history persistence, PDF report generation |
| `interview_coach.py` (247 lines) | Pure Gradio UI layer: layout, state management, event wiring. Imports everything from `config` and `engine` via `from config import *` / `from engine import *` |

---

## 3. Key Features & Their Implementation

### 3.1 Security Pipeline (`engine.py` → `analyze_and_validate_job`)
Two-stage job description validation:
1. **Programmatic filter:** Rejects inputs < 350 characters.
2. **LLM guardrail:** A temperature=0.0 prompt that classifies input as `VALID` or `INVALID` to prevent prompt injection.

After validation, the LLM extracts `<INDUSTRY>`, `<KEYWORDS>`, and `<TIPS>` XML tags from the job description to personalize the session.

### 3.2 PDF Report Generation (`engine.py` → `generate_pdf_report`)
- Uses **ReportLab** (`reportlab` package, v4.5.1 installed in `.venv`).
- Imports: `SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak` from `reportlab.platypus`.
- Generates `Interview_Session_Report.pdf` with:
  - Professional styled title, section headers, body text.
  - Metadata table (date, job snippet).
  - Color-coded score badges (green ≥8, orange ≥5, red <5).
  - Per-question breakdown: question text, candidate answer, AI score.
  - Summary & Recommendations section with dynamic coaching text.
  - Page breaks between sessions.
- **UI integration:** "📈 History & PDF Report" tab contains a `gr.Button("📥 Generate PDF Report")` wired to `generate_pdf_report`, outputting to a `gr.File` component for browser download.

### 3.3 Current-Session-Only History
- `generate_all_questions` resets history on every new interview start:
  ```python
  history_state = [session]  # Overwrites, does NOT append
  save_history(history_state)
  ```
- Each new interview session is completely independent — no data carries over from previous sessions.
- The PDF report and history preview reflect only the current/latest session.

### 3.4 Robust History Loading (`engine.py` → `load_history`)
- Protected against `JSONDecodeError` when `interview_history.json` is empty or corrupted:
  ```python
  try:
      content = f.read().strip()
      if not content:
          return []
      return json.loads(content)
  except json.JSONDecodeError:
      return []
  ```

### 3.5 Gradio 6.0 Compatibility Fix
- `theme` and `css` parameters moved from `gr.Blocks()` constructor to `demo.launch()`:
  ```python
  with gr.Blocks(title="AI Interview Coach") as demo:
      ...
  custom_theme = gr.themes.Soft(
      primary_hue=gr.themes.colors.violet,
      ...
  )
  demo.launch(theme=custom_theme, css=CUSTOM_CSS)
  ```

---

## 4. UI Layout (3 Tabs)

### Tab 1: 🎯 Practice
- **Left column:** Job description input + "Start Interview" button.
- **Right column:** Progress indicator, question display, answer input, "Get Feedback" & "Next Question" buttons.
- **Accordions:** "Previous Question Review" and "This Session's Log".
- **Feedback box:** Displays AI coach scoring output.

### Tab 2: 📈 History & PDF Report
- "📥 Generate PDF Report" button → `gr.File` download component.
- "🔄 Refresh Preview" and "🗑️ Clear History" buttons.
- Markdown-rendered quick progress history below a separator.

### Tab 3: 💡 Tips & Resources
- Dynamically populated based on validated job description profile (industry, keywords, tips extracted by LLM).

---

## 5. Visual Design
- **Dark theme:** `body { background: #0d0d1f }` with transparent Gradio containers.
- **Animated blobs:** 4 fixed `div` elements with CSS `@keyframes` float animations (violet, purple, orange, pink).
- **Gradient buttons:** Primary buttons use `linear-gradient(135deg, #6366f1, #8b5cf6)` with hover lift effect.
- **Typography:** Google Sans font via CSS import.

---

## 6. Environment & Dependencies
- **Python:** 3.12
- **Virtual env:** `.venv` in project root
- **Key packages:** `gradio` (v6.x), `requests`, `reportlab` (v4.5.1)
- **LLM Backend:** Ollama running locally at `http://localhost:11434/api/generate`, model `mistral:7b`
- **Persistence:** `interview_history.json` (JSON file, reset per session)

---

## 7. Git Branch Structure
| Branch | Purpose |
|---|---|
| `main` | Original stable version |
| `history-and-tips` | Added history & tips features |
| `multi-question-version` | Multi-question interview flow |
| `feature/job-analyzer-pipeline` | Modularized architecture + security pipeline + PDF |
| `Primarily-Vibe-Coded` | **ACTIVE** — Current development branch for agent-driven refinements |

---

## 8. Project Agenda (from `Project_Agenda.md`)
1. ✅ Bulletproof prompts — security validation pipeline implemented.
2. ✅ Fix Tips section — dynamically generated from LLM-parsed job description.
3. ✅ Fix History Section — replaced with PDF download option.
4. ⬜ Make response grading flexible — keyword-based scoring (partially implemented via `keywords` extraction, needs scoring integration).
5. ⬜ Support more job types — industry detection implemented, but broader flexibility can be enhanced.

---

## 9. Known Issues & Next Steps
- **Keyword-based scoring:** The `job_profile_state` extracts keywords from the job description but `score_answer` does not yet use them to influence the score. This is Agenda Item #4.
- **STAR format enforcement:** The scoring prompt mentions STAR but doesn't programmatically verify structure.
- **PDF filename:** Currently hardcoded as `Interview_Session_Report.pdf` — could be timestamped for uniqueness.
- **Deployment:** Currently local-only. For Hugging Face Spaces deployment, would need to swap Ollama for an API-based model (e.g., HF Inference API).
