# database/mongo.py
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

class MongoDB:
    def __init__(self):
        self.client = AsyncIOMotorClient(Config.MONGO_URI)
        self.db = self.client["AAKASH_FIGHT_BOT"]
        self.users = self.db["users"]
        self.accounts = self.db["accounts"]

    async def get_user(self, user_id: int):
        user = await self.users.find_one({"_id": user_id})
        if not user:
            user = {
                "_id": user_id, "is_approved": False, "is_banned": False,
                "record_group_id": None,
                "effects": {"level": 100, "bass": 0, "treble": 0, "gain": 0, "overdrive": 0, "echo": "off"}
            }
            await self.users.insert_one(user)
        return user

    async def approve_user(self, user_id: int):
        await self.users.update_one({"_id": user_id}, {"$set": {"is_approved": True}}, upsert=True)

    async def update_effect(self, user_id: int, effect_name: str, value):
        await self.users.update_one({"_id": user_id}, {"$set": {f"effects.{effect_name}": value}})

    async def reset_effects(self, user_id: int):
        default_fx = {"level": 100, "bass": 0, "treble": 0, "gain": 0, "overdrive": 0, "echo": "off"}
        await self.users.update_one({"_id": user_id}, {"$set": {"effects": default_fx}})

    async def save_account(self, user_id: int, phone: str, session: str):
        await self.accounts.update_one(
            {"owner_id": user_id, "phone": phone},
            {"$set": {"session_string": session, "is_active": True}},
            upsert=True
        )

    async def get_accounts(self, user_id: int):
        cursor = self.accounts.find({"owner_id": user_id})
        return await cursor.to_list(length=10)

db = MongoDB()