import json
import os
import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# === CONFIGURATION ===
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")
DATA_PATH = os.path.join(os.path.dirname(__file__), "job_skills.json")

# === LOAD JOB SKILLS DATA ===
try:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        JOB_SKILLS_DATA = json.load(f)
except Exception as e:
    print(f"Failed to load job skills: {e}")
    JOB_SKILLS_DATA = []

# === EXTRACT TEXT FROM PDF ===
def extract_text_from_pdf(file_path: str) -> str:
    try:
        doc = fitz.open(file_path)
        return "".join(page.get_text() for page in doc)
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

# === BUILD VECTORSTORE IN MEMORY ===
def get_vectorstore(resume_text: str):
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=30)
    docs = splitter.create_documents([resume_text], metadatas=[{"source": "resume"}])

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    vectorstore = FAISS.from_documents(docs, embeddings)
    return vectorstore

# === GENERAL DOCUMENT ANALYZER PROMPT TEMPLATE ===
def build_prompt_template():
    prompt = """
You are an intelligent document analyzer. Your task is to analyze the provided document content and answer questions based on it.

Instructions:
1. If the question is related to the document content, provide a brief and accurate answer based on the document.
2. If the question is not related to the document content, clearly state that the question is not document-specific and provide a brief generic answer based on your general knowledge.
3. Keep all answers brief and to the point.

Document Content:
{context}

Question: {question}

Answer:"""
    
    return PromptTemplate(template=prompt, input_variables=["context", "question"])

# === OPTIONAL OUTPUT CLEANER ===
def clean_output(answer: str) -> str:
    lines = answer.strip().split("\n")
    for line in lines:
        for job in JOB_SKILLS_DATA:
            if job["title"].lower() in line.lower():
                return job["title"]
    return lines[0].strip()

# === CREATE QA CHAIN ===
def create_qa_chain(resume_text: str):
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not found in environment variables")
    
    vectorstore = get_vectorstore(resume_text)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    # Initialize OpenRouter LLM via OpenAI-compatible API
    llm = ChatOpenAI(
        model=OPENROUTER_MODEL,
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.7,
        max_tokens=512,
        default_headers={
            "HTTP-Referer": "http://localhost:3000",  # Optional: for analytics
            "X-Title": "PDF Resume Analyzer",  # Optional: for analytics
        }
    )

    prompt_template = build_prompt_template()
    qa_chain = load_qa_chain(llm, chain_type="stuff", prompt=prompt_template)

    return RetrievalQA(
        combine_documents_chain=qa_chain,
        retriever=retriever,
        input_key="question",
        return_source_documents=False,
    )

# === MAIN TEST ===
if __name__ == "__main__":
    resume_pdf_path = "sample_resume.pdf"  # Change to your actual resume path
    resume_text = extract_text_from_pdf(resume_pdf_path)

    if not resume_text:
        print("No text extracted from resume.")
        exit()

    try:
        qa = create_qa_chain(resume_text)
        question = "What job role is suitable for me?"
        raw_answer = qa.run({"question": question})

        print("Raw model output:", raw_answer)
        print("Cleaned answer:", clean_output(raw_answer))
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please set OPENROUTER_API_KEY in your .env file")
