from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime
from bson import ObjectId
from jose import jwt, JWTError

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

# MongoDB Connection
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

# --- TOKEN VERIFICATION ---
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, os.getenv("JWT_SECRET", "fallback_secret"), algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# --- TRANSACTIONS API ---
@app.post("/transactions", status_code=status.HTTP_201_CREATED)
def create_transaction(transaction: models.TransactionCreate, user_id: str = Depends(get_current_user)):
    new_txn = {
        "userId": ObjectId(user_id),
        "type": transaction.type.value,
        "category": transaction.category,
        "amount": transaction.amount,
        "date": datetime.combine(transaction.date, datetime.min.time()),
        "description": transaction.description,
        "createdAt": datetime.utcnow()
    }
    
    result = db.transactions.insert_one(new_txn)
    
    return {
        "id": str(result.inserted_id),
        "type": transaction.type,
        "category": transaction.category,
        "amount": transaction.amount,
        "date": transaction.date,
        "description": transaction.description
    }

@app.get("/transactions")
def get_transactions(user_id: str = Depends(get_current_user)):
    query = {"userId": ObjectId(user_id)}
    cursor = db.transactions.find(query).sort("date", -1)
    
    data = []
    for doc in cursor:
        data.append({
            "id": str(doc["_id"]),
            "type": doc["type"],
            "category": doc["category"],
            "amount": doc["amount"],
            "date": doc["date"].strftime("%Y-%m-%d"),
            "description": doc.get("description", "")
        })
        
    return {"data": data}

@app.get("/health-score")
def get_health_score(user_id: str = Depends(get_current_user)):
    from bson import ObjectId
    query = {"userId": ObjectId(user_id)}
    transactions = list(db.transactions.find(query))
    
    # 1. Varavu, Selavu, Investment ellam kooturathu (Sum calculation)
    total_income = sum(t["amount"] for t in transactions if t.get("type") == "income")
    total_expense = sum(t["amount"] for t in transactions if t.get("type") == "expense")
    total_investment = sum(t["amount"] for t in transactions if t.get("type") == "investment")
    
    # 2. Health Score Logic
    if total_income == 0:
        score = 0
        status = "Need Data"
        tip = "Please add your income to calculate the health score."
    else:
        # Meetham irukkum panam (Savings)
        savings = total_income - total_expense
        savings_percentage = (savings / total_income) * 100
        
        if savings_percentage >= 30:
            score = 90
            status = "Excellent"
            tip = "Great job! You have a very healthy savings rate. Keep investing!"
        elif savings_percentage >= 15:
            score = 70
            status = "Good"
            tip = "You are doing well, but try to cut down unnecessary expenses to reach a 30% savings rate."
        elif savings_percentage >= 0:
            score = 50
            status = "Needs Improvement"
            tip = "Warning: You are spending almost everything you earn. Start budgeting!"
        else:
            score = 30
            status = "Critical"
            tip = "DANGER: You are spending more than you earn! High risk of debt."
            
    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "total_investment": total_investment,
        "savings_percentage": round(savings_percentage, 2) if total_income > 0 else 0,
        "health_score": score,
        "status": status,
        "financial_tip": tip
    }