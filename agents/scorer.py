"""
agents/scorer.py
────────────────────────────────────────────────────────────────────────────
ScorerAgent: Keyword-aware answer scoring — implements Agenda Item #4.

The core innovation over Phase 1:
  1. LOCAL keyword hit check (instant, deterministic, no LLM call needed)
     - Checks which expected job keywords appear in the candidate's answer
     - Computes coverage_pct = hits / total_keywords * 100
  2. LLM scoring prompt is dynamically AUGMENTED with:
     - The keyword coverage result
     - An explicit cap instruction if coverage < 40%
     - A list of missed keywords to guide the Weakness/Fix feedback
  3. Returns a structured dict with raw feedback AND parsed fields
     for the UI to render keyword coverage badges.

Scoring rubric enforced by prompt:
  - STAR format structure (encouraged, not hard-gated)
  - Keyword coverage (hard gate: <40% → score capped at 5/10)
  - Relevance check (irrelevant responses → NIL/10)
"""


class ScorerAgent:
    """
    Scores a candidate's interview answer against job-profile expectations.
    
    Usage:
        agent = ScorerAgent(llm_fn)
        result = agent.run(answer, question, job_profile)
        # result: {
        #   "raw_feedback": str,       # Full LLM output for display
        #   "score_str": str,          # e.g. "7/10" or "NIL/10"
        #   "numeric_score": float,    # e.g. 7.0 or None
        #   "hit_keywords": list,      # keywords found in answer
        #   "missed_keywords": list,   # keywords not found
        #   "coverage_pct": float,     # 0.0 – 100.0
        #   "star_hint": bool,         # True if answer has weak STAR structure
        # }
    """

    _MIN_ANSWER_LEN = 15
    _COVERAGE_THRESHOLD = 40.0  # % — below this, score is capped at 5

    def __init__(self, llm_fn):
        """
        Args:
            llm_fn: Callable (prompt: str, temperature: float, max_tokens: int) → str
        """
        self._ask = llm_fn

    # ── Public entry point ────────────────────────────────────────────────────
    def run(self, answer: str, question: str, job_profile: dict) -> dict:
        """
        Score the candidate's answer.

        Args:
            answer: The candidate's raw answer text.
            question: The interview question that was asked.
            job_profile: Dict from ValidatorAgent with 'keywords', 'industry', etc.

        Returns:
            Structured result dict (see class docstring).
        """
        if not answer or len(answer.strip()) < self._MIN_ANSWER_LEN:
            return self._short_answer_result()

        keywords    = job_profile.get("keywords", [])
        industry    = job_profile.get("industry", "General")
        role_level  = job_profile.get("role_level", "Mid-Level")
        answer_clip = answer.strip()[:600]

        # ── Step 1: Local keyword coverage check (no LLM) ────────────────────
        answer_lower    = answer_clip.lower()
        hit_keywords    = [k for k in keywords if k.lower() in answer_lower]
        missed_keywords = [k for k in keywords if k.lower() not in answer_lower]
        coverage_pct    = (len(hit_keywords) / len(keywords) * 100) if keywords else 100.0

        # ── Step 2: STAR structure heuristic (fast check) ────────────────────
        star_words = ["situation", "task", "action", "result", "outcome", "challenge", "i did", "i then", "as a result"]
        star_hint  = sum(1 for w in star_words if w in answer_lower) < 2

        # ── Step 3: Build augmented LLM scoring prompt ───────────────────────
        prompt = self._build_prompt(
            answer_clip, question, industry, role_level,
            keywords, hit_keywords, missed_keywords, coverage_pct
        )

        raw_feedback = self._ask(prompt, temperature=0.45, max_tokens=300)

        # ── Step 4: Parse the structured LLM response ────────────────────────
        score_str, numeric = self._parse_score(raw_feedback)

        return {
            "raw_feedback":   raw_feedback,
            "score_str":      score_str,
            "numeric_score":  numeric,
            "hit_keywords":   hit_keywords,
            "missed_keywords": missed_keywords,
            "coverage_pct":   round(coverage_pct, 1),
            "star_hint":      star_hint,
        }

    # ── Prompt builder ────────────────────────────────────────────────────────
    def _build_prompt(self, answer: str, question: str, industry: str,
                      role_level: str, all_kw: list, hit_kw: list,
                      missed_kw: list, coverage_pct: float) -> str:

        cap_instruction = ""
        if coverage_pct < self._COVERAGE_THRESHOLD and all_kw:
            cap_instruction = (
                f"\nIMPORTANT: The keyword coverage is only {coverage_pct:.0f}% "
                f"({len(hit_kw)}/{len(all_kw)} expected terms found). "
                f"You MUST cap the score at 5/10 or lower due to insufficient use of required terminology."
            )

        missed_str = ", ".join(missed_kw) if missed_kw else "None — great coverage!"
        hit_str    = ", ".join(hit_kw)    if hit_kw    else "None"

        return f"""[INST] You are a strict interview coach evaluating a candidate's answer for a {role_level} {industry} position.

Interview Question Asked:
{question}

Candidate's Answer:
{answer}

--- KEYWORD ANALYSIS (pre-computed, use this in your evaluation) ---
Expected industry keywords: {", ".join(all_kw)}
Keywords FOUND in answer: {hit_str}
Keywords MISSING from answer: {missed_str}
Keyword coverage: {coverage_pct:.0f}%
{cap_instruction}
--- END KEYWORD ANALYSIS ---

STEP 1 — Relevance Check:
Is this a genuine attempt at answering the interview question?
It is NOT relevant if it is: random text, code, gibberish, a single word, copy-pasted content, or completely off-topic.

STEP 2 — Respond with EXACTLY this format and nothing else:

If NOT relevant:
Relevant: NO
Score: NIL/10
Warning: ⚠️ Irrelevant response detected. Please answer the interview question properly.

If relevant, use ALL of these lines:
Relevant: YES
Score: X/10
Strength: (one sentence about what was done well — be specific)
Weakness: (one sentence about the biggest gap — mention missing keywords if relevant)
Fix: (one specific, actionable improvement — no code samples)
Keyword Coverage: {len(hit_kw)}/{len(all_kw)} expected terms used [/INST]"""

    # ── Parsers ───────────────────────────────────────────────────────────────
    @staticmethod
    def _parse_score(feedback: str) -> tuple[str, float | None]:
        """Extract 'X/10' or 'NIL/10' and its numeric value from feedback."""
        for line in feedback.splitlines():
            if line.strip().startswith("Score:"):
                score_str = line.replace("Score:", "").strip()
                try:
                    numeric = float(score_str.split("/")[0].strip())
                    return score_str, numeric
                except (ValueError, IndexError):
                    return score_str, None
        return "", None

    @staticmethod
    def _short_answer_result() -> dict:
        return {
            "raw_feedback":   "Please write a more detailed answer (at least 15 characters).",
            "score_str":      "",
            "numeric_score":  None,
            "hit_keywords":   [],
            "missed_keywords": [],
            "coverage_pct":   0.0,
            "star_hint":      True,
        }
