from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from db import users_collection  # Your MongoDB collection

SECRET_KEY = "njdnqwjndjkwwdbnjwbnd"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None

async def get_user_by_email(email: str):
    return await users_collection.find_one({"email": email})

async def create_user(email: str, password: str):
    hashed = get_password_hash(password)
    user = {"email": email, "password": hashed}
    await users_collection.insert_one(user)
    return user
