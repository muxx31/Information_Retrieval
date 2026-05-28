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
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
qa_chain = None
PDF_PATH = "storage/temp.pdf"

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
    os.makedirs("storage", exist_ok=True)
    with open(PDF_PATH, "wb") as f:
        f.write(contents)
    text = extract_text_from_pdf(PDF_PATH)
    global qa_chain
    qa_chain = create_qa_chain(text)
    return {"message": "PDF processed successfully"}

@app.post("/ask")
async def ask_question(q: Question, user=Depends(get_current_user)):
    global qa_chain
    if not qa_chain:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please upload a PDF first.")
    answer = qa_chain.invoke({"question": q.query})["result"]
    return {"answer": answer}
