import streamlit as st
import PyPDF2
import openai
from typing import List, Dict
import time

# Configure the page
st.set_page_config(
    page_title="GenAI Document Assistant",
    page_icon="📄",
    layout="wide"
)

# Initialize session state
if 'document_content' not in st.session_state:
    st.session_state.document_content = ""
if 'document_name' not in st.session_state:
    st.session_state.document_name = ""
if 'summary' not in st.session_state:
    st.session_state.summary = ""
if 'mode' not in st.session_state:
    st.session_state.mode = None
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'current_question_index' not in st.session_state:
    st.session_state.current_question_index = 0
if 'quiz_state' not in st.session_state:
    st.session_state.quiz_state = "ready"
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

class DocumentProcessor:
    """Handles document processing and text extraction"""
    
    @staticmethod
    def extract_text_from_pdf(pdf_file) -> str:
        """Extract text from PDF file using PyPDF2"""
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
            
            # Clean up the text
            text = text.replace('\n\n', '\n').strip()
            return text
        except Exception as e:
            st.error(f"Error extracting text from PDF: {str(e)}")
            return ""
    
    @staticmethod
    def extract_text_from_txt(txt_file) -> str:
        """Extract text from TXT file"""
        try:
            content = txt_file.read()
            if isinstance(content, bytes):
                content = content.decode('utf-8')
            return content.strip()
        except Exception as e:
            st.error(f"Error reading text file: {str(e)}")
            return ""

