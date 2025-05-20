import streamlit as st
import pdfplumber
import requests
import json

st.title("📄 PDF to Mindmap Generator (Visual - DeepSeek Prover V2)")

# Replace with your actual OpenRouter API key
OPENROUTER_API_KEY = "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"

def generate_graphviz_mindmap(text):
    lines = text.strip().split("\n")
    graph = 'digraph G {\nnode [shape=box, style=rounded, color=gray, fontname="Helvetica"];\n'
    parent_stack = ["root"]
    graph += f'{parent_stack[0]} [label="Mindmap"];\n'
    indent_stack = [0]

    for line in lines:
        stripped = line.lstrip("-• ")
        indent = len(line) - len(line.lstrip())
        node_id = f'node_{hash(line)}'.replace('-', 'n')  # Unique node id
        graph += f'{node_id} [label="{stripped}"];\n'

        # Determine parent based on indent
        while indent_stack and indent < indent_stack[-1]:
            indent_stack.pop()
            parent_stack.pop()
        parent = parent_stack[-1]
        graph += f'{parent} -> {node_id};\n'
        parent_stack.append(node_id)
        indent_stack.append(indent)

    graph += '}'
    return graph


uploaded_file = st.file_uploader("Upload a PDF", type="pdf")

if uploaded_file is not None:
    with pdfplumber.open(uploaded_file) as pdf:
        text = ''
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text

    st.subheader("Extracted Text")
    st.text_area("PDF Content", text, height=300)

    if st.button("🧠 Generate Mindmap"):
        if not text.strip():
            st.error("No text was extracted from the PDF.")
        else:
            with st.spinner("Sending request to DeepSeek Prover V2..."):
                prompt = f"""You are a mindmap creator. Summarize the content below into a bullet-point mindmap format.

Content:
{text}

Mindmap:"""

                url = "https://openrouter.ai/api/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                }
                body = {
                    "model": "deepseek/deepseek-prover-v2:free",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                }

                response = requests.post(url, headers=headers, data=json.dumps(body))

                if response.status_code == 200:
                    result = response.json()
                    mindmap_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    st.subheader("🗺️ Mindmap Text")
                    st.text_area("AI-Generated Mindmap", mindmap_text, height=300)

                    st.subheader("📌 Visual Mindmap Chart")
                    graph_code = generate_graphviz_mindmap(mindmap_text)
                    st.graphviz_chart(graph_code)
                else:
                    st.error(f"❌ API Error {response.status_code}: {response.text}")
