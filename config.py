OLLAMA_URL = "http://localhost:11434/api/generate"
HISTORY_FILE = "interview_history.json"

QUESTION_PROMPTS = [
    "Generate ONE interview question about the candidate's most recent project experience. Question:",
    "Generate ONE follow-up interview question about the specific technologies or tools used. Question:",
    "Generate ONE interview question about a challenge they faced and how they overcame it. Question:",
]

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
