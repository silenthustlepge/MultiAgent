from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import httpx
import asyncio
import json
import random
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Together.ai API Keys Pool
API_KEYS_POOL = [
    {
        "keyId": "together-ai-CartoonKeeda",
        "apiKey": "tgp_v1_fIg_qVDqihEaY5SSBQzx_CSFFHA2w_W1faFCIHjcn3Y",
        "provider": "together.ai",
        "rateLimitPerMinute": 60,
        "lastUsed": 0,
        "requestCount": 0
    },
    {
        "keyId": "together-key-itspg",
        "apiKey": "tgp_v1_nU0xsEVawSO2Gk66Q_IM7DLsLcQ5HFH36KTmtrD9ME4",
        "provider": "together.ai",
        "rateLimitPerMinute": 60,
        "lastUsed": 0,
        "requestCount": 0
    },
    {
        "keyId": "together-key-OneLastTry",
        "apiKey": "tgp_v1_MVngo4oDIOXZdedYMSW3CnoY2XkKWLf5k9YQAyMUjf8",
        "provider": "together.ai",
        "rateLimitPerMinute": 60,
        "lastUsed": 0,
        "requestCount": 0
    },
    {
        "keyId": "together-key-SilentHustle",
        "apiKey": "tgp_v1_DtPBgpNq2wSmwzMMnaq0hHTxRP7qeu4y9DnTE0Izu80",
        "provider": "together.ai",
        "rateLimitPerMinute": 60,
        "lastUsed": 0,
        "requestCount": 0
    },
    {
        "keyId": "together-key-pgCAN",
        "apiKey": "tgp_v1_EUHOklglfPyZTqt3mannWAg1Oe10IKrQkV1TCHPPrKc",
        "provider": "together.ai",
        "rateLimitPerMinute": 60,
        "lastUsed": 0,
        "requestCount": 0
    },
    {
        "keyId": "together-key-MRGEdits",
        "apiKey": "tgp_v1_xDIvrbvV_F2LyTDRjYXfvRD3TcI-JoG50dTx-jZvvbY",
        "provider": "together.ai",
        "rateLimitPerMinute": 60,
        "lastUsed": 0,
        "requestCount": 0
    },
    {
        "keyId": "together-key-PTY49",
        "apiKey": "tgp_v1_xgieCS82MlcfiP0749XX9oSGaNlmB17UkhsLZsSA9N8",
        "provider": "together.ai",
        "rateLimitPerMinute": 60,
        "lastUsed": 0,
        "requestCount": 0
    },
    {
        "keyId": "together-key-ShopsterZone",
        "apiKey": "tgp_v1_YRCuEbdYFCXWpOgOfLuR19p_XjM5ViS2hw26J3kj-Rc",
        "provider": "together.ai",
        "rateLimitPerMinute": 60,
        "lastUsed": 0,
        "requestCount": 0
    }
]

# Agent Models Configuration
AGENT_MODELS = {
    "strategist": {
        "name": "Strategist",
        "model": "deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
        "role": "Planning and strategic reasoning",
        "persona": "You are a strategic thinker and planner. You analyze problems deeply, consider multiple perspectives, and create structured approaches. You ask probing questions and think several steps ahead.",
        "color": "#3B82F6"
    },
    "creator": {
        "name": "Creator", 
        "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        "role": "Fast content generation and execution",
        "persona": "You are a creative and productive generator. You take ideas and quickly turn them into concrete content, stories, or solutions. You're action-oriented and love bringing concepts to life.",
        "color": "#10B981"
    },
    "analyst": {
        "name": "Analyst",
        "model": "lgai/exaone-3-5-32b-instruct", 
        "role": "Critical analysis and diverse perspectives",
        "persona": "You are a critical thinker and analyst. You examine ideas from multiple angles, identify potential issues, and provide balanced perspectives. You ask 'what if' questions and consider edge cases.",
        "color": "#F59E0B"
    },
    "visualizer": {
        "name": "Visualizer",
        "model": "black-forest-labs/FLUX.1-schnell-Free",
        "role": "Visual content and image generation",
        "persona": "You are a visual artist and designer. You create compelling images and help visualize concepts. You think in terms of composition, color, and visual storytelling.",
        "color": "#EF4444"
    }
}

# Connection Manager for WebSockets
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

