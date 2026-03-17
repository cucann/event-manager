from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import os
import asyncio

# Подключение к MongoDB через переменные окружения
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:mongopass123@mongodb-service:27017")
DB_NAME = os.getenv("DB_NAME", "events_db")
COLLECTION_NAME = "events"

# FastAPI приложение
app = FastAPI(title="Event Manager API")

# CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модель данных
class EventModel(BaseModel):
    title: str = Field(..., description="Название события")
    date: str = Field(..., description="Дата проведения (YYYY-MM-DD)")
    time: str = Field(..., description="Время проведения (HH:MM)")
    location: str = Field(..., description="Место проведения")
    participants: List[str] = Field(default=[], description="Список участников")
    description: Optional[str] = Field(None, description="Описание")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class EventInDB(EventModel):
    id: str

# Подключение к MongoDB при старте
@app.on_event("startup")
async def startup_db_client():
    print(f"Connecting to MongoDB: {MONGO_URI}")
    app.mongodb_client = AsyncIOMotorClient(MONGO_URI)
    app.mongodb = app.mongodb_client[DB_NAME]
    
    # Проверка подключения
    try:
        await app.mongodb_client.admin.command('ping')
        print("✅ Successfully connected to MongoDB!")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()

# Эндпоинты
@app.get("/")
async def root():
    return {"message": "Event Manager API", "status": "running"}

@app.get("/events", response_model=List[EventInDB])
async def get_events():
    """Получить все события"""
    events = []
    cursor = app.mongodb[COLLECTION_NAME].find()
    async for document in cursor:
        document["id"] = str(document.pop("_id"))
        events.append(EventInDB(**document))
    return events

@app.post("/events", response_model=EventInDB)
async def create_event(event: EventModel):
    """Создать новое событие"""
    event_dict = event.dict()
    result = await app.mongodb[COLLECTION_NAME].insert_one(event_dict)
    
    # Получаем созданный документ
    created_event = await app.mongodb[COLLECTION_NAME].find_one({"_id": result.inserted_id})
    created_event["id"] = str(created_event.pop("_id"))
    
    return EventInDB(**created_event)

@app.get("/events/{event_id}")
async def get_event(event_id: str):
    """Получить событие по ID"""
    from bson import ObjectId
    
    try:
        event = await app.mongodb[COLLECTION_NAME].find_one({"_id": ObjectId(event_id)})
        if event:
            event["id"] = str(event.pop("_id"))
            return event
        raise HTTPException(status_code=404, detail="Event not found")
    except:
        raise HTTPException(status_code=400, detail="Invalid event ID")

@app.delete("/events/{event_id}")
async def delete_event(event_id: str):
    """Удалить событие"""
    from bson import ObjectId
    
    try:
        result = await app.mongodb[COLLECTION_NAME].delete_one({"_id": ObjectId(event_id)})
        if result.deleted_count:
            return {"message": "Event deleted"}
        raise HTTPException(status_code=404, detail="Event not found")
    except:
        raise HTTPException(status_code=400, detail="Invalid event ID")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
