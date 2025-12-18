import asyncio
import psutil, os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List

current_interval = 1.0

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    async def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()
app = FastAPI()

async def broadcast():
    global current_interval
    while True:
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent
        await manager.broadcast({"cpu" : cpu, "memory" : memory, "disk": disk})
        await asyncio.sleep(current_interval)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(broadcast())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    global current_interval
    try:
        while True:
            data = await websocket.receive_text()
            if data == "fast":
                current_interval = 0.1
            elif data == "slow":
                current_interval = 3.0
    except WebSocketDisconnect:
        await manager.disconnect(websocket)