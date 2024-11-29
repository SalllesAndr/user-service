import os
import azure.functions as func
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from models import User, UserCreate, UserUpdate, UserLogin
from typing import List
from utils import generate_custom_id
import bcrypt

app = FastAPI()

# API Key
API_KEY = os.getenv("API_KEY")
API_KEY_NAME = "X-API-Key"

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_DETAILS = os.getenv("MONGO_DETAILS")
client = AsyncIOMotorClient(MONGO_DETAILS)
database = client["bootcamp_db"]
user_collection = database.get_collection("users")

@app.middleware("http")
async def api_key_validator(request: Request, call_next):
    if API_KEY_NAME in request.headers:
        provided_api_key = request.headers[API_KEY_NAME]
        if provided_api_key == API_KEY:
            response = await call_next(request)
            return response
    raise HTTPException(status_code=401, detail="Invalid or missing API Key")

# Utility functions
def user_helper(user) -> dict:
    return {
        "user_id": user["user_id"],
        "isStudent": user["isStudent"],
        "email": user["email"],
        "username": user["username"],
    }

# Password hashing utilities
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# Routes

@app.post("/signup", response_model=dict)
async def signup(user: UserCreate):
    existing_user = await user_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Generate user_id based on isStudent flag (signup is for students)
    user_id = generate_custom_id("stud")
    
    user_dict = user.dict()
    user_dict["password"] = hash_password(user.password)
    user_dict["user_id"] = user_id
    user_dict["isStudent"] = True  # Signup is for students
    
    await user_collection.insert_one(user_dict)
    
    return {
        "message": "User created successfully",
        "user": user_helper(user_dict)
    }

@app.post("/login", response_model=dict)
async def login(credentials: UserLogin):
    user = await user_collection.find_one({"email": credentials.email})
    if user and verify_password(credentials.password, user["password"]):
        return {"message": "Login successful", "user_id": user["user_id"]}
    raise HTTPException(status_code=401, detail="Invalid email or password")

@app.post("/createUser", response_model=dict)
async def create_user(user: UserCreate):
    existing_user = await user_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Determine if creating a student or professor
    # For example, if you have a way to distinguish, else default to professor
    # Here, let's assume 'createUser' creates professors
    user_id = generate_custom_id("prof")
    
    user_dict = user.dict()
    user_dict["password"] = hash_password(user.password)
    user_dict["user_id"] = user_id
    user_dict["isStudent"] = False  # Professors
    
    await user_collection.insert_one(user_dict)
    
    return {
        "message": "Professor created successfully",
        "user": user_helper(user_dict)
    }

@app.delete("/deleteUser/{user_id}", response_model=dict)
async def delete_user(user_id: str):
    result = await user_collection.delete_one({"user_id": user_id})
    if result.deleted_count:
        return {"status": "User deleted"}
    raise HTTPException(status_code=404, detail="User not found")

@app.put("/updateUser/{user_id}", response_model=dict)
async def update_user(user_id: str, user_data: UserUpdate):
    user = await user_collection.find_one({"user_id": user_id})
    if user:
        await user_collection.update_one(
            {"user_id": user_id}, {"$set": user_data.dict(exclude_unset=True)}
        )
        updated_user = await user_collection.find_one({"user_id": user_id})
        return user_helper(updated_user)
    raise HTTPException(status_code=404, detail="User not found")

@app.get("/getUserByID/{user_id}", response_model=dict)
async def get_user_by_id(user_id: str):
    user = await user_collection.find_one({"user_id": user_id})
    if user:
        return user_helper(user)
    raise HTTPException(status_code=404, detail="User not found")

@app.get("/getUsers", response_model=List[dict])
async def get_users():
    users = []
    async for user in user_collection.find():
        users.append(user_helper(user))
    return users

@app.get("/getStudents", response_model=List[dict])
async def get_students():
    students = []
    async for user in user_collection.find({"isStudent": True}):
        students.append(user_helper(user))
    return students

@app.get("/getProfessors", response_model=List[dict])
async def get_professors():
    professors = []
    async for user in user_collection.find({"isStudent": False}):
        professors.append(user_helper(user))
    return professors
