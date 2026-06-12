# ── LLM Backend ──────────────────────────────────────────────────────────────
# Currently configured for LOCAL development using Ollama (mistral:7b).
# Before HF Spaces deployment: swap this block for the HF InferenceClient
# block that is saved in .env.example / README.md.
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "mistral:7b"

# ── Persistence ──────────────────────────────────────────────────────────────
# Session is runtime-only. History JSON is written per-session and read for PDF.
HISTORY_FILE = "interview_history.json"

# ── Interview Modes ───────────────────────────────────────────────────────────
INTERVIEW_MODES = {
    "⚡ Quick (3 Questions)": 3,
    "📋 Standard (5 Questions)": 5,
    "🔬 Deep Dive (7 Questions)    ": 7,
}

# ── Question Prompt Templates ─────────────────────────────────────────────────
# These are injected into the QuestionGenAgent with the job profile context.
# The agent fills in {industry}, {role_level}, {keywords} dynamically.
QUESTION_PROMPT_TEMPLATES = [
    "Generate ONE interview question asking the candidate to describe their most relevant project experience for a {role_level} {industry} role. Focus on: {keywords}. Question:",
    "Generate ONE behavioral interview question about how the candidate handles challenges, relevant to {industry}. Question:",
    "Generate ONE technical or domain-specific question that tests knowledge of {keywords} in a {industry} context. Question:",
    "Generate ONE question asking the candidate about their approach to collaboration, communication, or leadership relevant to a {role_level} role. Question:",
    "Generate ONE situational interview question: 'What would you do if...' relevant to {industry} and {keywords}. Question:",
    "Generate ONE question about the candidate's long-term career goals and how this {industry} role aligns with them. Question:",
    "Generate ONE challenging follow-up question that digs deeper into technical expertise or past achievements relevant to {keywords}. Question:",
]

# ── Default Tips (fallback only — AI-generated tips take priority) ─────────────
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
    "label": "General / Professional",
    "leetcode": [
        ("Two Sum", "https://leetcode.com/problems/two-sum/", "Easy"),
        ("Merge Intervals", "https://leetcode.com/problems/merge-intervals/", "Medium"),
        ("Trapping Rain Water", "https://leetcode.com/problems/trapping-rain-water/", "Hard"),
    ],
    "concepts": ["STAR answer format", "System design basics", "Time & space complexity", "Behavioural questions"],
}

# ── CSS Design System ─────────────────────────────────────────────────────────
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Reset & Base ── */
* { font-family: 'Inter', ui-sans-serif, system-ui, sans-serif !important; box-sizing: border-box; }

/* ── Root color tokens (our design system) ── */
/* ── ALSO overrides Gradio's internal CSS variables so the loading overlay  ── */
/* ── stays dark. The white box during processing comes from                 ── */
/* ── var(--block-background-fill) defaulting to white in the Soft theme.   ── */
:root {
    /* Our tokens */
    --indigo:    #6366f1;
    --violet:    #8b5cf6;
    --indigo-glow: rgba(99,102,241,0.35);
    --violet-glow: rgba(139,92,246,0.25);
    --surface:   rgba(15,15,35,0.6);
    --border:    rgba(99,102,241,0.18);
    --text-muted: #94a3b8;
    --text-dim:   #64748b;

    /* Gradio's internal variables — override to prevent white loading overlay */
    --block-background-fill:     rgba(8,8,28,0.85);
    --input-background-fill:     rgba(8,8,28,0.85);
    --background-fill-primary:   #080818;
    --background-fill-secondary: rgba(15,15,35,0.7);
    --body-background-fill:      #080818;
    --border-color-primary:      rgba(99,102,241,0.18);
    --body-text-color:           #e2e8f0;
    --body-text-color-subdued:   #94a3b8;
    --loader-color:              #6366f1;
    --block-border-color:        rgba(99,102,241,0.18);
    --input-border-color:        rgba(99,102,241,0.18);
}

/* ── Background ── */
body { background: #080818 !important; }
gradio-app { background: transparent !important; }
.gradio-container { background: transparent !important; width: 100% !important; max-width: none !important; margin: 0 auto !important; padding: 0 20px !important; }

/* ── Make the blob background wrapper invisible (blobs are position:fixed, they float fine) ── */
#bg-blobs {
    background: none !important;
    border: none !important;
    backdrop-filter: none !important;
    padding: 0 !important;
    margin: 0 !important;
    overflow: visible !important;
    min-height: 0 !important;
    height: 0 !important;
    pointer-events: none !important;
}
/* ── Make the header wrapper borderless/transparent ── */
#app-header {
    background: none !important;
    border: none !important;
    backdrop-filter: none !important;
    padding: 0 !important;
    margin: 0 !important;
}

/* ── Glass panels ── */
.gr-panel, .gr-box, .svelte-panel, .block, .form {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    backdrop-filter: blur(12px) !important;
    border-radius: 14px !important;
}

