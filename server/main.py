# uvicorn main:app --reload
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from model import User, Question
from utils import extract_text_from_pdf, create_qa_chain
from auth import (
    verify_password, create_access_token, decode_access_token,
    get_user_by_email, create_user
)
import logging
import os
import tempfile
from collections import OrderedDict
from dotenv import load_dotenv
from pymongo.errors import DuplicateKeyError
from db import users_collection

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))

@app.on_event("startup")
async def ensure_indexes():
    # Unique index makes duplicate signups impossible even under a race condition
    try:
        await users_collection.create_index("email", unique=True)
    except Exception:
        logger.exception("Could not create unique index on users.email")

# One QA chain per user (keyed by email) so users never see each other's documents.
# Capped (least-recently-used is dropped) so memory can't grow without limit.
MAX_USERS_IN_MEMORY = int(os.getenv("MAX_USERS_IN_MEMORY", "10"))
user_chains = OrderedDict()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = authorization.split(" ")[1]
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return email

@app.get("/")
def root():
    return {"message": "Backend is running"}

@app.post("/signup")
async def signup(user: User):
    existing = await get_user_by_email(user.email)
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    try:
        await create_user(user.email, user.password)
    except DuplicateKeyError:
        # Two simultaneous signups can both pass the check above
        raise HTTPException(status_code=400, detail="User already exists")
    return {"message": "User created"}

@app.post("/login")
async def login(user: User):
    try:
        db_user = await get_user_by_email(user.email)
        if not db_user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        password_hash = db_user.get("password") if isinstance(db_user, dict) else db_user.password

        if not verify_password(user.password, password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_access_token({"sub": user.email})
        return {"access_token": token, "token_type": "bearer"}

    except HTTPException:
        # Let deliberate errors (e.g. 401) pass through instead of becoming 500
        raise
    except Exception:
        logger.exception("Unexpected error during login")
        raise HTTPException(status_code=500, detail="Server error during login")

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...), user=Depends(get_current_user)):
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File too large (max {MAX_UPLOAD_MB} MB).")
    # Unique temp file per request so concurrent uploads can't overwrite each other
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name
    try:
        text = extract_text_from_pdf(tmp_path)
    finally:
        os.remove(tmp_path)
    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail="Could not read any text from this PDF (it may be scanned or corrupted).",
        )
    try:
        user_chains[user] = create_qa_chain(text)
    except ValueError:
        # Missing API key etc. is a server configuration problem, not the user's fault
        logger.exception("QA chain configuration error")
        raise HTTPException(status_code=500, detail="Server is not configured correctly.")
    except Exception:
        logger.exception("Failed to process PDF")
        raise HTTPException(status_code=500, detail="Failed to process the PDF.")
    user_chains.move_to_end(user)
    while len(user_chains) > MAX_USERS_IN_MEMORY:
        user_chains.popitem(last=False)
    return {"message": "PDF processed successfully"}

@app.post("/ask")
async def ask_question(q: Question, user=Depends(get_current_user)):
    chain = user_chains.get(user)
    if not chain:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please upload a PDF first.")
    user_chains.move_to_end(user)
    try:
        answer = chain.invoke({"question": q.query})["result"]
    except Exception:
        # Free-tier LLM calls fail often (rate limits, timeouts, outages)
        logger.exception("LLM call failed")
        raise HTTPException(
            status_code=503,
            detail="The AI service is temporarily unavailable. Please try again.",
        )
    return {"answer": answer}
