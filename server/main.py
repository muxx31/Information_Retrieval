# uvicorn main:app --reload
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from model import User, Question
from utils import extract_text_from_pdf, create_qa_chain
from auth import (
    verify_password, create_access_token, decode_access_token,
    get_user_by_email, create_user
)
import os
import tempfile
from collections import OrderedDict
from dotenv import load_dotenv
from fastapi.concurrency import run_in_threadpool

load_dotenv()

app = FastAPI()

# Per-user QA chains (keyed by email), in memory. Capped so memory can't grow unbounded;
# the least-recently-used user is evicted and must re-upload.
MAX_USERS_IN_MEMORY = int(os.getenv("MAX_USERS_IN_MEMORY", "20"))
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))
user_chains: "OrderedDict[str, object]" = OrderedDict()

# Comma-separated list of allowed frontend origins
ALLOWED_ORIGINS = [
    o.strip().rstrip("/")
    for o in os.getenv("FRONTEND_URL", "http://localhost:5173").split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
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
    await create_user(user.email, user.password)
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
        raise
    except Exception as e:
        print(f"LOGIN ERROR: {e}")
        raise HTTPException(status_code=500, detail="Server error during login")

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...), user=Depends(get_current_user)):
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File too large (max {MAX_UPLOAD_MB} MB)")

    # Per-request temp file so concurrent users never overwrite each other
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name
    try:
        text = await run_in_threadpool(extract_text_from_pdf, tmp_path)
    finally:
        os.remove(tmp_path)

    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract any text from this PDF.")

    chain = await run_in_threadpool(create_qa_chain, text)
    user_chains[user] = chain
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
    result = await run_in_threadpool(chain.invoke, {"question": q.query})
    return {"answer": result["result"]}