/* ── Tab nav ── */
.tab-nav { border-bottom: 1px solid var(--border) !important; }
.tab-nav button {
    font-weight: 600 !important;
    color: var(--text-muted) !important;
    padding: 0.6rem 1.2rem !important;
    border-radius: 8px 8px 0 0 !important;
    transition: all 0.2s !important;
}
.tab-nav button.selected {
    color: var(--indigo) !important;
    border-bottom: 2px solid var(--indigo) !important;
    background: rgba(99,102,241,0.08) !important;
}

/* ── Primary buttons ── */
.gr-button-primary, button[variant="primary"], .primary-btn {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 0.6rem 1.4rem !important;
    border-radius: 10px !important;
    cursor: pointer !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease !important;
    box-shadow: 0 0 0 rgba(99,102,241,0) !important;
}
.gr-button-primary:hover, button[variant="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(99,102,241,0.45) !important;
}
.gr-button-primary:active, button[variant="primary"]:active {
    transform: translateY(0px) !important;
}

/* ── Secondary buttons ── */
.gr-button-secondary, button[variant="secondary"] {
    border: 1.5px solid var(--indigo) !important;
    color: var(--indigo) !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    background: transparent !important;
    transition: all 0.15s !important;
}
.gr-button-secondary:hover, button[variant="secondary"]:hover {
    background: var(--indigo) !important;
    color: white !important;
}

/* ── Textbox inputs — idle & focus ── */
.gr-textbox textarea, input[type="text"], textarea {
    background: rgba(8,8,28,0.7) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-size: 0.92rem !important;
    padding: 0.65rem 0.9rem !important;
    transition: border-color 0.2s !important;
}
.gr-textbox textarea:focus, textarea:focus {
    border-color: var(--indigo) !important;
    outline: none !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
}

/* ── Textbox inputs — Gradio loading/processing states ── */
/* Gradio adds .generating / .pending to the .wrap container during LLM calls.
   Without these, the dark textarea flips to white during processing. */

/* Target the wrapper container in every loading state */
.wrap.generating, .wrap.pending, .wrap.processing,
.generating .wrap, .pending .wrap, .processing .wrap {
    background: rgba(8,8,28,0.7) !important;
    border-color: var(--indigo) !important;
}

/* Target the textarea itself inside any loading-state wrapper */
.generating textarea, .pending textarea, .processing textarea,
.wrap.generating textarea, .wrap.pending textarea, .wrap.processing textarea,
textarea.generating, textarea.pending {
    background: rgba(8,8,28,0.7) !important;
    color: #e2e8f0 !important;
}

/* The loading overlay div Gradio injects on top of the textarea */
.generating .eta-bar, .generating .progress-bar,
.pending .eta-bar, .pending .progress-bar {
    background: rgba(99,102,241,0.12) !important;
}

/* The small "processing | X.Xs" status text Gradio adds */
.wrap .eta-bar, .eta-bar {
    color: var(--text-muted) !important;
    font-size: 0.78rem !important;
    background: transparent !important;
}

/* The loading spinner icon — keep it indigo, not default grey */
.loader, .generating .loader {
    border-top-color: var(--indigo) !important;
}

/* Gradio 4/5/6 Svelte-generated loading shimmer overlay */
.generating::after, .pending::after {
    background: rgba(8,8,28,0.4) !important;
}

/* ── Labels ── */
label span, .gr-textbox label { color: #cbd5e1 !important; font-weight: 500 !important; font-size: 0.85rem !important; }

/* ── Progress box ── */
#progress_box textarea {
    font-weight: 700 !important;
    font-size: 1rem !important;
    color: var(--indigo) !important;
    text-align: center !important;
    background: rgba(99,102,241,0.08) !important;
    border-color: var(--indigo) !important;
}

/* ── Feedback box ── */
#feedback_box textarea {
    font-size: 0.93rem !important;
    line-height: 1.65 !important;
    color: #cbd5e1 !important;
}

/* ── Markdown text ── */
.gr-markdown, .prose {
    color: #cbd5e1 !important;
}
.gr-markdown h1, .gr-markdown h2, .gr-markdown h3 {
    color: #e2e8f0 !important;
}
.gr-markdown code { 
    background: rgba(99,102,241,0.15) !important; 
    color: #a5b4fc !important; 
    border-radius: 4px !important; 
    padding: 2px 6px !important;
}
.gr-markdown table {
    border-collapse: collapse !important;
    width: 100% !important;
}
.gr-markdown th {
    background: rgba(99,102,241,0.15) !important;
    color: #a5b4fc !important;
    padding: 8px 12px !important;
    font-weight: 600 !important;
}
.gr-markdown td {
    border: 1px solid var(--border) !important;
    padding: 7px 12px !important;
    color: #cbd5e1 !important;
}

/* ── Accordion ── */
.gr-accordion summary {
    color: #a5b4fc !important;
    font-weight: 600 !important;
}

/* ── Radio group (mode selector) ── */
.gr-radio-group label {
    background: rgba(99,102,241,0.06) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    padding: 0.5rem 1rem !important;
    cursor: pointer !important;
    transition: all 0.15s !important;
    color: #94a3b8 !important;
}
.gr-radio-group label:has(input:checked) {
    background: rgba(99,102,241,0.2) !important;
    border-color: var(--indigo) !important;
    color: #a5b4fc !important;
}

