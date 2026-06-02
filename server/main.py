"""
CapyTalk Server — FastAPI + WebSocket
Запуск: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import Dict
import json
from datetime import datetime

app = FastAPI(title="CapyTalk Server")

# Хранилище подключённых клиентов
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.usernames: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, username: str):
        await websocket.accept()
        self.active_connections[username] = websocket
        self.usernames[websocket] = username
        await self.broadcast_system(f"🐹 {username} присоединился к беседе")

    def disconnect(self, websocket: WebSocket):
        username = self.usernames.get(websocket, "кто-то")
        if username in self.active_connections:
            del self.active_connections[username]
        if websocket in self.usernames:
            del self.usernames[websocket]
        return username

    async def broadcast(self, message: dict, exclude: WebSocket = None):
        disconnected = []
        for username, connection in self.active_connections.items():
            if connection != exclude:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.append(username)
        # Чистим отвалившихся
        for username in disconnected:
            if username in self.active_connections:
                del self.active_connections[username]

    async def broadcast_system(self, text: str):
        await self.broadcast({
            "type": "system",
            "text": text,
            "time": datetime.now().strftime("%H:%M")
        })

manager = ConnectionManager()

@app.get("/")
async def root():
    return {"message": "🐹 CapyTalk Server is running", "status": "ok"}

@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await manager.connect(websocket, username)
    
    # Отправляем историю (заглушка — в реальном проекте из БД)
    await websocket.send_json({
        "type": "system",
        "text": f"🐹 Добро пожаловать в CapyTalk, {username}!",
        "time": datetime.now().strftime("%H:%M")
    })
    
    try:
        while True:
            data = await websocket.receive_json()
            message = {
                "type": "message",
                "username": username,
                "text": data.get("text", ""),
                "time": datetime.now().strftime("%H:%M")
            }
            await manager.broadcast(message)
    except WebSocketDisconnect:
        username = manager.disconnect(websocket)
        await manager.broadcast_system(f"👋 {username} покинул беседу")
    except Exception as e:
        username = manager.disconnect(websocket)
        await manager.broadcast_system(f"👋 {username} покинул беседу")
