# GenAI Document Q&A System using RAG

A full-stack AI-powered document question-answering application that allows users to upload PDF documents and ask questions based on their content.

The project uses Retrieval Augmented Generation (RAG), where relevant information is retrieved from the uploaded document using vector similarity search and provided as context to a Large Language Model (LLM) for generating accurate answers.

---

## Features

- User authentication using JWT
- Secure password hashing with bcrypt
- PDF upload and text extraction
- Document chunking for efficient processing
- Text embeddings generation using Sentence Transformers
- Vector similarity search using FAISS
- Context-aware answers using LLM integration
- React-based interactive Q&A interface
- Protected routes for authenticated users

---

## Tech Stack

### Frontend
- React.js
- Vite
- React Router DOM
- Axios
- CSS

### Backend
- FastAPI
- Python
- MongoDB
- Motor (Async MongoDB Driver)
- JWT Authentication
- Pydantic

### GenAI / Machine Learning
- LangChain
- FAISS (Vector Search)
- HuggingFace Sentence Transformers
- OpenRouter API
- Large Language Models (LLMs)

---

## System Architecture
          React Frontend
                |
                |
          Axios API Calls
                |
                v
         FastAPI Backend
                |
    --------------------------
    |                        |
    Authentication Document Pipeline
| |
MongoDB PDF Processing
|
v
Text Extraction
|
v
Text Chunking
|
v
Embeddings Model
|
v
FAISS Index
|
v
Retriever + LLM
|
v
Generated Answer


---

## How It Works

### 1. Authentication Flow

- User signs up using email and password
- Password is hashed using bcrypt before storing
- User credentials are stored in MongoDB
- On successful login, JWT token is generated
- Token is sent with protected API requests

---

### 2. Document Processing Flow

When a PDF is uploaded:

1. FastAPI receives the document
2. PyMuPDF extracts text from the PDF
3. Extracted text is divided into smaller chunks
4. Sentence Transformer model generates embeddings
5. Embeddings are stored in FAISS vector store

---

### 3. Question Answering Flow

When a user asks a question:

1. The question is processed by the retriever
2. FAISS searches for the most relevant document chunks
3. Retrieved context and question are passed to the LLM
4. LLM generates a context-aware response
5. Answer is displayed on the frontend

---

## API Endpoints

### Authentication

### Signup

Project Structure
client/
 └── src/
     ├── components/
     │    ├── Login.jsx
     │    ├── Signup.jsx
     │    ├── UploadAndAsk.jsx
     │    ├── ChatHistory.jsx
     │    └── Navbar.jsx
     |
     ├── api.js
     ├── App.jsx
     └── main.jsx


server/
 ├── main.py
 ├── auth.py
 ├── db.py
 ├── model.py
 ├── utils.py
 ├── requirements.txt
 └── job_skills.json

Future Improvements:
Persistent chat history storage
Multiple document support
User-specific FAISS indexes
Support for DOCX/TXT files
Redis caching
Deployment optimization


Learning Outcomes:

Through this project, I explored:

Building GenAI applications using RAG architecture
Working with embeddings and vector databases
Integrating LLM APIs
Designing authentication systems
Connecting React frontend with FastAPI backend
Handling document processing pipelines
