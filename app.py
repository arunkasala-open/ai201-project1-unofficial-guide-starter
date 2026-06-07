"""Gradio web UI for the data-protection policy RAG system.

Run:  python app.py   then open  http://localhost:7860
Make sure Embedding_Setup.py has been run first so ./chroma_db exists.
"""

import gradio as gr

from rag_query import ask


def handle_query(question):
    question = (question or "").strip()
    if not question:
        return "Please type a question.", ""
    result = ask(question)
    sources = "\n".join(f"• {s}" for s in result["sources"]) or "(no sources matched)"
    return result["answer"], sources


with gr.Blocks(title="Data Protection Policy Assistant") as demo:
    gr.Markdown(
        "# 🌍 Data Protection Policy Assistant\n"
        "Ask about countries' data-protection / privacy laws. "
        "Answers are grounded **only** in the retrieved policy documents."
    )

    inp = gr.Textbox(
        label="Your question",
        placeholder="e.g. What is Iceland's Data Privacy Policy?",
    )
    btn = gr.Button("Ask", variant="primary")
    answer = gr.Textbox(label="Answer", lines=8)
    sources = gr.Textbox(label="Retrieved from", lines=4)

    gr.Examples(
        examples=[
            "What is Iceland's Data Privacy Policy?",
            "What are the duties of a data controller in Zambia?",
            "Which countries require registration before processing personal data?",
        ],
        inputs=inp,
    )

    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])


if __name__ == "__main__":
    demo.launch()
