import asyncio
from typing import List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.loop = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.loop = asyncio.get_running_loop()

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass
    # Allows sync threads to trigger a websocket broadcast on the main loop
    def thread_safe_broadcast(self, message: dict):
        
        if self.loop and self.active_connections:
            asyncio.run_coroutine_threadsafe(self.broadcast(message), self.loop)

manager = ConnectionManager()
