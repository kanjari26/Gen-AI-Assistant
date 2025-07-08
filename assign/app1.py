# app.py

import streamlit as st
from core import (
    create_vector_store_from_upload,
    generate_summary,
    create_conversational_chain,
    generate_challenge_questions,
    evaluate_challenge_answer
)

# --- App Configuration ---
st.set_page_config(page_title="Smart Research Assistant", layout="wide")

# --- Session State Initialization ---
# This is crucial to maintain state across user interactions in Streamlit
if "conversation_chain" not in st.session_state:
    st.session_state.conversation_chain = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "summary" not in st.session_state:
    st.session_state.summary = None
if "challenge_questions" not in st.session_state:
    st.session_state.challenge_questions = None
if "challenge_results" not in st.session_state:
    st.session_state.challenge_results = None


# --- UI Rendering ---
st.title("🧠 Smart Assistant for Research Summarization")
st.write("Upload a document (PDF or TXT) to get started.")

# --- Sidebar for Document Upload ---
with st.sidebar:
    st.header("Upload Your Document")
    uploaded_file = st.file_uploader("Choose a PDF or TXT file", type=["pdf", "txt"])

    if uploaded_file is not None:
        if st.button("Process Document"):
            with st.spinner("Processing document... This may take a moment."):
                # 1. Create Vector Store
                vector_store = create_vector_store_from_upload(uploaded_file)
                
                # 2. Create Conversational Chain and store in session
                st.session_state.conversation_chain = create_conversational_chain(vector_store)

                # 3. Generate Summary
                st.session_state.summary = generate_summary(vector_store)
                
                # 4. Clear previous challenge state
                st.session_state.challenge_questions = None
                st.session_state.challenge_results = None
                st.session_state.chat_history = [] # Reset chat history

                st.success("Document processed successfully!")
                st.rerun() # Rerun to update the main page view

# --- Main Content Area ---
if st.session_state.conversation_chain is None:
    st.info("Please upload and process a document to activate the assistant.")
else:
    # Display the summary first
    with st.expander("📝 **Auto Summary (≤ 150 Words)**", expanded=True):
        st.write(st.session_state.summary)

    # --- Interaction Modes (Tabs) ---
    tab1, tab2 = st.tabs(["💬 Ask Anything", "🤔 Challenge Me"])

    # --- "Ask Anything" Mode ---
    with tab1:
        st.header("Ask Anything")
        st.write("Ask free-form questions about the document.")

        # Display existing chat messages
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "source" in message:
                    with st.expander("View Source Snippet"):
                        st.info(message["source"])

        # Chat input for new questions
        if user_question := st.chat_input("What would you like to ask?"):
            # Add user message to history
            st.session_state.chat_history.append({"role": "user", "content": user_question})
            with st.chat_message("user"):
                st.markdown(user_question)

            # Get assistant's response
            with st.spinner("Thinking..."):
                result = st.session_state.conversation_chain({
                    "question": user_question,
                    "chat_history": [(msg["role"], msg["content"]) for msg in st.session_state.chat_history]
                })
                answer = result["answer"]
                source_docs = result["source_documents"]
                source_snippet = source_docs[0].page_content if source_docs else "No specific source snippet found."

                # Add assistant response to history
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": answer,
                    "source": source_snippet
                })

                # Display assistant's response
                with st.chat_message("assistant"):
                    st.markdown(answer)
                    with st.expander("View Source Snippet"):
                        st.info(source_snippet)

    # --- "Challenge Me" Mode ---
    with tab2:
        st.header("Challenge Me")
        st.write("Test your understanding with logic-based questions generated from the document.")

        # Generate questions if they don't exist
        if st.session_state.challenge_questions is None:
            if st.button("Generate Challenge Questions"):
                with st.spinner("Generating questions..."):
                    vector_store = st.session_state.conversation_chain.retriever.vectorstore
                    st.session_state.challenge_questions = generate_challenge_questions(vector_store)
                    st.rerun()
        else:
            # Display questions and collect answers in a form
            with st.form("challenge_form"):
                answers = []
                for i, q in enumerate(st.session_state.challenge_questions):
                    st.write(f"**Question {i+1}:** {q}")
                    answer = st.text_area(f"Your answer for question {i+1}", key=f"ans_{i}")
                    answers.append(answer)
                
                submitted = st.form_submit_button("Submit Answers")

                if submitted:
                    with st.spinner("Evaluating your answers..."):
                        results = []
                        vector_store = st.session_state.conversation_chain.retriever.vectorstore
                        for i, (q, a) in enumerate(zip(st.session_state.challenge_questions, answers)):
                            if a.strip() == "":
                                results.append("You did not provide an answer.")
                                continue
                            evaluation = evaluate_challenge_answer(vector_store, q, a)
                            results.append(evaluation)
                        st.session_state.challenge_results = results
                        st.rerun()

            # Display evaluation results if they exist
            if st.session_state.challenge_results:
                st.subheader("Evaluation Results")
                for i, result in enumerate(st.session_state.challenge_results):
                    st.write(f"**Question {i+1}:** {st.session_state.challenge_questions[i]}")
                    st.success(f"**Evaluation:**\n{result}")