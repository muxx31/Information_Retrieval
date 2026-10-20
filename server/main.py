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

load_dotenv()

app = FastAPI()

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

    except Exception as e:
        print(f"LOGIN ERROR: {e}")
        raise HTTPException(status_code=500, detail="Server error during login")

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...), user=Depends(get_current_user)):
    contents = await file.read()
    # Unique temp file per request so concurrent uploads can't overwrite each other
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name
    try:
        text = extract_text_from_pdf(tmp_path)
    finally:
        os.remove(tmp_path)
    user_chains[user] = create_qa_chain(text)
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
    answer = chain.invoke({"question": q.query})["result"]
    return {"answer": answer}
