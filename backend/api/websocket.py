from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter()

class ConnectionManager:
    """
    WebSocket 连接管理器
    负责处理 WebSocket 连接、断开和消息广播
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        """
        向所有连接的客户端广播消息
        """
        # 创建副本以避免在迭代时修改列表（虽然这里是同步迭代，但在async环境中更安全）
        connections = self.active_connections[:]
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                # 连接出错时尝试断开并移除
                try:
                    self.disconnect(connection)
                except:
                    pass

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # 保持连接活跃，并处理心跳
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
