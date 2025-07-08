# Gen-AI-Assistant
🤖 GenAI Document Assistant
GenAI Document Assistant is a powerful Streamlit application that uses OpenAI’s GPT models to help you analyze, understand, and interact with PDF or TXT documents. It offers document summarization, question answering, and AI-generated quizzes — all grounded strictly in your uploaded document.

🔍 Features
📄 Upload Documents: Supports PDF and TXT files up to 10MB

✨ AI-Powered Summary: Generates concise summaries (under 150 words)

💬 Ask Anything Mode: Ask free-form questions — answers include quotes and justifications from the document

🧠 Challenge Me Mode: Auto-generates 3 logic-based questions to test your comprehension

✅ Answer Evaluation: AI evaluates your answers with scores and feedback based on accuracy, completeness, and understanding

📊 Progress Tracking: See your quiz score, percentage, and detailed feedback

🔁 Retry Options: Generate new questions, retake quizzes, or upload new documents

📦 Installation
1. Clone the Repository

git clone https://github.com/your-username/genai-document-assistant.git
cd genai-document-assistant
2. Create a Virtual Environment (optional but recommended)

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
3. Install Dependencies

pip install -r requirements.txt
🚀 Usage
1. Add Your OpenAI API Key
You’ll need an OpenAI API Key to use the AI features.

The app allows entering the key via the sidebar. For production, you can set it using st.secrets or environment variables.

2. Run the App
   streamlit run app.py








⚙️ File Structure

.
├── app.py                  # Main Streamlit app
├── requirements.txt        # Python dependencies
├── README.md               # This file
