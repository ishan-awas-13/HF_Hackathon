"""
agents/question_gen.py
────────────────────────────────────────────────────────────────────────────
QuestionGenAgent: Generates N adaptive interview questions from a job profile.

- Uses the validated job profile (industry, role_level, keywords, interview_style)
  to craft highly specific questions — NOT generic ones.
- Selects and fills QUESTION_PROMPT_TEMPLATES from config.py dynamically.
- Applies light post-processing to clean up the LLM output.
- Number of questions is determined by the user's selected interview mode (3, 5, or 7).
"""

import re
from config import QUESTION_PROMPT_TEMPLATES


class QuestionGenAgent:
    """
    Generates a list of interview questions tailored to a specific job profile.
    
    Usage:
        agent = QuestionGenAgent(llm_fn)
        questions = agent.run(job_profile, job_desc, n_questions=5)
        # returns: ["Q1 text", "Q2 text", ..., "Q5 text"]
    """

    def __init__(self, llm_fn):
        """
        Args:
            llm_fn: Callable (prompt: str, temperature: float, max_tokens: int) → str
        """
        self._ask = llm_fn

    # ── Public entry point ────────────────────────────────────────────────────
    def run(self, job_profile: dict, job_desc: str, n_questions: int = 3) -> list[str]:
        """
        Generate n_questions tailored interview questions.

        Args:
            job_profile: Dict from ValidatorAgent containing industry, role_level,
                         keywords, interview_style.
            job_desc: Original job description text (used for context injection).
            n_questions: Number of questions to generate (3, 5, or 7).

        Returns:
            List of n_questions question strings.
        """
        industry  = job_profile.get("industry", "General")
        level     = job_profile.get("role_level", "Mid-Level")
        keywords  = ", ".join(job_profile.get("keywords", []))
        style     = job_profile.get("interview_style", "Mixed")
        jd_ctx    = job_desc[:600]  # Context window for the LLM

        # Select templates: cycle through if n > len(templates)
        templates = QUESTION_PROMPT_TEMPLATES[:n_questions]

        questions = []
        for template in templates:
            prompt = self._build_prompt(template, industry, level, keywords, style, jd_ctx)
            raw_q = self._ask(prompt, temperature=0.85, max_tokens=150)
            clean_q = self._clean(raw_q)
            if clean_q:
                questions.append(clean_q)

        # If LLM returned empty/bad responses, fill with fallbacks
        while len(questions) < n_questions:
            fallback_prompt = self._fallback_prompt(industry, level, keywords, len(questions) + 1)
            raw_q = self._ask(fallback_prompt, temperature=0.7, max_tokens=120)
            questions.append(self._clean(raw_q) or f"Tell me about your experience relevant to {industry}.")

        return questions[:n_questions]

    # ── Prompt builder ────────────────────────────────────────────────────────
    def _build_prompt(self, template: str, industry: str, level: str,
                      keywords: str, style: str, jd_ctx: str) -> str:
        """Fill in the question template with job profile context."""
        filled_template = template.format(
            industry=industry,
            role_level=level,
            keywords=keywords,
        )
        return f"""[INST] You are an experienced technical interviewer conducting a {style} interview for a {level} {industry} position.

Job Context:
{jd_ctx}

Key skills expected: {keywords}

{filled_template}

Important: Generate exactly ONE clear, specific interview question. Do not include any preamble or explanation. End with a question mark. [/INST]"""

    def _fallback_prompt(self, industry: str, level: str, keywords: str, q_num: int) -> str:
        return f"""[INST] Generate interview question #{q_num} for a {level} {industry} candidate. Focus on: {keywords}. One question only, ending with a question mark. [/INST]"""

    # ── Output cleaning ───────────────────────────────────────────────────────
    @staticmethod
    def _clean(raw: str) -> str:
        """
        Strip LLM artefacts and extract the first clean question.
        Handles: 'Question:', numbering, quotes, '[INST]' leftovers.
        """
        if not raw:
            return ""

        # Remove common prefixes
        for prefix in ["Question:", "Q:", "[INST]", "[/INST]", "Answer:", "Interview Question:"]:
            raw = raw.replace(prefix, "")

        # Remove leading numbering like "1." or "1)"
        raw = re.sub(r"^\s*\d+[\.\)]\s*", "", raw.strip())

        # Take only the first sentence ending with a question mark
        if "?" in raw:
            raw = raw.split("?")[0].strip() + "?"

        # Remove surrounding quotes
        raw = raw.strip('"\'')

        return raw.strip()
