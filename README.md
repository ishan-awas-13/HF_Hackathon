# 🎙️ AI Interview Coach — Version Alpha

An AI-powered interview preparation tool built with **Gradio** and **Mistral 7B** via the HuggingFace Inference API.

> Built for the **HuggingFace Hackathon 2026** — Gradio on HF Spaces.

---

## Features

- 🔐 **Two-stage job description validation** — blocks spam and prompt injection
- 🎚️ **3 interview modes** — Quick (3Q), Standard (5Q), Deep Dive (7Q)
- 🤖 **Adaptive questions** — tailored to industry, role level, and detected keywords
- 📊 **Keyword-aware scoring** — answers scored against job-specific expected terms
- 🔑 **Keyword coverage badges** — see exactly which terms you hit and missed
- 💡 **AI-generated Prep Sheet** — works for ANY industry (not just tech)
- 📄 **Timestamped PDF report** — downloadable session summary
- 🎨 **Premium dark UI** — glassmorphism, animated blobs, Inter font

---

## Quick Start (Local)

### 1. Clone and set up environment

```bash
cd HF_Hackathon
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
```

### 2. Set your HuggingFace token

```bash
# Copy the example and fill in your token
copy .env.example .env
# Edit .env and replace hf_PASTE_YOUR_TOKEN_HERE with your actual token
```

Get a free token at: https://huggingface.co/settings/tokens  
Required permission: **Inference** (read)

### 3. Run

```bash
python interview_coach.py
```

Open http://localhost:7860

---

## HuggingFace Spaces Deployment

1. Push this repo to your HF Space (Gradio SDK)
2. Go to **Settings → Secrets** and add `HF_TOKEN` = your token
3. The app starts automatically — no other changes needed

---

## Architecture

```
interview_coach.py   ← Gradio UI (pure layout + event wiring)
engine.py            ← Orchestration (LLM client, session, PDF)
config.py            ← All constants, CSS design system
agents/
  validator.py       ← 3-stage JD validation + profile extraction
  question_gen.py    ← Adaptive question generation
  scorer.py          ← Keyword-aware answer scoring (Agenda #4)
```

---

## Model

- **Model:** `mistralai/Mistral-7B-Instruct-v0.3`
- **Parameters:** 7B (within HF Hackathon ≤32B limit)
- **Inference:** HuggingFace Serverless Inference API (free tier)
- **Local fallback:** Ollama (`mistral:7b`) if no HF token is set

---

## Scoring System

| Score | Meaning |
|-------|---------|
| 8–10 | Excellent — strong STAR structure + good keyword coverage |
| 5–7 | Good — missing key terms or depth |
| 1–4 | Needs work — expand and use role-specific language |
| NIL | Irrelevant response |

**Keyword Coverage Rule:** < 40% of expected keywords → score capped at 5/10.
