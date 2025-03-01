from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from pymongo import MongoClient
from datetime import datetime, timedelta
import random

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # اجازه به وب‌اپت
    allow_credentials=True,
    allow_methods=["*"],  # اجازه همه متدها (GET, POST, ...)
    allow_headers=["*"],  # اجازه همه هدرها
)

client = MongoClient("mongodb://localhost:27017/")
db = client["mining_game"]
users = db["users"]
blocks = db["blocks"]

TOKEN = "7920386335:AAF41_AbPmwQengnAvQD0M5cbaQB-JtmApA"  # توکن باتت رو اینجا بذار

# ثبت کاربر جدید
@app.post("/register/{user_id}")
async def register(user_id: str):
    if not users.find_one({"user_id": user_id}):
        users.insert_one({"user_id": user_id, "level": 1, "tokens": 0})
    return {"message": "ثبت شدید!"}

# شروع بلاک
@app.post("/start_block/{user_id}")
async def start_block(user_id: str):
    user = users.find_one({"user_id": user_id})
    if not user:
        return {"message": "اول ثبت‌نام کن!"}
    block = blocks.find_one({"active": True})
    if not block:
        blocks.insert_one({"active": True, "users": [], "start_time": datetime.now()})
    blocks.update_one({"active": True}, {"$push": {"users": {"id": user_id, "level": user["level"]}}})
    return {"message": "به بلاک اضافه شدی!"}

# پایان بلاک و تقسیم پاداش
@app.get("/end_block")
async def end_block():
    block = blocks.find_one({"active": True})
    if block and (datetime.now() - block["start_time"]) >= timedelta(minutes=1):
        total_level = sum(user["level"] for user in block["users"])
        reward_per_level = 20 / total_level
        for user in block["users"]:
            user_reward = reward_per_level * user["level"]
            users.update_one({"user_id": user["id"]}, {"$inc": {"tokens": user_reward}})
        blocks.update_one({"active": True}, {"$set": {"active": False}})
    return {"message": "بلاک تمام شد!"}

# ارتقا سطح
@app.post("/upgrade/{user_id}")
async def upgrade(user_id: str):
    user = users.find_one({"user_id": user_id})
    if not user:
        return {"message": "اول ثبت‌نام کن!"}
    cost = user["level"] * 5  # مثلاً 5 توکن برای هر سطح
    if user["tokens"] >= cost:
        users.update_one({"user_id": user_id}, {"$inc": {"level": 1, "tokens": -cost}})
        return {"message": f"سطحت به {user['level'] + 1} ارتقا یافت!"}
    return {"message": "توکن کافی نداری!"}