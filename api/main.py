from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from bson import ObjectId
from jose import jwt, JWTError

import models
import auth

# --- Load Environment ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

app = FastAPI(title="FinFresh API")

# --- CORS (React Frontend-ku allow panrathu) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB Connection
mongo_url = os.getenv("MONGODB_URL")
client = MongoClient(mongo_url)
db = client.finfresh_db

# --- AUTH LOGIC (JWT) ---
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

@app.get("/")
def read_root():
    return {"message": "FinFresh API is running!"}

# --- AUTH ENDPOINTS ---
@app.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register_user(user: models.UserRegister):
    if db.users.find_one({"email": user.email}):
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
    token = auth.create_access_token(data={"sub": user_id})
    return {"token": token, "user": {"id": user_id, "name": user.name, "email": user.email}}

@app.post("/auth/login")
def login_user(user: models.UserLogin):
    db_user = db.users.find_one({"email": user.email})
    if not db_user or not auth.verify_password(user.password, db_user["passwordHash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user_id = str(db_user["_id"])
    token = auth.create_access_token(data={"sub": user_id})
    return {"token": token, "user": {"id": user_id, "name": db_user["name"], "email": db_user["email"]}}

# --- TRANSACTIONS ---
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
    return {"id": str(result.inserted_id), **transaction.dict()}

@app.get("/transactions")
def get_transactions(user_id: str = Depends(get_current_user), page: int = 1, limit: int = 20):
    query = {"userId": ObjectId(user_id)}
    cursor = db.transactions.find(query).sort("date", -1).skip((page-1)*limit).limit(limit)
    total = db.transactions.count_documents(query)
    
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
    return {"data": data, "pagination": {"page": page, "limit": limit, "total": total}}

# --- CHALLENGE REQUIRED: GET /summary ---
@app.get("/summary")
def get_summary(user_id: str = Depends(get_current_user)):
    now = datetime.utcnow()
    start_of_month = datetime(now.year, now.month, 1)
    
    txns = list(db.transactions.find({"userId": ObjectId(user_id), "date": {"$gte": start_of_month}}))
    
    income = sum(t["amount"] for t in txns if t["type"] == "income")
    expense = sum(t["amount"] for t in txns if t["type"] == "expense")
    savings = income - expense
    rate = round((savings / income * 100), 1) if income > 0 else 0
    
    categories = {}
    for t in txns:
        if t["type"] == "expense":
            categories[t["category"]] = categories.get(t["category"], 0) + t["amount"]

    return {
        "income": income, "expense": expense, "savings": savings,
        "savingsRate": rate, "categories": categories
    }

# --- CHALLENGE REQUIRED: GET /financial-health (The Algorithm) ---
@app.get("/financial-health")
def get_financial_health(user_id: str = Depends(get_current_user)):
    oid = ObjectId(user_id)
    now = datetime.utcnow()
    start_of_month = datetime(now.year, now.month, 1)

    all_txns = list(db.transactions.find({"userId": oid}))
    this_month = [t for t in all_txns if t["date"] >= start_of_month]

    # Metrics
    total_savings = sum(t["amount"] if t["type"] == "income" else -t["amount"] for t in all_txns)
    monthly_income = sum(t["amount"] for t in this_month if t["type"] == "income")
    monthly_expense = sum(t["amount"] for t in this_month if t["type"] == "expense")
    monthly_debt = sum(t["amount"] for t in this_month if t["type"] == "debt")
    monthly_invest = sum(t["amount"] for t in this_month if t["type"] == "investment")

    # 1. Emergency Fund (max 25)
    coverage = total_savings / monthly_expense if monthly_expense > 0 else 99
    ef_pts = 25 if coverage > 6 else (20 if coverage >= 3 else (10 if coverage >= 1 else 5))

    # 2. Savings Rate (max 25)
    s_rate = ((monthly_income - monthly_expense) / monthly_income * 100) if monthly_income > 0 else 0
    s_pts = 25 if s_rate > 40 else (20 if s_rate >= 20 else (10 if s_rate >= 10 else 5))

    # 3. Debt Ratio (max 25)
    d_ratio = (monthly_debt / monthly_income * 100) if monthly_income > 0 else 0
    d_pts = 25 if d_ratio < 10 else (20 if d_ratio <= 30 else (10 if d_ratio <= 50 else 5))

    # 4. Investment Ratio (max 25)
    i_ratio = (monthly_invest / monthly_income * 100) if monthly_income > 0 else 0
    i_pts = 25 if i_ratio > 30 else (20 if i_ratio >= 15 else (10 if i_ratio >= 5 else 5))

    score = ef_pts + s_pts + d_pts + i_pts
    category = "Excellent" if score >= 80 else ("Healthy" if score >= 60 else ("Moderate" if score >= 40 else "At Risk"))

    suggestions = []
    if ef_pts < 20: suggestions.append("Increase emergency fund to cover 3-6 months.")
    if i_pts < 20: suggestions.append("Try to invest at least 15% of your income.")

    return {
        "score": score, "category": category,
        "breakdown": {"emergencyFund": ef_pts, "savingsRate": s_pts, "debtRatio": d_pts, "investmentRatio": i_pts},
        "suggestions": suggestions
    }