# Models
class AgentType(str, Enum):
    STRATEGIST = "strategist"
    CREATOR = "creator" 
    ANALYST = "analyst"
    VISUALIZER = "visualizer"

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str
    agent_type: Optional[AgentType] = None
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    is_user: bool = False
    image_url: Optional[str] = None

class ConversationRequest(BaseModel):
    topic: str
    agents: List[AgentType]
    message_count: int = 10

class ImageGenerationRequest(BaseModel):
    prompt: str
    conversation_id: str

# Key Pool Management
def get_next_available_key():
    """Get the next available API key using round-robin with rate limiting"""
    current_time = datetime.utcnow().timestamp()
    
    # Reset counters every minute
    for key_info in API_KEYS_POOL:
        if current_time - key_info["lastUsed"] > 60:
            key_info["requestCount"] = 0
    
    # Find key with available capacity
    available_keys = [k for k in API_KEYS_POOL if k["requestCount"] < k["rateLimitPerMinute"]]
    
    if not available_keys:
        # All keys are rate limited, return the one with lowest usage
        return min(API_KEYS_POOL, key=lambda k: k["requestCount"])
    
    # Return the least recently used key
    selected_key = min(available_keys, key=lambda k: k["lastUsed"])
    selected_key["lastUsed"] = current_time
    selected_key["requestCount"] += 1
    
    return selected_key

# Together.ai API Integration
async def call_together_ai(prompt: str, model: str, max_tokens: int = 1000):
    """Make API call to Together.ai"""
    key_info = get_next_available_key()
    
    headers = {
        "Authorization": f"Bearer {key_info['apiKey']}",
        "Content-Type": "application/json"
    }
    
    # Check if it's an image generation model
    if "FLUX" in model:
        payload = {
            "model": model,
            "prompt": prompt,
            "width": 1024,
            "height": 768,
            "steps": 4,
            "n": 1
        }
        url = "https://api.together.xyz/v1/images/generations"
    else:
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
        url = "https://api.together.xyz/v1/chat/completions"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            if "FLUX" in model:
                # Image generation response
                if "data" in result and len(result["data"]) > 0:
                    return result["data"][0]["url"]
                return None
            else:
                # Text generation response
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                return "No response generated"
                
        except httpx.HTTPError as e:
            logger.error(f"API call failed: {e}")
            return f"Error: API call failed - {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return f"Error: {str(e)}"

# Agent System
async def generate_agent_response(agent_type: AgentType, conversation_context: str, topic: str):
    """Generate response from specific agent"""
    agent_config = AGENT_MODELS[agent_type.value]
    
    prompt = f"""
    {agent_config['persona']}

    Topic: {topic}
    
    Previous conversation context:
    {conversation_context}
    
    Please provide your perspective on this topic. Keep your response focused, insightful, and true to your role as {agent_config['name']}.
    Respond in 2-3 sentences maximum.
    """
    
    response = await call_together_ai(prompt, agent_config['model'])
    return response

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Multi-Agent Chat Platform API"}

@api_router.get("/agents")
async def get_agents():
    """Get available agent types and their configurations"""
    return AGENT_MODELS

@api_router.post("/conversation/start")
async def start_conversation(request: ConversationRequest):
    """Start a new multi-agent conversation"""
    conversation_id = str(uuid.uuid4())
    
    # Store conversation in database
    conversation_doc = {
        "id": conversation_id,
        "topic": request.topic,
        "agents": [agent.value for agent in request.agents],
        "message_count": request.message_count,
        "created_at": datetime.utcnow(),
        "status": "active"
    }
    
    await db.conversations.insert_one(conversation_doc)
    
    return {"conversation_id": conversation_id, "status": "started"}

@api_router.post("/conversation/{conversation_id}/message")
async def add_user_message(conversation_id: str, message: dict):
    """Add a user message to the conversation"""
    chat_message = ChatMessage(
        conversation_id=conversation_id,
        content=message["content"],
        is_user=True
    )
    
    # Save to database
    message_dict = chat_message.dict()
    message_dict["timestamp"] = message_dict["timestamp"].isoformat()
    await db.messages.insert_one(message_dict)
    
    # Remove MongoDB _id for JSON serialization
    if "_id" in message_dict:
        del message_dict["_id"]
    
    # Broadcast to WebSocket connections
    await manager.broadcast(json.dumps({
        "type": "user_message",
        "data": message_dict
    }))
    
    return {"status": "message_added"}

