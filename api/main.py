from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime

import models
import auth

# --- PUTHU CODE: Force Load .env ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
# -----------------------------------

app = FastAPI(title="FinFresh API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB Connection - Link varalana alert aagum
mongo_url = os.getenv("MONGODB_URL")
if not mongo_url:
    print("ALERT: MONGODB_URL is missing! Check your .env file.")
    
client = MongoClient(mongo_url)
db = client.finfresh_db

@app.get("/")
def read_root():
    return {"message": "FinFresh API is running!"}

# --- AUTH ENDPOINTS ---

@app.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register_user(user: models.UserRegister):
    existing_user = db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pw = auth.get_password_hash(user.password)
    
    new_user = {
        "name": user.name,
        "email": user.email,
        "passwordHash": hashed_pw,
        "createdAt": datetime.utcnow()
    }
    result = db.users.insert_one(new_user)
    
    user_id = str(result.inserted_id)
    access_token = auth.create_access_token(data={"sub": user_id})
    
    return {
        "token": access_token,
        "user": {"id": user_id, "name": user.name, "email": user.email}
    }

@app.post("/auth/login")
def login_user(user: models.UserLogin):
    db_user = db.users.find_one({"email": user.email})
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not auth.verify_password(user.password, db_user["passwordHash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user_id = str(db_user["_id"])
    access_token = auth.create_access_token(data={"sub": user_id})
    
    return {
        "token": access_token,
        "user": {"id": user_id, "name": db_user["name"], "email": db_user["email"]}
    }