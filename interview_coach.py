import gradio as gr
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"


def ask_ollama(prompt, model="mistral:7b", temperature=0.7):
    """Send prompt to Ollama"""
    try:
        payload = {
            "model": model, 
            "prompt": prompt, 
            "stream": False,
            "temperature": temperature  # ADD THIS
        }
        response = requests.post(OLLAMA_URL, json=payload, timeout=300)
        return response.json().get("response", "No response")
    except Exception as e:
        print(f"Error: {e}")
        return f"Error: {str(e)}"
#--------------------------------------------------------------------------------------------------

def generate_question(job_desc):
    if not job_desc or len(job_desc.strip()) < 20:
        return "Paste a job description (50+ chars)"
    
    prompt = f"""Generate ONE interview question for this role:

{job_desc}

Question:"""
    
    result = ask_ollama(prompt)
    
    if "Question:" in result:
        result = result.split("Question:")[-1].strip()
    
    if "?" in result:
        result = result.split("?")[0] + "?"
    
    return result[:400] if result else "Tell me about a challenging project?"
#--------------------------------------------------------------------------------------------------


def score_answer(answer):
    if not answer or len(answer.strip()) < 15:
        return "Provide a longer answer"
    
    prompt = f"""Rate this interview answer on scale of 0-10 (HARSH grading, be frank). Give 2 tips. Maintain a general Method of rating any inappropriate responses at a strict 0 score to promptly discourage misbehavior.

Answer: {answer}

Response:"""
    
    return ask_ollama(prompt)

with gr.Blocks() as demo:
    gr.Markdown("# 🎤 AI Interview Coach(Runs on Local Machine)")
    
    with gr.Group():
        job_desc = gr.Textbox(label="Job Description", lines=6)
        gen_btn = gr.Button("Generate Question", variant="primary")
    
    with gr.Group():
        question = gr.Textbox(label="Question", interactive=False, lines=3)
        answer = gr.Textbox(label="Your Answer", lines=6)
        submit_btn = gr.Button("Get Feedback", variant="primary")
    
    with gr.Group():
        feedback = gr.Textbox(label="Feedback", interactive=False, lines=6)
    
    gen_btn.click(generate_question, inputs=job_desc, outputs=question)
    submit_btn.click(score_answer, inputs=answer, outputs=feedback)

demo.launch()