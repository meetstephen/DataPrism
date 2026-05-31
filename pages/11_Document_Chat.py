"""Document Chat - Upload any document and chat with it using AI."""
import streamlit as st
st.set_page_config(page_title="Document Chat", page_icon="\U0001f4a0", layout="wide")
from utils.styles import inject_global_css
inject_global_css()

import pandas as pd
from io import StringIO, BytesIO
from utils.ai_client import get_api_key, GEMINI_MODEL
from utils.persistence import save_session_state

st.title("📄 Document Chat")
st.markdown("Upload any document and have an AI-powered conversation about its contents. Get insights, summaries, and answers to your questions.")

st.markdown("---")

# Initialize chat state for document chat
if "doc_chat_history" not in st.session_state:
    st.session_state.doc_chat_history = []
if "doc_content" not in st.session_state:
    st.session_state.doc_content = None
if "doc_name" not in st.session_state:
    st.session_state.doc_name = None

# File uploader
uploaded_doc = st.file_uploader(
    "Upload a document to chat with",
    type=["pdf", "docx", "doc", "txt", "csv", "xlsx", "xls", "json", "md", "rtf"],
    help="Supported formats: PDF, Word (DOCX), Text, CSV, Excel, JSON, Markdown"
)

def extract_text_from_file(uploaded_file):
    """Extract text content from various file types."""
    file_type = uploaded_file.name.split(".")[-1].lower()
    content = ""
    
    try:
        if file_type == "txt" or file_type == "md" or file_type == "rtf":
            content = uploaded_file.read().decode("utf-8", errors="replace")
        
        elif file_type == "csv":
            df = pd.read_csv(uploaded_file)
            content = f"CSV File: {uploaded_file.name}\n"
            content += f"Shape: {df.shape[0]} rows x {df.shape[1]} columns\n"
            content += f"Columns: {', '.join(df.columns.tolist())}\n\n"
            content += "Column Types:\n"
            for col in df.columns:
                content += f"  - {col}: {df[col].dtype}\n"
            content += f"\nSummary Statistics:\n{df.describe().to_string()}\n"
            content += f"\nFirst 20 rows:\n{df.head(20).to_string()}\n"
            if len(df) > 20:
                content += f"\n... ({len(df) - 20} more rows)\n"
            # Also store the dataframe
            st.session_state.uploaded_df = df
        
        elif file_type in ["xlsx", "xls"]:
            df = pd.read_excel(uploaded_file)
            content = f"Excel File: {uploaded_file.name}\n"
            content += f"Shape: {df.shape[0]} rows x {df.shape[1]} columns\n"
            content += f"Columns: {', '.join(df.columns.tolist())}\n\n"
            content += "Column Types:\n"
            for col in df.columns:
                content += f"  - {col}: {df[col].dtype}\n"
            content += f"\nSummary Statistics:\n{df.describe().to_string()}\n"
            content += f"\nFirst 20 rows:\n{df.head(20).to_string()}\n"
            if len(df) > 20:
                content += f"\n... ({len(df) - 20} more rows)\n"
            st.session_state.uploaded_df = df
        
        elif file_type == "json":
            import json
            raw = uploaded_file.read().decode("utf-8", errors="replace")
            try:
                data = json.loads(raw)
                if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                    df = pd.DataFrame(data)
                    content = f"JSON File (tabular): {uploaded_file.name}\n"
                    content += f"Shape: {df.shape[0]} rows x {df.shape[1]} columns\n"
                    content += f"Columns: {', '.join(df.columns.tolist())}\n\n"
                    content += f"First 10 records:\n{df.head(10).to_string()}\n"
                    st.session_state.uploaded_df = df
                else:
                    content = f"JSON File: {uploaded_file.name}\n\n"
                    content += json.dumps(data, indent=2)[:10000]  # Limit to 10k chars
            except json.JSONDecodeError:
                content = raw[:10000]
        
        elif file_type == "pdf":
            try:
                import fitz  # PyMuPDF
                pdf_bytes = uploaded_file.read()
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                pages_text = []
                for page_num, page in enumerate(doc):
                    text = page.get_text()
                    if text.strip():
                        pages_text.append(f"--- Page {page_num + 1} ---\n{text}")
                content = f"PDF File: {uploaded_file.name}\n"
                content += f"Pages: {len(doc)}\n\n"
                content += "\n".join(pages_text)
                doc.close()
            except ImportError:
                # Fallback if PyMuPDF not available
                content = "[PDF reading requires PyMuPDF. Please install it or convert to text first.]"
            except Exception as e:
                content = f"[Error reading PDF: {str(e)}]"
        
        elif file_type in ["docx", "doc"]:
            try:
                from docx import Document
                doc = Document(uploaded_file)
                paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                content = f"Word Document: {uploaded_file.name}\n"
                content += f"Paragraphs: {len(paragraphs)}\n\n"
                content += "\n\n".join(paragraphs)
            except ImportError:
                content = "[Word document reading requires python-docx. Please install it or convert to text first.]"
            except Exception as e:
                content = f"[Error reading document: {str(e)}]"
        
        else:
            content = uploaded_file.read().decode("utf-8", errors="replace")
    
    except Exception as e:
        content = f"[Error processing file: {str(e)}]"
    
    # Truncate very long content for context window
    if len(content) > 30000:
        content = content[:30000] + "\n\n[... Content truncated for analysis. First 30,000 characters shown.]"
    
    return content


