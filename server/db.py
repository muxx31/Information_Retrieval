import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Must run before reading env vars, regardless of import order
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("MONGO_URI environment variable is not set")

client = AsyncIOMotorClient(MONGO_URI)
# Uses the database named in the URI (falls back to genai_project)
db = client.get_default_database(default="genai_project")
users_collection = db["users"]