class AIAssistant:
    """Handles AI interactions using OpenAI API"""
    
    
    def __init__(self, api_key: str, model_name: str = "gpt-3.5-turbo"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model_name = model_name
    
    def generate_summary(self, content: str) -> str:
        """Generate a concise summary of the document (under 150 words)"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a document summarization expert. Create concise, informative summaries that capture the key points and main themes of documents in under 150 words."
                    },
                    {
                        "role": "user",
                        "content": f"Please provide a concise summary of the following document content in under 150 words. Focus on the main points, key themes, and important information:\n\n{content[:4000]}\n\nSummary:"
                    }
                ],
                max_tokens=200,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    def answer_question(self, question: str, document_content: str) -> str:
        """Answer questions based strictly on document content"""
        try:
            response = self.client.chat.completions.create(
                model= self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a helpful AI assistant that answers questions based STRICTLY on the provided document content.

CRITICAL RULES:
1. ONLY use information explicitly stated or directly inferable from the document
2. If the document doesn't contain information to answer the question, clearly state "The document does not contain information to answer this question"
3. ALWAYS provide justification by quoting or referencing specific parts of the document
4. Do NOT use external knowledge or make assumptions beyond the document content
5. Structure your response as: [Direct Answer] followed by [Justification with specific document references]"""
                    },
                    {
                        "role": "user",
                        "content": f"Document Content:\n{document_content}\n\nQuestion: {question}\n\nAnswer based solely on the document content above, with justification:"
                    }
                ],
                max_tokens=500,
                temperature=0.2
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error answering question: {str(e)}"
    
    def generate_quiz_questions(self, document_content: str) -> List[str]:
        """Generate exactly 3 logic-based questions from document content"""
        try:
            response = self.client.chat.completions.create(
                model= self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert quiz generator. Create exactly 3 challenging, logic-based questions that test deep understanding of the document content.

REQUIREMENTS:
1. Generate EXACTLY 3 questions
2. Focus on comprehension, analysis, and critical thinking (not simple recall)
3. Questions must be answerable from the document content
4. Test understanding of relationships, implications, and reasoning
5. Format: One question per line, no numbering
6. Make questions thought-provoking and analytical"""
                    },
                    {
                        "role": "user",
                        "content": f"Based on this document content, generate exactly 3 challenging logic-based questions that test analytical thinking:\n\n{document_content[:3000]}\n\nQuestions:"
                    }
                ],
                max_tokens=300,
                temperature=0.4
            )
            
            questions_text = response.choices[0].message.content.strip()
            questions = [q.strip() for q in questions_text.split('\n') if q.strip() and len(q.strip()) > 10]
            return questions[:3]  # Ensure exactly 3 questions
        except Exception as e:
            st.error(f"Error generating questions: {str(e)}")
            return []
    
    def evaluate_answer(self, question: str, user_answer: str, document_content: str) -> Dict[str, any]:
        """Evaluate user's answer with justified feedback"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert evaluator. Assess answers based on accuracy, completeness, and understanding relative to the document content.

EVALUATION CRITERIA:
1. Accuracy: Factually correct based on the document
2. Completeness: Addresses all aspects of the question  
3. Understanding: Demonstrates comprehension of concepts
4. Evidence: References or aligns with document content

SCORING (0-10):
- 9-10: Excellent - Accurate, complete, deep understanding
- 7-8: Good - Mostly accurate and complete
- 5-6: Fair - Partially correct, basic understanding
- 3-4: Poor - Some correct elements, significant gaps
- 0-2: Very Poor - Mostly incorrect or irrelevant

REQUIRED FORMAT:
SCORE: [number 0-10]
EVALUATION: [Detailed feedback with specific justifications from the document, explaining the score and how to improve]"""
                    },
                    {
                        "role": "user",
                        "content": f"Document Content:\n{document_content[:3000]}\n\nQuestion: {question}\n\nUser Answer: {user_answer}\n\nEvaluate this answer:"
                    }
                ],
                max_tokens=400,
                temperature=0.3
            )
            
            evaluation_text = response.choices[0].message.content.strip()
            
            # Parse score
            score = 5  # default
            lines = evaluation_text.split('\n')
            
            for line in lines:
                if 'SCORE:' in line.upper():
                    try:
                        score = int(''.join(filter(str.isdigit, line)))
                        score = max(0, min(10, score))  # Ensure 0-10 range
                        break
                    except:
                        pass
            
            # Extract evaluation text
            eval_start = evaluation_text.upper().find('EVALUATION:')
            if eval_start != -1:
                evaluation = evaluation_text[eval_start + 11:].strip()
            else:
                evaluation = evaluation_text
            
            return {"score": score, "evaluation": evaluation}
        except Exception as e:
            return {"score": 0, "evaluation": f"Error evaluating answer: {str(e)}"}

def reset_session():
    """Reset all session state variables"""
    keys_to_reset = ['document_content', 'document_name', 'summary', 'mode', 
                     'questions', 'current_question_index', 'quiz_state', 'chat_history']
    for key in keys_to_reset:
        if key in st.session_state:
            del st.session_state[key]

def main():
    """Main application function"""
    
    # Header
    st.title("🤖 GenAI Document Assistant")
    st.markdown("**Upload PDF/TXT documents for AI-powered analysis and interactive learning**")
    
    # Sidebar for API key
    with st.sidebar:
        st.header("🔑 Configuration")
        api_key = st.text_input(
            "OpenAI API Key", 
            type="password", 
            help="Enter your OpenAI API key to enable AI features"
        )
        model_name = st.selectbox("OpenAI Model", options = ["gpt-3.5-turbo" , "gpt-4", "gpt-4o"],
                                  index = 0, help = "Choose a model on your access level. GPT-3.5 is free and fast. GPT-4(o) needs paid access")
        
        if not api_key:
            st.warning("⚠️ Please enter your OpenAI API key to continue")
            st.info("Get your API key from: https://platform.openai.com/api-keys")
            st.stop()
        
        # Initialize AI assistant
        try:
            ai_assistant = AIAssistant(api_key, model_name)
        except Exception as e:
            st.error(f"Error initializing AI assistant: {str(e)}")
            st.stop()
        
        st.header("📋 How to Use")
        st.markdown("""
        1. **Upload** a PDF or TXT document
        2. **Review** the AI-generated summary  
        3. **Choose** an interaction mode:
           - **Ask Anything**: Free-form Q&A
           - **Challenge Me**: Take a 3-question quiz
        """)
        
        if st.session_state.document_content:
            st.success(f"📄 Document loaded: {st.session_state.document_name}")
            if st.button("🔄 Upload New Document"):
                reset_session()
                st.rerun()
    
    # Main content area
    if not st.session_state.document_content:
        # File upload section
        st.header("📄 Upload Document")
        
        uploaded_file = st.file_uploader(
            "Choose a PDF or TXT file",
            type=['pdf', 'txt'],
            help="Upload a document to begin AI-powered analysis"
        )
        
        if uploaded_file is not None:
            # File validation
            if uploaded_file.size > 10 * 1024 * 1024:  # 10MB limit
                st.error("❌ File size must be less than 10MB")
                st.stop()
            
            if uploaded_file.size == 0:
                st.error("❌ File appears to be empty")
                st.stop()
            
            # Process document
            with st.spinner("🔄 Processing document..."):
                if uploaded_file.type == "application/pdf":
                    content = DocumentProcessor.extract_text_from_pdf(uploaded_file)
                else:
                    content = DocumentProcessor.extract_text_from_txt(uploaded_file)
                
                if not content or len(content.strip()) < 50:
                    st.error("❌ Could not extract sufficient text from the document")
                    st.stop()
                
                # Store document content
                st.session_state.document_content = content
                st.session_state.document_name = uploaded_file.name
                
                # Generate summary
                with st.spinner("🤖 Generating AI summary..."):
                    summary = ai_assistant.generate_summary(content)
                    st.session_state.summary = summary
                
                st.success(f"✅ Successfully processed: {uploaded_file.name}")
                st.rerun()
    
    else:
        # Document summary section
        st.header("📋 Document Summary")
        st.info(st.session_state.summary)
        
        # Mode selection
        if not st.session_state.mode:
            st.header("🎯 Choose Interaction Mode")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("💬 Ask Anything", use_container_width=True, type="primary"):
                    st.session_state.mode = "ask_anything"
                    st.rerun()
                st.markdown("**Free-form questions** with document-based answers and justifications")
            
            with col2:
                if st.button("🧠 Challenge Me", use_container_width=True, type="primary"):
                    st.session_state.mode = "challenge_me"
                    st.session_state.quiz_state = "ready"
                    st.rerun()
                st.markdown("**Take a quiz** with 3 logic-based questions and detailed feedback")
        
        # Ask Anything Mode
        elif st.session_state.mode == "ask_anything":
            st.header("💬 Ask Anything")
            st.markdown("Ask questions about your document. All answers are grounded in the document content.")
            
            # Question input
            question = st.text_area(
                "Your Question:",
                placeholder="What are the main arguments presented in this document?",
                height=100
            )
            
            col1, col2 = st.columns([2, 1])
            with col1:
                if st.button("🔍 Get Answer", disabled=not question.strip(), type="primary"):
                    with st.spinner("🤖 Analyzing document and generating answer..."):
                        answer = ai_assistant.answer_question(question, st.session_state.document_content)
                        st.session_state.chat_history.append({
                            "question": question,
                            "answer": answer,
                            "timestamp": time.time()
                        })
                        st.rerun()
            
            with col2:
                if st.button("← Back to Modes"):
                    st.session_state.mode = None
                    st.rerun()
            
            # Display conversation history
            if st.session_state.chat_history:
                st.subheader("💭 Conversation History")
                
                for i, chat in enumerate(reversed(st.session_state.chat_history)):
                    with st.expander(
                        f"Q: {chat['question'][:80]}..." if len(chat['question']) > 80 
                        else f"Q: {chat['question']}", 
                        expanded=(i == 0)
                    ):
                        st.markdown(f"**Question:** {chat['question']}")
                        st.markdown(f"**Answer:** {chat['answer']}")
        
        # Challenge Me Mode
        elif st.session_state.mode == "challenge_me":
            st.header("🧠 Challenge Me")
            st.markdown("Test your understanding with AI-generated questions based on your document.")
            
            # Generate questions
            if st.session_state.quiz_state == "ready":
                if st.button("🎯 Generate Quiz Questions", type="primary"):
                    with st.spinner("🤖 Generating 3 challenging questions..."):
                        questions = ai_assistant.generate_quiz_questions(st.session_state.document_content)
                        
                        if len(questions) >= 3:
                            st.session_state.questions = [
                                {
                                    "id": i + 1,
                                    "question": q,
                                    "user_answer": "",
                                    "evaluation": "",
                                    "score": 0,
                                    "answered": False
                                }
                                for i, q in enumerate(questions[:3])
                            ]
                            st.session_state.quiz_state = "answering"
                            st.session_state.current_question_index = 0
                            st.rerun()
                        else:
                            st.error("❌ Could not generate sufficient questions. Please try again.")
                
                if st.button("← Back to Modes"):
                    st.session_state.mode = None
                    st.rerun()
            
            # Answering phase
            elif st.session_state.quiz_state == "answering" and st.session_state.questions:
                current_q = st.session_state.questions[st.session_state.current_question_index]
                
                # Progress indicator
                progress = (st.session_state.current_question_index) / len(st.session_state.questions)
                st.progress(progress, text=f"Question {st.session_state.current_question_index + 1} of {len(st.session_state.questions)}")
                
                # Display question
                st.subheader(f"Question {current_q['id']}")
                st.write(current_q["question"])
                
                # Answer input
                user_answer = st.text_area(
                    "Your Answer:",
                    value=current_q["user_answer"],
                    placeholder="Provide a detailed answer based on the document content...",
                    height=150,
                    key=f"answer_{current_q['id']}"
                )
                
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    if st.button("✅ Submit Answer", disabled=not user_answer.strip(), type="primary"):
                        with st.spinner("🤖 Evaluating your answer..."):
                            evaluation_result = ai_assistant.evaluate_answer(
                                current_q["question"],
                                user_answer,
                                st.session_state.document_content
                            )
                            
                            # Update question
                            st.session_state.questions[st.session_state.current_question_index].update({
                                "user_answer": user_answer,
                                "evaluation": evaluation_result["evaluation"],
                                "score": evaluation_result["score"],
                                "answered": True
                            })
                            
                            # Move to next question or results
                            if st.session_state.current_question_index < len(st.session_state.questions) - 1:
                                st.session_state.current_question_index += 1
                            else:
                                st.session_state.quiz_state = "results"
                            
                            st.rerun()
                
                with col2:
                    if st.session_state.current_question_index > 0:
                        if st.button("← Previous"):
                            st.session_state.current_question_index -= 1
                            st.rerun()
                
                with col3:
                    if st.button("← Back to Modes"):
                        st.session_state.mode = None
                        st.rerun()
            
            # Results phase
            elif st.session_state.quiz_state == "results":
                st.subheader("🎯 Quiz Results")
                
                # Calculate overall score
                total_score = sum(q["score"] for q in st.session_state.questions)
                max_score = len(st.session_state.questions) * 10
                percentage = (total_score / max_score) * 100
                
                # Display overall score
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Score", f"{total_score}/{max_score}")
                with col2:
                    st.metric("Percentage", f"{percentage:.1f}%")
                with col3:
                    if percentage >= 80:
                        st.success("🎉 Excellent!")
                    elif percentage >= 60:
                        st.info("👍 Good job!")
                    else:
                        st.warning("📚 Keep studying!")
                
                # Display detailed results
                st.subheader("📊 Detailed Results")
                
                for i, q in enumerate(st.session_state.questions):
                    with st.expander(f"Question {i+1} - Score: {q['score']}/10", expanded=False):
                        st.markdown(f"**Question:** {q['question']}")
                        st.markdown(f"**Your Answer:** {q['user_answer']}")
                        st.markdown(f"**Evaluation:** {q['evaluation']}")
                        
                        # Score visualization
                        if q['score'] >= 8:
                            st.success(f"🌟 Excellent: {q['score']}/10")
                        elif q['score'] >= 6:
                            st.info(f"👍 Good: {q['score']}/10")
                        elif q['score'] >= 4:
                            st.warning(f"⚠️ Fair: {q['score']}/10")
                        else:
                            st.error(f"❌ Needs improvement: {q['score']}/10")
                
                # Action buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔄 Try New Questions", type="primary"):
                        st.session_state.questions = []
                        st.session_state.quiz_state = "ready"
                        st.session_state.current_question_index = 0
                        st.rerun()
                
                with col2:
                    if st.button("← Back to Modes"):
                        st.session_state.mode = None
                        st.rerun()

if __name__ == "__main__":
    main()