# Process uploaded document
if uploaded_doc:
    if uploaded_doc.name != st.session_state.doc_name:
        with st.spinner("Reading document..."):
            content = extract_text_from_file(uploaded_doc)
            st.session_state.doc_content = content
            st.session_state.doc_name = uploaded_doc.name
            st.session_state.doc_chat_history = []  # Reset chat for new doc
        st.success(f"Document loaded: **{uploaded_doc.name}** ({len(content):,} characters extracted)")

# Show document preview
if st.session_state.doc_content:
    with st.expander("Document Preview", expanded=False):
        st.text(st.session_state.doc_content[:3000])
        if len(st.session_state.doc_content) > 3000:
            st.caption(f"Showing first 3,000 of {len(st.session_state.doc_content):,} characters")

    st.markdown("---")

    # Quick action buttons
    st.markdown("### Quick Actions")
    action_col1, action_col2, action_col3, action_col4 = st.columns(4)
    
    with action_col1:
        if st.button("Summarize", use_container_width=True):
            st.session_state.doc_chat_history.append({
                "role": "user",
                "content": "Please provide a comprehensive summary of this document. Include the main topics, key findings, and important details."
            })
            st.rerun()
    
    with action_col2:
        if st.button("Key Insights", use_container_width=True):
            st.session_state.doc_chat_history.append({
                "role": "user",
                "content": "What are the most important insights and key takeaways from this document? List them as bullet points."
            })
            st.rerun()
    
    with action_col3:
        if st.button("Generate Questions", use_container_width=True):
            st.session_state.doc_chat_history.append({
                "role": "user",
                "content": "Generate 5 important questions that this document raises or answers. For each question, provide a brief answer based on the document content."
            })
            st.rerun()
    
    with action_col4:
        if st.button("Data Analysis", use_container_width=True):
            st.session_state.doc_chat_history.append({
                "role": "user",
                "content": "If this document contains data or statistics, provide a detailed analysis. Identify trends, patterns, outliers, and any notable findings. If it's a text document, analyze the key themes and arguments."
            })
            st.rerun()

    st.markdown("---")
    st.markdown("### Chat")

    # Display chat history
    for message in st.session_state.doc_chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask anything about your document..."):
        st.session_state.doc_chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing document..."):
                # Try Gemini API
                api_key = get_api_key()

                if api_key:
                    try:
                        import google.generativeai as genai
                        genai.configure(api_key=api_key)

                        # Build context
                        system_context = (
                            "You are DataPrism's senior document analysis assistant, acting as an "
                            "expert analyst. You have been given the contents of a document to analyze. "
                            "Answer the user's questions strictly based on the document content. "
                            "Be specific and quantified: cite exact figures and reference relevant "
                            "parts of the document, and provide actionable insights. "
                            "If the document contains data, provide quantitative analysis with concrete numbers. "
                            "Format every response in clean markdown with clear headings and bullet points."
                        )
                        model = genai.GenerativeModel(GEMINI_MODEL, system_instruction=system_context)
                        
                        # Include last few messages for context
                        history_context = ""
                        recent_history = st.session_state.doc_chat_history[-6:-1]  # Last 5 messages before current
                        if recent_history:
                            history_context = "\n\nRecent conversation:\n"
                            for msg in recent_history:
                                history_context += f"{msg['role'].upper()}: {msg['content']}\n"
                        
                        full_prompt = (
                            f"DOCUMENT CONTENT:\n{st.session_state.doc_content}\n\n"
                            f"{history_context}\n"
                            f"USER QUESTION: {prompt}\n\n"
                            "Provide a detailed, helpful response:"
                        )
                        
                        response = model.generate_content(full_prompt)
                        
                        if response and response.text:
                            answer = response.text
                        else:
                            answer = "I couldn't generate a response. Please try rephrasing your question."
                    
                    except Exception as e:
                        import logging
                        logging.warning(f"Gemini document chat failed: {str(e)}")
                        answer = "AI analysis unavailable. Please check your Gemini API key in the sidebar."
                else:
                    # Fallback - basic analysis without AI
                    doc_content = st.session_state.doc_content
                    answer = (
                        "**AI features require a Gemini API key.**\n\n"
                        "Enter your key in the sidebar to enable intelligent document chat.\n\n"
                        "**Document info:**\n"
                        f"- File: {st.session_state.doc_name}\n"
                        f"- Content length: {len(doc_content):,} characters\n"
                        f"- Lines: {doc_content.count(chr(10)):,}\n\n"
                        "Get a free API key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)"
                    )
                
                st.markdown(answer)
                st.session_state.doc_chat_history.append({"role": "assistant", "content": answer})
                save_session_state()

    # Sidebar for this page
    with st.sidebar:
        st.markdown("### Document Chat")
        if st.session_state.doc_name:
            st.success(f"Active: {st.session_state.doc_name}")
        
        # API key input
        api_key_input = st.text_input("Gemini API Key", type="password", key="doc_chat_api_key")
        if api_key_input:
            st.session_state.gemini_api_key = api_key_input
        
        st.markdown("---")
        if st.button("Clear Chat History"):
            st.session_state.doc_chat_history = []
            st.rerun()
        
        if st.session_state.doc_chat_history:
            # Export chat as text
            chat_export = f"Document Chat - {st.session_state.doc_name}\n{'='*50}\n\n"
            for msg in st.session_state.doc_chat_history:
                chat_export += f"{'USER' if msg['role'] == 'user' else 'AI'}: {msg['content']}\n\n"
            st.download_button("Export Chat", chat_export, file_name="document_chat.txt", mime="text/plain")

    # Cross-module navigation
    st.markdown("---")
    st.markdown("### Related Tools")
    nav_col1, nav_col2, nav_col3 = st.columns(3)
    with nav_col1:
        st.page_link("pages/10_Chat_With_Data.py", label="Chat With Data", icon="\U0001F4AC")
    with nav_col2:
        st.page_link("pages/8_Expert_Analyst.py", label="Expert Analyst", icon="\U0001F393")
    with nav_col3:
        st.page_link("pages/7_Report_Generator.py", label="Generate Report", icon="\U0001F4CB")

else:
    # Empty state
    from utils.styles import render_empty_state
    render_empty_state(
        "\U0001F4C4",
        "Upload a Document",
        "Upload any document (PDF, Word, Excel, CSV, Text, JSON) and start chatting with it. Ask questions, get summaries, extract insights, and more."
    )
    
    st.markdown("---")
    st.markdown("### Supported File Types")
    
    type_col1, type_col2, type_col3 = st.columns(3)
    with type_col1:
        st.markdown("""
        **Data Files**
        - CSV (.csv)
        - Excel (.xlsx, .xls)
        - JSON (.json)
        """)
    with type_col2:
        st.markdown("""
        **Documents**
        - PDF (.pdf)
        - Word (.docx)
        - Text (.txt)
        """)
    with type_col3:
        st.markdown("""
        **Other**
        - Markdown (.md)
        - Rich Text (.rtf)
        - Power BI exports
        """)
