import gradio as gr
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

# Track state
current_questions = []
current_question_index = 0

def ask_ollama(prompt, model="mistral:7b", temperature=0.7):
    """Send prompt to Ollama"""
    try:
        payload = {
            "model": model, 
            "prompt": prompt, 
            "stream": False,
            "temperature": temperature
        }
        response = requests.post(OLLAMA_URL, json=payload, timeout=300)
        return response.json().get("response", "No response")
    except Exception as e:
        return f"❌ Error: {str(e)}"

def generate_all_questions(job_desc):
    """Generate all Level 1 questions at once"""
    global current_questions, current_question_index
    
    if not job_desc or len(job_desc.strip()) < 20:
        return "Paste a job description (50+ chars)", "", ""
    
    job_desc = job_desc[:400]
    
    # Generate Question 1
    prompt1 = f"""Generate ONE interview question about project experience. Based on:

{job_desc}

Question:"""
    
    q1 = ask_ollama(prompt1, temperature=0.8)
    if "Question:" in q1:
        q1 = q1.split("Question:")[-1].strip()
    if "?" in q1:
        q1 = q1.split("?")[0] + "?"
    
    # Generate Question 2
    prompt2 = f"""Generate ONE follow-up interview question about technologies used. Based on:

{job_desc}

Question:"""
    
    q2 = ask_ollama(prompt2, temperature=0.8)
    if "Question:" in q2:
        q2 = q2.split("Question:")[-1].strip()
    if "?" in q2:
        q2 = q2.split("?")[0] + "?"
    
    # Generate Question 3
    prompt3 = f"""Generate ONE follow-up interview question about challenges faced. Based on:

{job_desc}

Question:"""
    
    q3 = ask_ollama(prompt3, temperature=0.8)
    if "Question:" in q3:
        q3 = q3.split("Question:")[-1].strip()
    if "?" in q3:
        q3 = q3.split("?")[0] + "?"
    
    current_questions = [q1, q2, q3]
    current_question_index = 0
    
    return q1, "", f"Question 1/3"

def get_next_question():
    """Move to next question"""
    global current_question_index
    
    if current_question_index < len(current_questions) - 1:
        current_question_index += 1
        next_q = current_questions[current_question_index]
        progress = f"Question {current_question_index + 1}/3"
        return next_q, "", progress
    else:
        return "All questions completed!", "", "Interview Complete!"

def score_answer(answer):
    """Score and give feedback on the answer"""
    if not answer or len(answer.strip()) < 15:
        return "Provide a longer answer (20+ chars)"
    
    answer = answer[:400]
    
    prompt = f"""You are a TOUGH interview coach. Rate this interview answer 0-10.

FIRST: Check if it's RELEVANT to interview questions. If not relevant/off-topic, score max 3/10.

THEN: If relevant, rate on clarity, examples, and impact.

Answer: {answer}

Score and explain:
1. Is this relevant? (YES/NO)
2. Score: X/10
3. Main weakness
4. One specific fix"""
    
    return ask_ollama(prompt, temperature=0.5)

# Build the UI
with gr.Blocks(title="Interview Prep Coach", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🎤 Interview Prep Coach
    
    **Practice real interview scenarios with AI coaching**
    """)
    
    with gr.Column(scale=0.6):  # Narrower container
        with gr.Group():
            gr.Markdown("## Step 1: Job Description")
            job_desc = gr.Textbox(
                label="Paste job description",
                lines=5,
                placeholder="Paste from LinkedIn, company website, etc.",
                info="Include role, skills, responsibilities"
            )
            gen_btn = gr.Button("🚀 Start Interview", variant="primary", size="lg")
        
        with gr.Group():
            gr.Markdown("## Step 2: Answer Questions")
            
            progress = gr.Textbox(
                label="Progress",
                interactive=False,
                value="Ready to start",
                info="Shows which question you're on"
            )
            
            question = gr.Textbox(
                label="Interview Question",
                interactive=False,
                lines=3,
                info="Your current question"
            )
            
            answer = gr.Textbox(
                label="Your Answer",
                lines=5,
                placeholder="Type your answer here...",
                info="Be specific with examples"
            )
            
            with gr.Row():
                submit_btn = gr.Button("📊 Get Feedback", variant="primary")
                next_btn = gr.Button("➡️ Next Question", variant="secondary")
        
        with gr.Group():
            gr.Markdown("## Step 3: Feedback")
            feedback = gr.Textbox(
                label="Coach Feedback",
                interactive=False,
                lines=6,
                info="Your AI coach will rate and suggest improvements"
            )
    
    # Connect buttons
    gen_btn.click(
        generate_all_questions,
        inputs=job_desc,
        outputs=[question, answer, progress]
    )
    
    submit_btn.click(
        score_answer,
        inputs=answer,
        outputs=feedback
    )
    
    next_btn.click(
        get_next_question,
        outputs=[question, answer, progress]
    )

demo.launch()