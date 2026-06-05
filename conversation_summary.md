# AI Interview Coach - Session Handoff Summary

This document captures the current architecture, styling status, and immediate roadmap of the AI Interview Coach project for the next chat session.

## 1. Project Directory & Git Status
*   **Active Branch:** `feature/job-analyzer-pipeline` (all changes committed and pushed upstream).
*   **Repository Path:** `c:\Users\ishan\OneDrive\Desktop\HF_Hackathon`

---

## 2. Architectural Code Split (Refactored)
To make the codebase professional and maintainable, the monolithic `interview_coach.py` was refactored and split into three modular files:
1.  **`config.py`**: Holds static configuration settings, prompt definitions, CSS styles, and resources databases:
    *   `OLLAMA_URL` (local model API endpoint)
    *   `HISTORY_FILE` (`interview_history.json` path)
    *   `QUESTION_PROMPTS` & `TIPS_DB`/`DEFAULT_TIPS`
    *   `CUSTOM_CSS`
2.  **`engine.py`**: Houses all backend processing, database transactions, helper functions, and LLM utilities:
    *   `load_history()` & `save_history()`
    *   `ask_ollama()`, `clean_question()`, `generate_all_questions()`, `score_answer()`
    *   `next_question()`, `render_session_log()`, `compute_stats()`, `render_history()`, `build_tips()`
3.  **`interview_coach.py`**: Contains only the core UI layout (`gr.Blocks`), HTML content, animated blob setups, and event listeners (`.click()`), cleanly importing configurations and functions from `config.py` and `engine.py`.

---

## 3. UI, Theming, and Styling Status
*   **Active Theme:** Dark mode base (`body { background: #0d0d1f }`) with Google Sans typography.
*   **Background Blobs:** 3 animated gradient blobs (`#6366f1`, `#8b5cf6`, `#f97316`) that drift using CSS keyframes. 
*   **Gradio Transparency:** Custom CSS makes `.gradio-container` and `gradio-app` transparent so the background blobs display cleanly through the layers.
*   **Light Mode Note:** We experimented with a minimalist light/white theme but rolled back to the dark mode because standard Gradio text elements lost visibility. The styling remains on the darker theme with soft glowing blobs.
*   **Public Sharing:** Ready to run publicly via `demo.launch(share=True)`.

---

## 4. Immediate Next Steps & Hackathon Roadmap
1.  **Add Custom Text Analytics (Upskilling Showcase):** 
    *   Integrate a custom analysis function in `engine.py` (e.g., using pure Python or NLP tools) to measure candidate answer metrics like **vocabulary diversity**, **word count checks**, or **targeted keyword frequency matching** before/alongside LLM feedback.
2.  **Enhance Coaching Output:** 
    *   Render LLM evaluation details (Scores, Strengths, Weaknesses, Fixes) into dedicated structured UI components instead of a raw text block.
