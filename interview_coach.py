import gradio as gr
import os
from config import *
from engine import *

# ── Build UI ───────────────────────────────────────────────────────────────────
with gr.Blocks(title="AI Interview Coach") as demo:

    # Load history from disk on startup
    history_state = gr.State(load_history())
    q_index = gr.State("0")

    # Agenda 1, 2, 4, 5 System Profile Memory State
    job_profile_state = gr.State({
        "valid": False,
        "industry": "General",
        "keywords": [],
        "tips": "No tips generated yet."
    })

    
    gr.HTML("""
    <div style="text-align:center; padding: 1.8rem 0 0.8rem;">
        <h1 style="font-size:2.2rem; font-weight:800; margin:0; font-size: 2.2rem;
                   background: linear-gradient(135deg,#6366f1,#a78bfa);
                   -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
            AI Interview Coach
        </h1>
        <p style="color:#64748b; margin-top:0.4rem; font-size:1rem;">
            <b>Practice · Get Feedback · Improve</b><br>
            <span style="font-size:0.8rem; color:#808080;">Powered by <span style="color:#f97316; font-weight:600;">Mistral 7B</span></span>
        </p>
    </div>
    """)

    gr.HTML("""
        <style>
            @keyframes floatBlob1 {
                0%   { transform: translate(0px,   0px);  }
                33%  { transform: translate(-30px, -40px); }
                66%  { transform: translate(100px,  -20px); }
                100% { transform: translate(0px,   0px);  }
            }
            @keyframes floatBlob2 {
                0%   { transform: translate(0px,  0px);  }
                33%  { transform: translate(50px, 30px);  }
                66%  { transform: translate(-30px, 50px); }
                100% { transform: translate(0px,  0px);  }
            }
            @keyframes floatBlob3 {
                0%   { transform: translate(0px,   0px);  }
                33%  { transform: translate(-40px, 50px); }
                66%  { transform: translate(30px, -40px); }
                100% { transform: translate(0px,   0px);  }
            }

            @keyframes floatBlob4 {
                0%   { transform: translate(0px,   0px);  }
                33%  { transform: translate(50px, 100px); }
                66%  { transform: translate(30px, -40px); }
                100% { transform: translate(0px,   0px);  }
            }
        </style>

        <div style="
            position: fixed; width: 400px; height: 300px;
            border-radius: 50%; background: #6366f1;
            filter: blur(80px); opacity: 0.35;
            top: -100px; left: -100px;
            z-index: 0; pointer-events: none;
            animation: floatBlob1 20s ease-in-out infinite;
        "></div>

        <div style="
            position: fixed; width: 500px; height: 400px;
            border-radius: 50%; background: #8b5cf6;
            filter: blur(100px); opacity: 0.25;
            top: 50%; right: -200px;
            z-index: 0; pointer-events: none;
            animation: floatBlob2 25s ease-in-out infinite;
        "></div>

        <div style="
            position: fixed; width: 600px; height: 350px;
            border-radius: 50%; background: #f97316;
            filter: blur(90px); opacity: 0.2;
            bottom: -100px; left: 100px;
            z-index: 0; pointer-events: none;
            animation: floatBlob3 15s ease-in-out infinite;
        "></div>

        <div style="
            position: fixed; width: 600px; height: 350px;
            border-radius: 50%; background: #ff0077;
            filter: blur(90px); opacity: 0.2;
            top: 50px; right: -50px;
            z-index: 0; pointer-events: none;
            animation: floatBlob4 15s ease-in-out infinite;
        "></div>
    """)

    with gr.Tabs():

        # ── Tab 1: Practice ───────────────────────────────────────────────────
        with gr.Tab("🎯 Practice"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 📋 Step 1 — Paste the Job Description")
                    job_desc_box = gr.Textbox(
                        label="Job Description",
                        lines=6,
                        placeholder="Paste from LinkedIn, company careers page, etc.",
                    )
                    start_btn = gr.Button("🚀 Start Interview", variant="primary", size="lg")

                with gr.Column(scale=1):
                    gr.Markdown("### 💬 Step 2 — Answer Questions")
                    progress_box = gr.Textbox(
                        label="Progress",
                        value="Ready to start",
                        interactive=False,
                        elem_id="progress_box",
                    )
                    question_box = gr.Textbox(
                        label="Interview Question",
                        lines=3,
                        interactive=False,
                    )
                    answer_box = gr.Textbox(
                        label="Your Answer",
                        lines=5,
                        placeholder="Be specific — use the STAR format (Situation, Task, Action, Result).",
                    )
                    with gr.Row():
                        feedback_btn = gr.Button("📊 Get Feedback", variant="primary")
                        next_btn = gr.Button("➡️ Next Question", variant="secondary")

            # ── Previous answer review panel ──────────────────────────────────
            with gr.Accordion("🔁 Previous Question Review", open=False) as prev_accordion:
                with gr.Row():
                    prev_question_box = gr.Textbox(
                        label="Previous Question",
                        interactive=False,
                        lines=2,
                        placeholder="Will show the last question after you click Next Question...",
                    )
                    prev_answer_box = gr.Textbox(
                        label="Your Previous Answer",
                        interactive=False,
                        lines=3,
                        placeholder="Will show your last answer here...",
                    )

            # ── Full session log accordion ─────────────────────────────────────
            with gr.Accordion("📋 This Session's Log", open=False):
                session_log_display = gr.Markdown("Complete questions to see your session log here.")

            gr.Markdown("### 🏆 Step 3 — Coach Feedback")
            feedback_box = gr.Textbox(
                label="AI Coach Feedback",
                interactive=False,
                lines=7,
                elem_id="feedback_box",
            )

        # ── Tab 2: History ────────────────────────────────────────────────────
        with gr.Tab("📈 History & PDF Report"):
            gr.Markdown("""
            ### 📄 Download Interview Session Report
            Generate a professionally formatted PDF containing your complete interview history, answers, AI feedback, and coaching recommendations.
            """)
            with gr.Row():
                download_report_btn = gr.Button("📥 Generate PDF Report", variant="primary")
                refresh_btn = gr.Button("🔄 Refresh Preview", variant="secondary")
                clear_btn = gr.Button("🗑️ Clear History", variant="secondary")
            
            report_file_output = gr.File(label="Your PDF Report", interactive=False)
            
            gr.Markdown("---")
            gr.Markdown("### 📝 Quick Progress History")
            history_display = gr.Markdown(
                render_history(load_history())  # Load from disk on startup
            )

        # ── Tab 3: Tips ───────────────────────────────────────────────────────
        with gr.Tab("💡 Tips & Resources"):
            tips_display = gr.Markdown(build_tips())

    # ── Wire up events ─────────────────────────────────────────────────────────
    start_btn.click(
        fn=generate_all_questions,
        inputs=[job_desc_box, history_state, job_profile_state],
        outputs=[question_box, q_index, progress_box, history_state, tips_display, job_profile_state],
    ).then(
        fn=render_history,
        inputs=[history_state],
        outputs=[history_display],
    )

    feedback_btn.click(
        fn=score_answer,
        inputs=[answer_box, q_index, history_state],
        outputs=[feedback_box, history_state],
    ).then(
        fn=render_history,
        inputs=[history_state],
        outputs=[history_display],
    )

    next_btn.click(
        fn=next_question,
        inputs=[q_index, answer_box, history_state],
        outputs=[question_box, answer_box, q_index, progress_box, history_state, prev_question_box, prev_answer_box, session_log_display],
    )

    download_report_btn.click(
        fn=generate_pdf_report,
        inputs=[history_state],
        outputs=[report_file_output]
    )

    refresh_btn.click(
        fn=render_history,
        inputs=[history_state],
        outputs=[history_display],
    )

    def clear_history(history_state):
        """Clear all history"""
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        return [], "History cleared! Start a new interview above."

    clear_btn.click(
        fn=clear_history,
        inputs=[history_state],
        outputs=[history_state, history_display],
    )

custom_theme = gr.themes.Soft(
    primary_hue=gr.themes.colors.violet,
    secondary_hue=gr.themes.colors.purple,
    neutral_hue=gr.themes.colors.slate,
    font=[gr.themes.GoogleFont("Google Sans"), "ui-sans-serif", "sans-serif"],
)

demo.launch(theme=custom_theme, css=CUSTOM_CSS)