/* ── File upload ── */
.gr-file { border: 1px dashed var(--border) !important; border-radius: 10px !important; }

/* ── Scrollbars ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--indigo); border-radius: 3px; }

/* ── Fix for White File Download Row ── */
.gr-file .file-preview, 
.gr-file .file-preview-holder,
.gr-file .file-preview-wrap,
.gr-file tbody tr,
.gr-file table td,
.gr-file .download-link {
    background-color: transparent !important;
    background: transparent !important;
    color: #e2e8f0 !important;
}

/* Add a subtle hover effect for the file row */
.gr-file tbody tr:hover {
    background-color: rgba(99,102,241,0.1) !important;
}

/* Ensure the file name text and size information are readable */
.gr-file tbody td {
    color: #cbd5e1 !important;
    border-color: rgba(99,102,241,0.18) !important;
}

/* Color the download icon to match your purple theme */
.gr-file svg {
    stroke: #8b5cf6 !important;
}

/* ── Gradio footer (settings cog, "Built with Gradio" link) ── */
footer, .gradio-container > footer, .built-with {
    color: var(--text-dim) !important;
}
footer a, .built-with a {
    color: var(--text-muted) !important;
}
footer svg, .built-with svg {
    fill: var(--text-dim) !important;
    stroke: var(--text-dim) !important;
}

/* Remove default borders and backgrounds from columns, rows, and forms to prevent nested double borders */
.gradio-container .vertical,
.gradio-container .row,
.gradio-container .gr-form {
    background: transparent !important;
    border: none !important;
    backdrop-filter: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}

/* Style all step group containers as unified glass panels */
#step-1-group, #step-2-group, #step-3-group, #step-4-group {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    backdrop-filter: blur(10px) !important;
    border-radius: 15px !important;
    padding: 2px !important;
    display: flex !important;
    flex-direction: column !important;
    gap: 1px !important;
    margin-bottom: 5px !important;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2) !important;
}

/* Remove borders, backgrounds, shadows, and extra padding from all nested elements inside the groups to eliminate double-bordering */
#step-1-group div, #step-1-group label,
#step-2-group div,
#step-3-group div, #step-3-group label,
#step-4-group div, #step-4-group label {
    background: transparent !important;
    border: none !important;
    backdrop-filter: none !important;
    box-shadow: none !important;
}

/* Format the inner textareas (Step 1, Step 3, Step 4) to be clean, integrated, and borderless */
#step-1-group textarea,
#step-3-group textarea,
#step-4-group textarea {
    background: rgba(8, 8, 28, 0.7) !important;
    border: 2px solid rgba(99, 102, 241, 0.35) !important;
    border-radius: 8px !important;
    padding: 10px !important;
    box-shadow: none !important;
}

#step-1-group textarea:focus,
#step-3-group textarea:focus,
#step-4-group textarea:focus {
    outline: none !important;
    box-shadow: none !important;
}
/*------------------------------------------------------*/
/* Step-2 Normal (unselected) radio button choices */
#step-2-group label {
    border: 2px solid rgba(99, 102, 241, 0.2) !important; /* Edit normal border width/color here */
    border-radius: 30px !important;
    background: #475569 !important;
    width: 97%;
}

/*Step-2 label Hover settings*/
#step-2-group label:hover {
    border: 2px solid rgba(99, 102, 241, 0.8) !important; /* Edit selected border width/color here */
    background: rgba(99, 102, 241, 0.1) !important;       /* Edit selected background here */
    width: 100%;
    border-radius: 30px !important;
}

/* Step-2 Selected/active radio button choice */
#step-2-group label.selected {
    border: 2px solid rgba(99, 102, 241, 0.8) !important; /* Edit selected border width/color here */
    background: #9333EA !important;       /* Edit selected background here */
    width: 100%;
    border-radius: 30px !important;
}

/*Step-2 Radio button container's border editing.*/
#step-2-group fieldset{
    border: none !important;
    background: tranparent !important;
    box-shadow: none !important;
    backdrop-filter: none !important;    
}

/*Step-3 button formartting*/
/*we edit the row settings as the button render inside a row within the right column*/
#step-3-group .row {
    display: flex !important;
    flex-direction: row !important;     /* Force horizontal layout */
    flex-wrap: nowrap !important;       /* Prevent wrapping/stacking */
    justify-content: center !important; /* Center both buttons */
    margin: 0px auto !important;
    padding: 0px !important;
    gap: 10px !important;
    width: 95% !important;
}


/*Now we get into the button formatting directly*/
#step-3-group button{
    border-radius: 30px !important;
    border: 1px solid rgba(99, 102, 241, 0.2) !important;  
    padding: 5px !important;
    width: 49.5% !important;
    flex: none !important;
}

/* Hover (mouse-over) effect: make the button slightly larger/taller */
#step-3-group button:hover {
    padding: 5px !important;
    background: #191836 !important; /* Slightly stronger purple */
    border: 1px solid rgba(99, 102, 241, 0.8) !important; /* Edit selected border width/color here */
}
/*------------------------------------------------------*/

"""
