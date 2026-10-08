# AI Career Co-Pilot

AI Career Co-Pilot is an intelligent career advisory system powered by Large Language Models (LLMs) and vector search. It bridges the gap between candidates and job descriptions (JDs) by performing deep semantic matching, skill gap analysis, and automated resume optimization.

---

## Key Features

- **Secure Authentication:** User sign-up, login, and session management protected by JWT (JSON Web Tokens) and password hashing (`bcrypt`).
- **Intelligent CV Parsing:** Upload resumes in PDF format. The system automatically extracts text, classifies the document, structures key details (skills, experience, education), and stores vector embeddings.
- **Job Description (JD) Validation & Parsing:** Supports both text input and PDF uploads for JDs with built-in validation to prevent cross-contamination (e.g., uploading a CV instead of a JD).
- **Deep Semantic Matching & Scoring:** Evaluates candidate-JD alignment using Qdrant vector database and LLM reasoning, returning a detailed match score, level, and categorized skill insights.
- **Analysis Evaluation Metrics:** Measures skill coverage rate, critical gap rate, match confidence, and overall quality score for every analysis.
- **Historical Analytics:** Securely tracks past analyses per user account for career progression tracking.
- **Modern UI & API:** Built with **FastAPI** for high-performance backend processing and **Streamlit** for an interactive, user-friendly frontend.

---

## Tech Stack

- **Backend:** Python, FastAPI, SQLAlchemy, Pydantic, Slowapi, Loguru, PyJWT, Passlib
- **Frontend:** Streamlit, Requests
- **AI / LLM:** Groq API / Gemini API, FastEmbed
- **Vector Database:** Qdrant
- **Testing & Quality:** Pytest, Ruff, Black

---

## Project Structure

```
ai-career-copilot/
├── app/
│   ├── api/          # FastAPI routes & endpoints
│   ├── core/         # Security, session store, configurations
│   ├── models/       # Database models & Pydantic schemas
│   └── tools/        # CV/JD parsers & LLM integration
├── tests/            # Pytest test suite (API tests)
├── .env.example      # Environment variables template
├── pyproject.toml    # Ruff & Black configurations
├── pytest.ini        # Pytest configuration
├── requirements.txt  # Production dependencies
├── requirements-dev.txt # Development & testing dependencies
├── streamlit_app.py  # Streamlit frontend application
└── README.md
```
---

## Getting Started

1. **Prerequisites:**
    Python 3.10+
    Pip & Virtual Environment

2. **Clone the Repository**
    git clone https://github.com/azizmirz/ai-career-copilot.git
    cd ai-career-copilot

3. **Create and Activate Virtual Environment**
    python -m venv venv
    # On Windows:
    venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate

4. **Install Dependencies**
    pip install -r requirements.txt
    pip install -r requirements-dev.txt

5. **Configure Environment Variables**
    Create a .env file in the root directory based on .env.example:
    
    GROQ_API_KEY=your_groq_key_here
    GEMINI_API_KEY=your_gemini_key_here
    SECRET_KEY=your_secret_key_here
    APP_ENV=development

6. **Running the Application**
    1.Start the FastAPI Backend:
    uvicorn app.main:app --reload --port 8000
    (The API documentation will be available at http://localhost:8000/docs)
    
    2.Start the Streamlit Frontend (in a new terminal window):
    streamlit run streamlit_app.py
    (The UI will open automatically in your browser at http://localhost:8501)

7. **Running Tests**
    To run the automated test suite using pytest