@api_router.get("/conversation/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str):
    """Get all messages for a conversation"""
    messages = await db.messages.find(
        {"conversation_id": conversation_id}
    ).sort("timestamp", 1).to_list(1000)
    
    # Convert MongoDB documents to ChatMessage objects, removing _id
    result = []
    for msg in messages:
        if "_id" in msg:
            del msg["_id"]
        result.append(ChatMessage(**msg))
    
    return result

@api_router.post("/conversation/{conversation_id}/generate")
async def generate_agent_conversation(conversation_id: str):
    """Generate a multi-agent conversation"""
    
    # Get conversation details
    conversation = await db.conversations.find_one({"id": conversation_id})
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get existing messages for context
    existing_messages = await db.messages.find(
        {"conversation_id": conversation_id}
    ).sort("timestamp", 1).to_list(1000)
    
    context = "\n".join([f"{msg.get('agent_type', 'User')}: {msg['content']}" for msg in existing_messages[-5:]])
    
    agents = [AgentType(agent) for agent in conversation["agents"]]
    topic = conversation["topic"]
    
    # Generate responses from each agent
    for i in range(conversation["message_count"]):
        for agent_type in agents:
            try:
                response = await generate_agent_response(agent_type, context, topic)
                
                # Create message
                chat_message = ChatMessage(
                    conversation_id=conversation_id,
                    agent_type=agent_type,
                    content=response,
                    is_user=False
                )
                
                # Save to database
                message_dict = chat_message.dict()
                message_dict["timestamp"] = message_dict["timestamp"].isoformat()
                await db.messages.insert_one(message_dict)
                
                # Remove MongoDB _id for JSON serialization
                if "_id" in message_dict:
                    del message_dict["_id"]
                
                # Broadcast to WebSocket
                message_data = message_dict.copy()
                message_data["agent_config"] = AGENT_MODELS[agent_type.value]
                
                await manager.broadcast(json.dumps({
                    "type": "agent_message",
                    "data": message_data
                }))
                
                # Update context
                context += f"\n{AGENT_MODELS[agent_type.value]['name']}: {response}"
                
                # Small delay between messages
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error generating response for {agent_type}: {e}")
                continue
    
    return {"status": "conversation_generated"}

@api_router.post("/image/generate")
async def generate_image(request: ImageGenerationRequest):
    """Generate image using FLUX model"""
    try:
        image_url = await call_together_ai(request.prompt, "black-forest-labs/FLUX.1-schnell-Free")
        
        if image_url:
            # Create image message
            chat_message = ChatMessage(
                conversation_id=request.conversation_id,
                agent_type=AgentType.VISUALIZER,
                content=f"Generated image: {request.prompt}",
                image_url=image_url,
                is_user=False
            )
            
            # Save to database
            message_dict = chat_message.dict()
            message_dict["timestamp"] = message_dict["timestamp"].isoformat()
            await db.messages.insert_one(message_dict)
            
            # Remove MongoDB _id for JSON serialization
            if "_id" in message_dict:
                del message_dict["_id"]
            
            # Broadcast to WebSocket
            message_data = message_dict.copy()
            message_data["agent_config"] = AGENT_MODELS[AgentType.VISUALIZER.value]
            
            await manager.broadcast(json.dumps({
                "type": "agent_message",
                "data": message_data
            }))
            
            return {"status": "image_generated", "url": image_url}
        else:
            return {"status": "error", "message": "Failed to generate image"}
            
    except Exception as e:
        logger.error(f"Image generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/stats")
async def get_api_stats():
    """Get API key usage statistics"""
    stats = []
    for key_info in API_KEYS_POOL:
        stats.append({
            "keyId": key_info["keyId"],
            "requestCount": key_info["requestCount"],
            "rateLimit": key_info["rateLimitPerMinute"],
            "utilizationPercent": (key_info["requestCount"] / key_info["rateLimitPerMinute"]) * 100
        })
    return {"api_keys": stats}

# WebSocket endpoint
@app.websocket("/ws/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    await manager.connect(websocket)
    try:
        # Send initial connection confirmation
        await manager.send_personal_message(json.dumps({
            "type": "connection_established",
            "data": {"conversation_id": conversation_id, "message": "Connected successfully"}
        }), websocket)
        
        # Keep connection alive
        while True:
            try:
                # Wait for WebSocket messages or keep connection alive
                await asyncio.sleep(1)
            except WebSocketDisconnect:
                break
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"WebSocket disconnected for conversation: {conversation_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()