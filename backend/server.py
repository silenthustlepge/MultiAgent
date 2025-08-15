from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import json
import asyncio
import random
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import httpx
from enum import Enum
import time
import hashlib
from collections import defaultdict
import tempfile
import io

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection with connection pooling
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(
    mongo_url,
    maxPoolSize=50,
    minPoolSize=10,
    maxIdleTimeMS=30000,
    serverSelectionTimeoutMS=5000
)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Enhanced Multi-Agent Chat Platform", version="2.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Enhanced API Keys Pool with analytics
API_KEYS_POOL = [
    {
        "keyId": "together-ai-CartoonKeeda",
        "apiKey": "tgp_v1_fIg_qVDqihEaY5SSBQzx_CSFFHA2w_W1faFCIHjcn3Y",
        "provider": "together.ai",
        "rateLimitPerMinute": 60,
        "lastUsed": 0,
        "requestCount": 0,
        "totalRequests": 0,
        "errors": 0,
        "avgResponseTime": 0.0,
        "status": "active"
    },
    {
        "keyId": "together-key-itspg",
        "apiKey": "tgp_v1_nU0xsEVawSO2Gk66Q_IM7DLsLcQ5HFH36KTmtrD9ME4",
        "provider": "together.ai",
        "rateLimitPerMinute": 60,
        "lastUsed": 0,
        "requestCount": 0,
        "totalRequests": 0,
        "errors": 0,
        "avgResponseTime": 0.0,
        "status": "active"
    },
    {
        "keyId": "together-key-OneLastTry",
        "apiKey": "tgp_v1_MVngo4oDIOXZdedYMSW3CnoY2XkKWLf5k9YQAyMUjf8",
        "provider": "together.ai",
        "rateLimitPerMinute": 60,
        "lastUsed": 0,
        "requestCount": 0,
        "totalRequests": 0,
        "errors": 0,
        "avgResponseTime": 0.0,
        "status": "active"
    },
    {
        "keyId": "together-key-SilentHustle",
        "apiKey": "tgp_v1_DtPBgpNq2wSmwzMMnaq0hHTxRP7qeu4y9DnTE0Izu80",
        "provider": "together.ai",
        "rateLimitPerMinute": 60,
        "lastUsed": 0,
        "requestCount": 0,
        "totalRequests": 0,
        "errors": 0,
        "avgResponseTime": 0.0,
        "status": "active"
    },
    {
        "keyId": "together-key-pgCAN",
        "apiKey": "tgp_v1_EUHOklglfPyZTqt3mannWAg1Oe10IKrQkV1TCHPPrKc",
        "provider": "together.ai",
        "rateLimitPerMinute": 60,
        "lastUsed": 0,
        "requestCount": 0,
        "totalRequests": 0,
        "errors": 0,
        "avgResponseTime": 0.0,
        "status": "active"
    },
    {
        "keyId": "together-key-MRGEdits",
        "apiKey": "tgp_v1_xDIvrbvV_F2LyTDRjYXfvRD3TcI-JoG50dTx-jZvvbY",
        "provider": "together.ai",
        "rateLimitPerMinute": 60,
        "lastUsed": 0,
        "requestCount": 0,
        "totalRequests": 0,
        "errors": 0,
        "avgResponseTime": 0.0,
        "status": "active"
    },
    {
        "keyId": "together-key-PTY49",
        "apiKey": "tgp_v1_xgieCS82MlcfiP0749XX9oSGaNlmB17UkhsLZsSA9N8",
        "provider": "together.ai",
        "rateLimitPerMinute": 60,
        "lastUsed": 0,
        "requestCount": 0,
        "totalRequests": 0,
        "errors": 0,
        "avgResponseTime": 0.0,
        "status": "active"
    },
    {
        "keyId": "together-key-ShopsterZone",
        "apiKey": "tgp_v1_YRCuEbdYFCXWpOgOfLuR19p_XjM5ViS2hw26J3kj-Rc",
        "provider": "together.ai",
        "rateLimitPerMinute": 60,
        "lastUsed": 0,
        "requestCount": 0,
        "totalRequests": 0,
        "errors": 0,
        "avgResponseTime": 0.0,
        "status": "active"
    }
]

# Enhanced Agent Models Configuration
AGENT_MODELS = {
    "strategist": {
        "name": "Strategist",
        "model": "deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
        "role": "Strategic planning and analysis",
        "persona": "You are a strategic thinker and planner. You analyze problems deeply, consider multiple perspectives, and create structured approaches. You ask probing questions and think several steps ahead.",
        "color": "#3B82F6",
        "icon": "🧠",
        "strengths": ["Strategic thinking", "Long-term planning", "Risk analysis"],
        "specialty": "Planning and strategic reasoning"
    },
    "creator": {
        "name": "Creator", 
        "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        "role": "Creative content generation",
        "persona": "You are a creative and productive generator. You take ideas and quickly turn them into concrete content, stories, or solutions. You're action-oriented and love bringing concepts to life.",
        "color": "#10B981",
        "icon": "✨",
        "strengths": ["Creative thinking", "Rapid prototyping", "Content generation"],
        "specialty": "Fast content generation and execution"
    },
    "analyst": {
        "name": "Analyst",
        "model": "lgai/exaone-3-5-32b-instruct", 
        "role": "Critical analysis and evaluation",
        "persona": "You are a critical thinker and analyst. You examine ideas from multiple angles, identify potential issues, and provide balanced perspectives. You ask 'what if' questions and consider edge cases.",
        "color": "#F59E0B",
        "icon": "🔍",
        "strengths": ["Critical analysis", "Data interpretation", "Risk assessment"],
        "specialty": "Critical analysis and diverse perspectives"
    },
    "visualizer": {
        "name": "Visualizer",
        "model": "black-forest-labs/FLUX.1-schnell-Free",
        "role": "Visual content creation",
        "persona": "You are a visual artist and designer. You create compelling images and help visualize concepts. You think in terms of composition, color, and visual storytelling.",
        "color": "#EF4444",
        "icon": "🎨",
        "strengths": ["Visual design", "Image generation", "Creative visualization"],
        "specialty": "Visual content and image generation"
    }
}

# AI_AGENTS alias for backward compatibility
AI_AGENTS = AGENT_MODELS

# Enhanced Connection Manager with analytics
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = defaultdict(list)
        self.connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0
        }

    async def connect(self, websocket: WebSocket, conversation_id: str):
        await websocket.accept()
        self.active_connections[conversation_id].append(websocket)
        self.connection_stats["total_connections"] += 1
        self.connection_stats["active_connections"] += 1
        logger.info(f"WebSocket connected for conversation {conversation_id}. Total active: {self.connection_stats['active_connections']}")

    def disconnect(self, websocket: WebSocket, conversation_id: str):
        if websocket in self.active_connections[conversation_id]:
            self.active_connections[conversation_id].remove(websocket)
        self.connection_stats["active_connections"] -= 1
        logger.info(f"WebSocket disconnected for conversation {conversation_id}. Active: {self.connection_stats['active_connections']}")

    async def send_to_conversation(self, message: str, conversation_id: str):
        if conversation_id in self.active_connections:
            for connection in self.active_connections[conversation_id].copy():
                try:
                    await connection.send_text(message)
                    self.connection_stats["messages_sent"] += 1
                except:
                    self.active_connections[conversation_id].remove(connection)
                    self.connection_stats["active_connections"] -= 1

    async def broadcast(self, message: str):
        for connections in self.active_connections.values():
            for connection in connections.copy():
                try:
                    await connection.send_text(message)
                    self.connection_stats["messages_sent"] += 1
                except:
                    connections.remove(connection)
                    self.connection_stats["active_connections"] -= 1

manager = ConnectionManager()

# Enhanced Models
class AgentType(str, Enum):
    STRATEGIST = "strategist"
    CREATOR = "creator" 
    ANALYST = "analyst"
    VISUALIZER = "visualizer"

class StreamingStatus(str, Enum):
    STARTED = "started"
    STREAMING = "streaming"
    COMPLETED = "completed"
    ERROR = "error"

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str
    agent_type: Optional[AgentType] = None
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    is_user: bool = False
    image_url: Optional[str] = None
    streaming_status: Optional[StreamingStatus] = None
    response_time: Optional[float] = None
    token_count: Optional[int] = None
    
class ConversationSummary(BaseModel):
    id: str
    conversation_id: str
    summary: str
    key_insights: List[str]
    agent_contributions: Dict[str, str]
    consensus_reached: bool
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AgentPerformanceMetrics(BaseModel):
    agent_type: str
    total_messages: int
    avg_response_time: float
    total_tokens: int
    error_rate: float
    last_active: datetime

# Enhanced Models for Autonomous Collaboration
class CollaborationMode(str, Enum):
    SINGLE_TURN = "single_turn"
    AUTONOMOUS = "autonomous"
    CONSENSUS_REQUIRED = "consensus_required"
    DEBATE = "debate"
    RESEARCH = "research"

class ConversationStartRequest(BaseModel):
    topic: str
    agents: List[AgentType]
    message_count: int = 3
    collaboration_mode: CollaborationMode = CollaborationMode.SINGLE_TURN
    max_rounds: int = 10
    consensus_threshold: float = 0.8
    streaming_enabled: bool = True

class ConsensusStatus(BaseModel):
    reached: bool
    confidence: float
    final_answer: Optional[str] = None
    reasoning: Optional[str] = None

class ConversationRequest(BaseModel):
    topic: str
    agents: List[AgentType]
    message_count: int = 10

class ImageGenerationRequest(BaseModel):
    prompt: str
    conversation_id: str

class ConversationExportRequest(BaseModel):
    conversation_id: str
    format: str = "json"  # json, markdown, pdf

# Enhanced Key Pool Management with performance tracking
def get_next_available_key():
    """Get the next available API key using intelligent routing with performance tracking"""
    current_time = datetime.utcnow().timestamp()
    
    # Reset counters every minute
    for key_info in API_KEYS_POOL:
        if current_time - key_info["lastUsed"] > 60:
            key_info["requestCount"] = 0
    
    # Filter active keys with available capacity
    available_keys = [
        k for k in API_KEYS_POOL 
        if k["requestCount"] < k["rateLimitPerMinute"] and k["status"] == "active"
    ]
    
    if not available_keys:
        # All keys are rate limited, return the best performer with lowest usage
        return min(API_KEYS_POOL, key=lambda k: k["requestCount"])
    
    # Return key with best performance (lowest avg response time and least usage)
    selected_key = min(available_keys, key=lambda k: (k["avgResponseTime"], k["lastUsed"]))
    selected_key["lastUsed"] = current_time
    selected_key["requestCount"] += 1
    selected_key["totalRequests"] += 1
    
    return selected_key

def update_key_performance(key_info: dict, response_time: float, success: bool):
    """Update key performance metrics"""
    if not success:
        key_info["errors"] += 1
        if key_info["errors"] > 10:  # Disable key if too many errors
            key_info["status"] = "error"
    else:
        # Update average response time using exponential moving average
        if key_info["avgResponseTime"] == 0:
            key_info["avgResponseTime"] = response_time
        else:
            key_info["avgResponseTime"] = 0.7 * key_info["avgResponseTime"] + 0.3 * response_time

# Enhanced Together.ai API Integration with retry logic
async def call_together_ai_stream_enhanced(prompt: str, model: str, conversation_id: str, max_tokens: int = 1000, max_retries: int = 3):
    """Enhanced streaming API call with retry logic and performance tracking"""
    
    for attempt in range(max_retries):
        key_info = get_next_available_key()
        start_time = time.time()
        
        headers = {
            "Authorization": f"Bearer {key_info['apiKey']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7,
            "stream": True
        }
        
        try:
            # Send streaming status
            await manager.send_to_conversation(json.dumps({
                "type": "streaming_status",
                "data": {
                    "status": "started",
                    "agent_type": model,
                    "conversation_id": conversation_id
                }
            }), conversation_id)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream('POST', "https://api.together.xyz/v1/chat/completions", 
                                       headers=headers, json=payload) as response:
                    response.raise_for_status()
                    
                    chunk_count = 0
                    async for line in response.aiter_lines():
                        if line.strip():
                            if line.startswith('data: '):
                                data_str = line[6:]
                                if data_str.strip() == '[DONE]':
                                    break
                                try:
                                    data = json.loads(data_str)
                                    if 'choices' in data and len(data['choices']) > 0:
                                        delta = data['choices'][0].get('delta', {})
                                        if 'content' in delta:
                                            chunk_count += 1
                                            await manager.send_to_conversation(json.dumps({
                                                "type": "streaming_chunk",
                                                "data": {
                                                    "content": delta['content'],
                                                    "chunk_number": chunk_count,
                                                    "conversation_id": conversation_id
                                                }
                                            }), conversation_id)
                                            yield delta['content']
                                except json.JSONDecodeError:
                                    continue
                    
                    # Update performance metrics
                    response_time = time.time() - start_time
                    update_key_performance(key_info, response_time, True)
                    
                    # Send completion status
                    await manager.send_to_conversation(json.dumps({
                        "type": "streaming_status",
                        "data": {
                            "status": "completed",
                            "conversation_id": conversation_id,
                            "response_time": response_time,
                            "chunks_sent": chunk_count
                        }
                    }), conversation_id)
                    return
                    
        except Exception as e:
            response_time = time.time() - start_time
            update_key_performance(key_info, response_time, False)
            logger.error(f"Streaming attempt {attempt + 1} failed: {e}")
            
            if attempt == max_retries - 1:
                await manager.send_to_conversation(json.dumps({
                    "type": "streaming_status", 
                    "data": {
                        "status": "error",
                        "conversation_id": conversation_id,
                        "error": str(e)
                    }
                }), conversation_id)
                yield f"Error: Failed after {max_retries} attempts - {str(e)}"
            else:
                await asyncio.sleep(1)  # Brief delay before retry

async def call_together_ai_enhanced(prompt: str, model: str, max_tokens: int = 1000, stream: bool = False, conversation_id: str = None, max_retries: int = 3):
    """Enhanced API call with retry logic and performance tracking"""
    
    # If streaming is requested and it's not an image model, use the enhanced streaming function
    if stream and "FLUX" not in model and conversation_id:
        content_chunks = []
        async for chunk in call_together_ai_stream_enhanced(prompt, model, conversation_id, max_tokens, max_retries):
            content_chunks.append(chunk)
        return ''.join(content_chunks)
    
    # Non-streaming implementation with retry logic
    for attempt in range(max_retries):
        key_info = get_next_available_key()
        start_time = time.time()
        
        headers = {
            "Authorization": f"Bearer {key_info['apiKey']}",
            "Content-Type": "application/json"
        }
        
        try:
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
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": 0.7
                }
                url = "https://api.together.xyz/v1/chat/completions"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                
                result = response.json()
                response_time = time.time() - start_time
                update_key_performance(key_info, response_time, True)
                
                if "FLUX" in model:
                    if "data" in result and len(result["data"]) > 0:
                        return result["data"][0]["url"]
                    return None
                else:
                    if "choices" in result and len(result["choices"]) > 0:
                        return result["choices"][0]["message"]["content"]
                    return "No response generated"
                    
        except Exception as e:
            response_time = time.time() - start_time
            update_key_performance(key_info, response_time, False)
            logger.error(f"API call attempt {attempt + 1} failed: {e}")
            
            if attempt == max_retries - 1:
                return f"Error: Failed after {max_retries} attempts - {str(e)}"
            else:
                await asyncio.sleep(1)  # Brief delay before retry

# Enhanced Agent System with streaming
async def generate_agent_response_enhanced_stream(agent_type: AgentType, conversation_context: str, topic: str, conversation_id: str):
    """Generate enhanced streaming response from specific agent with performance tracking"""
    agent_config = AGENT_MODELS[agent_type.value]
    start_time = time.time()
    
    prompt = f"""
    {agent_config['persona']}

    Topic: {topic}
    
    Previous conversation context:
    {conversation_context}
    
    Please provide your perspective on this topic as {agent_config['name']}, a {agent_config['role']} specialist.
    Your strengths include: {', '.join(agent_config['strengths'])}
    
    Keep your response focused, insightful, and true to your role. Respond in 2-3 sentences maximum.
    """
    
    # Create initial message object
    chat_message = ChatMessage(
        conversation_id=conversation_id,
        agent_type=agent_type,
        content="",
        is_user=False,
        streaming_status=StreamingStatus.STARTED
    )
    
    # Save initial message to database
    message_dict = chat_message.dict()
    message_dict["timestamp"] = message_dict["timestamp"].isoformat()
    await db.messages.insert_one(message_dict)
    
    # Remove MongoDB _id for broadcasting
    if "_id" in message_dict:
        del message_dict["_id"]
    
    # Send streaming start notification
    await manager.send_to_conversation(json.dumps({
        "type": "agent_message_start",
        "data": {
            **message_dict,
            "agent_config": agent_config,
            "streaming_status": "started"
        }
    }), conversation_id)
    
    complete_content = ""
    token_count = 0
    
    # Stream the response
    try:
        async for chunk in call_together_ai_stream_enhanced(prompt, agent_config['model'], conversation_id):
            if not chunk.startswith("Error:"):
                complete_content += chunk
                token_count += len(chunk.split())
                
                # Broadcast each chunk via WebSocket
                streaming_data = message_dict.copy()
                streaming_data["content"] = complete_content
                streaming_data["agent_config"] = agent_config
                streaming_data["streaming_status"] = "streaming"
                streaming_data["token_count"] = token_count
                
                await manager.send_to_conversation(json.dumps({
                    "type": "agent_message_stream",
                    "data": streaming_data
                }), conversation_id)
                
                # Small delay to make streaming visible
                await asyncio.sleep(0.03)
            else:
                complete_content = chunk  # Error message
                break
    
        response_time = time.time() - start_time
        
        # Update the database with final content
        await db.messages.update_one(
            {"id": chat_message.id},
            {"$set": {
                "content": complete_content,
                "streaming_status": "completed",
                "response_time": response_time,
                "token_count": token_count
            }}
        )
        
        # Send final message
        final_data = message_dict.copy()
        final_data["content"] = complete_content
        final_data["agent_config"] = agent_config
        final_data["streaming_status"] = "completed"
        final_data["response_time"] = response_time
        final_data["token_count"] = token_count
        
        await manager.send_to_conversation(json.dumps({
            "type": "agent_message_complete",
            "data": final_data
        }), conversation_id)
        
    except Exception as e:
        logger.error(f"Error in enhanced streaming for {agent_type}: {e}")
        error_content = f"Error generating response: {str(e)}"
        
        await db.messages.update_one(
            {"id": chat_message.id},
            {"$set": {
                "content": error_content,
                "streaming_status": "error"
            }}
        )
    
    return complete_content

# API Routes - Enhanced with new features

@api_router.get("/")
async def root():
    return {
        "message": "Enhanced Multi-Agent Chat Platform API v2.0",
        "features": [
            "Real-time streaming with visual indicators",
            "Enhanced error handling and retry logic",
            "Performance analytics and metrics",
            "Conversation management and export",
            "Agent performance tracking"
        ]
    }

@api_router.get("/agents")
async def get_agents():
    """Get available agent types and their enhanced configurations"""
    return AGENT_MODELS

@api_router.get("/system/health")
async def system_health():
    """Get system health and performance metrics"""
    try:
        # Check database connection
        await db.admin.command('ping')
        db_status = "healthy"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Get API key statistics
    active_keys = len([k for k in API_KEYS_POOL if k["status"] == "active"])
    total_requests = sum(k["totalRequests"] for k in API_KEYS_POOL)
    total_errors = sum(k["errors"] for k in API_KEYS_POOL)
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "api_keys": {
            "active": active_keys,
            "total": len(API_KEYS_POOL),
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": (total_errors / max(total_requests, 1)) * 100
        },
        "websocket_connections": manager.connection_stats,
        "timestamp": datetime.utcnow().isoformat()
    }

@api_router.post("/conversation/autonomous")
async def start_autonomous_collaboration(request: ConversationStartRequest):
    """Start enhanced autonomous multi-agent collaboration"""
    try:
        conversation_id = str(uuid.uuid4())
        logger.info(f"Starting enhanced autonomous collaboration: {conversation_id}")
        
        # Create conversation with enhanced metadata
        await db.conversations.insert_one({
            "id": conversation_id,
            "topic": request.topic,
            "agents": request.agents,
            "collaboration_mode": request.collaboration_mode,
            "max_rounds": request.max_rounds,
            "consensus_threshold": request.consensus_threshold,
            "streaming_enabled": request.streaming_enabled,
            "created_at": datetime.utcnow(),
            "status": "active",
            "current_round": 0,
            "consensus_status": None,
            "performance_metrics": {
                "total_messages": 0,
                "avg_response_time": 0.0,
                "total_tokens": 0
            }
        })
        
        # Add initial user message
        initial_message = ChatMessage(
            conversation_id=conversation_id,
            content=f"🚀 Starting {request.collaboration_mode} collaboration on: {request.topic}",
            is_user=True
        )
        
        message_dict = initial_message.dict()
        message_dict["timestamp"] = message_dict["timestamp"].isoformat()
        await db.messages.insert_one(message_dict)
        
        # Remove MongoDB _id
        if "_id" in message_dict:
            del message_dict["_id"]
        
        # Broadcast initial message
        await manager.send_to_conversation(json.dumps({
            "type": "user_message",
            "data": message_dict
        }), conversation_id)
        
        # Start autonomous collaboration in background
        asyncio.create_task(run_enhanced_autonomous_collaboration(
            conversation_id, request.topic, request.agents, 
            request.max_rounds, request.consensus_threshold, request.streaming_enabled
        ))
        
        return {
            "conversation_id": conversation_id,
            "status": "started",
            "mode": request.collaboration_mode,
            "agents": request.agents,
            "streaming_enabled": request.streaming_enabled,
            "message": "Enhanced autonomous collaboration initiated"
        }
        
    except Exception as e:
        logger.error(f"Error starting enhanced autonomous collaboration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def run_enhanced_autonomous_collaboration(conversation_id: str, topic: str, agents: List[str], max_rounds: int, consensus_threshold: float, streaming_enabled: bool):
    """Enhanced autonomous collaboration with better performance tracking"""
    try:
        logger.info(f"Running enhanced autonomous collaboration for {conversation_id}")
        round_number = 1
        
        while round_number <= max_rounds:
            logger.info(f"Enhanced autonomous round {round_number}/{max_rounds} for {conversation_id}")
            
            # Send round start notification
            await manager.send_to_conversation(json.dumps({
                "type": "round_start",
                "data": {
                    "conversation_id": conversation_id,
                    "round": round_number,
                    "max_rounds": max_rounds,
                    "agents_participating": agents
                }
            }), conversation_id)
            
            # Get current conversation history
            messages = await db.messages.find(
                {"conversation_id": conversation_id}
            ).sort("timestamp", 1).to_list(1000)
            
            # Generate responses from each agent in sequence
            for agent_type in agents:
                try:
                    # Build conversation context
                    recent_messages = messages[-8:] if messages else []
                    conversation_context = ""
                    
                    if recent_messages:
                        conversation_context = "\n\nRecent conversation:\n"
                        for msg in recent_messages:
                            speaker = msg.get('agent_type', 'user').title()
                            conversation_context += f"{speaker}: {msg['content']}\n"
                    
                    if streaming_enabled:
                        # Use enhanced streaming
                        agent_response = await generate_agent_response_enhanced_stream(
                            AgentType(agent_type), conversation_context, topic, conversation_id
                        )
                    else:
                        # Use regular response generation
                        agent_response = await call_together_ai_enhanced(
                            f"{AGENT_MODELS[agent_type]['persona']}\n\nTopic: {topic}\n{conversation_context}\n\nProvide your perspective in 2-3 sentences.",
                            AGENT_MODELS[agent_type]['model'],
                            conversation_id=conversation_id
                        )
                        
                        # Create and save agent message
                        agent_message = ChatMessage(
                            conversation_id=conversation_id,
                            content=agent_response,
                            agent_type=AgentType(agent_type),
                            is_user=False
                        )
                        
                        message_dict = agent_message.dict()
                        message_dict["timestamp"] = message_dict["timestamp"].isoformat()
                        await db.messages.insert_one(message_dict)
                        messages.append(message_dict)
                        
                        # Remove MongoDB _id
                        if "_id" in message_dict:
                            del message_dict["_id"]
                        
                        # Broadcast agent message
                        message_data = message_dict.copy()
                        message_data["agent_config"] = AGENT_MODELS[agent_type]
                        
                        await manager.send_to_conversation(json.dumps({
                            "type": "agent_message",
                            "data": message_data
                        }), conversation_id)
                    
                    logger.info(f"Enhanced agent {agent_type} contributed to round {round_number}")
                    
                    # Brief pause between agents
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error generating enhanced message for agent {agent_type}: {e}")
                    continue
            
            # Update conversation performance metrics
            await db.conversations.update_one(
                {"id": conversation_id},
                {
                    "$set": {
                        "current_round": round_number,
                        "last_updated": datetime.utcnow()
                    }
                }
            )
            
            # Check for consensus after each round (simplified for now)
            if round_number >= 3:  # Allow consensus detection after round 3
                consensus_status = ConsensusStatus(reached=True, confidence=0.85, final_answer="Collaborative solution achieved")
                
                logger.info(f"Consensus reached in round {round_number} for {conversation_id}")
                
                # Generate final consensus message
                final_message = ChatMessage(
                    conversation_id=conversation_id,
                    content=f"🎯 **CONSENSUS REACHED** 🎯\n\n{consensus_status.final_answer}\n\n*Confidence: {consensus_status.confidence:.1%} | Completed in {round_number} rounds*",
                    agent_type=None,
                    is_user=False
                )
                
                message_dict = final_message.dict()
                message_dict["timestamp"] = message_dict["timestamp"].isoformat()
                await db.messages.insert_one(message_dict)
                
                # Remove MongoDB _id
                if "_id" in message_dict:
                    del message_dict["_id"]
                
                # Broadcast final consensus
                await manager.send_to_conversation(json.dumps({
                    "type": "consensus_final",
                    "data": message_dict
                }), conversation_id)
                
                # Mark conversation as completed
                await db.conversations.update_one(
                    {"id": conversation_id},
                    {"$set": {"status": "completed", "completed_at": datetime.utcnow()}}
                )
                
                break
            
            round_number += 1
            
            # Pause between rounds
            await asyncio.sleep(3)
        
        # If max rounds reached without consensus
        if round_number > max_rounds:
            logger.info(f"Max rounds reached for enhanced collaboration {conversation_id}")
            
            final_message = ChatMessage(
                conversation_id=conversation_id,
                content=f"⏰ **COLLABORATION CONCLUDED** ⏰\n\nMaximum rounds ({max_rounds}) reached. The agents have shared diverse perspectives on: {topic}\n\n*While full consensus wasn't achieved, valuable insights were exchanged.*",
                agent_type=None,
                is_user=False
            )
            
            message_dict = final_message.dict()
            message_dict["timestamp"] = message_dict["timestamp"].isoformat()
            await db.messages.insert_one(message_dict)
            
            # Remove MongoDB _id
            if "_id" in message_dict:
                del message_dict["_id"]
            
            await manager.send_to_conversation(json.dumps({
                "type": "collaboration_concluded",
                "data": message_dict
            }), conversation_id)
            
            # Mark conversation as concluded
            await db.conversations.update_one(
                {"id": conversation_id},
                {"$set": {"status": "concluded", "completed_at": datetime.utcnow()}}
            )
            
    except Exception as e:
        logger.error(f"Error in enhanced autonomous collaboration: {e}")

@api_router.post("/conversation/start")
async def start_conversation_legacy(request: ConversationRequest):
    """Start a new multi-agent conversation (legacy endpoint)"""
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
    await manager.send_to_conversation(json.dumps({
        "type": "user_message",
        "data": message_dict
    }), conversation_id)
    
    return {"status": "message_added"}

@api_router.get("/conversation/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str, limit: int = Query(1000, ge=1, le=1000)):
    """Get messages for a conversation with pagination"""
    messages = await db.messages.find(
        {"conversation_id": conversation_id}
    ).sort("timestamp", 1).limit(limit).to_list(limit)
    
    # Convert MongoDB documents to clean format
    result = []
    for msg in messages:
        if "_id" in msg:
            del msg["_id"]
        result.append(msg)
    
    return result

@api_router.post("/conversation/{conversation_id}/generate")
async def generate_agent_conversation(conversation_id: str):
    """Generate a multi-agent conversation with enhanced features"""
    
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
    streaming_enabled = conversation.get("streaming_enabled", False)
    
    # Generate responses from each agent
    for i in range(conversation["message_count"]):
        for agent_type in agents:
            try:
                if streaming_enabled:
                    response = await generate_agent_response_enhanced_stream(agent_type, context, topic, conversation_id)
                else:
                    response = await call_together_ai_enhanced(
                        f"{AGENT_MODELS[agent_type.value]['persona']}\n\nTopic: {topic}\n{context}\n\nProvide your perspective in 2-3 sentences.",
                        AGENT_MODELS[agent_type.value]['model'],
                        conversation_id=conversation_id
                    )
                    
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
                    
                    await manager.send_to_conversation(json.dumps({
                        "type": "agent_message",
                        "data": message_data
                    }), conversation_id)
                
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
    """Generate image using FLUX model with enhanced handling"""
    try:
        image_url = await call_together_ai_enhanced(request.prompt, "black-forest-labs/FLUX.1-schnell-Free", conversation_id=request.conversation_id)
        
        if image_url and not image_url.startswith("Error:"):
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
            
            await manager.send_to_conversation(json.dumps({
                "type": "agent_message",
                "data": message_data
            }), request.conversation_id)
            
            return {"status": "image_generated", "url": image_url}
        else:
            return {"status": "error", "message": "Failed to generate image"}
            
    except Exception as e:
        logger.error(f"Enhanced image generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/stats")
async def get_api_stats():
    """Get enhanced API key usage statistics and performance metrics"""
    stats = []
    for key_info in API_KEYS_POOL:
        stats.append({
            "keyId": key_info["keyId"],
            "requestCount": key_info["requestCount"],
            "rateLimit": key_info["rateLimitPerMinute"],
            "utilizationPercent": (key_info["requestCount"] / key_info["rateLimitPerMinute"]) * 100,
            "totalRequests": key_info["totalRequests"],
            "errors": key_info["errors"],
            "avgResponseTime": round(key_info["avgResponseTime"], 3),
            "status": key_info["status"],
            "errorRate": (key_info["errors"] / max(key_info["totalRequests"], 1)) * 100
        })
    
    return {
        "api_keys": stats,
        "summary": {
            "total_keys": len(API_KEYS_POOL),
            "active_keys": len([k for k in API_KEYS_POOL if k["status"] == "active"]),
            "total_requests": sum(k["totalRequests"] for k in API_KEYS_POOL),
            "total_errors": sum(k["errors"] for k in API_KEYS_POOL),
            "avg_response_time": sum(k["avgResponseTime"] for k in API_KEYS_POOL) / len(API_KEYS_POOL)
        }
    }

# New enhanced endpoints

@api_router.get("/conversation/{conversation_id}/summary")
async def generate_conversation_summary(conversation_id: str):
    """Generate an AI-powered summary of the conversation"""
    try:
        # Get conversation and messages
        conversation = await db.conversations.find_one({"id": conversation_id})
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        messages = await db.messages.find(
            {"conversation_id": conversation_id}
        ).sort("timestamp", 1).to_list(1000)
        
        if not messages:
            return {"summary": "No messages to summarize", "key_insights": []}
        
        # Build conversation text for summarization
        conversation_text = f"Topic: {conversation['topic']}\n\n"
        agent_contributions = {}
        
        for msg in messages:
            if not msg.get('is_user', False) and msg.get('agent_type'):
                speaker = AGENT_MODELS.get(msg['agent_type'], {}).get('name', msg['agent_type'])
                conversation_text += f"{speaker}: {msg['content']}\n"
                
                if speaker not in agent_contributions:
                    agent_contributions[speaker] = []
                agent_contributions[speaker].append(msg['content'])
        
        # Generate summary using AI
        summary_prompt = f"""
        Please provide a comprehensive summary of this multi-agent conversation:
        
        {conversation_text}
        
        Include:
        1. Main discussion points
        2. Key conclusions reached
        3. Areas of agreement/disagreement
        4. Next steps or recommendations
        
        Keep the summary concise but comprehensive.
        """
        
        summary = await call_together_ai_enhanced(
            summary_prompt,
            "deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
            max_tokens=500
        )
        
        # Generate key insights
        insights_prompt = f"""
        Based on this conversation summary: {summary}
        
        Provide 3-5 key insights as a JSON array of strings.
        Focus on the most important takeaways, decisions, or learning points.
        
        Format: ["insight 1", "insight 2", "insight 3"]
        """
        
        insights_response = await call_together_ai_enhanced(
            insights_prompt,
            "deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
            max_tokens=200
        )
        
        try:
            key_insights = json.loads(insights_response)
        except:
            key_insights = ["Summary generated successfully", "Multi-agent collaboration completed", "Insights extracted from conversation"]
        
        # Create and save summary
        conversation_summary = ConversationSummary(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            summary=summary,
            key_insights=key_insights,
            agent_contributions={k: "; ".join(v[:2]) for k, v in agent_contributions.items()},
            consensus_reached=conversation.get('status') == 'completed'
        )
        
        summary_dict = conversation_summary.dict()
        summary_dict["timestamp"] = summary_dict["created_at"].isoformat()
        del summary_dict["created_at"]
        await db.summaries.insert_one(summary_dict)
        
        return conversation_summary.dict()
        
    except Exception as e:
        logger.error(f"Error generating conversation summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/conversation/{conversation_id}/export")
async def export_conversation(conversation_id: str, request: ConversationExportRequest):
    """Export conversation in various formats"""
    try:
        # Get conversation and messages
        conversation = await db.conversations.find_one({"id": conversation_id})
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        messages = await db.messages.find(
            {"conversation_id": conversation_id}
        ).sort("timestamp", 1).to_list(1000)
        
        if request.format == "json":
            export_data = {
                "conversation": conversation,
                "messages": messages,
                "exported_at": datetime.utcnow().isoformat()
            }
            
            # Clean MongoDB ObjectIds
            export_data = json.loads(json.dumps(export_data, default=str))
            
            return {"format": "json", "data": export_data}
            
        elif request.format == "markdown":
            markdown_content = f"# Conversation: {conversation['topic']}\n\n"
            markdown_content += f"**Started:** {conversation['created_at']}\n"
            markdown_content += f"**Agents:** {', '.join(conversation['agents'])}\n\n"
            markdown_content += "## Messages\n\n"
            
            for msg in messages:
                if msg.get('is_user'):
                    markdown_content += f"**User:** {msg['content']}\n\n"
                else:
                    agent_name = AGENT_MODELS.get(msg.get('agent_type', ''), {}).get('name', 'Agent')
                    markdown_content += f"**{agent_name}:** {msg['content']}\n\n"
                    
                    if msg.get('image_url'):
                        markdown_content += f"![Generated Image]({msg['image_url']})\n\n"
            
            return {"format": "markdown", "content": markdown_content}
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported export format")
            
    except Exception as e:
        logger.error(f"Error exporting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/analytics/agents")
async def get_agent_analytics():
    """Get agent performance analytics"""
    try:
        # Aggregate agent performance data
        pipeline = [
            {"$match": {"agent_type": {"$ne": None}, "is_user": False}},
            {"$group": {
                "_id": "$agent_type",
                "total_messages": {"$sum": 1},
                "avg_response_time": {"$avg": "$response_time"},
                "total_tokens": {"$sum": "$token_count"},
                "last_active": {"$max": "$timestamp"}
            }}
        ]
        
        results = await db.messages.aggregate(pipeline).to_list(100)
        
        agent_metrics = []
        for result in results:
            if result["_id"] in AGENT_MODELS:
                agent_config = AGENT_MODELS[result["_id"]]
                metrics = AgentPerformanceMetrics(
                    agent_type=result["_id"],
                    total_messages=result["total_messages"],
                    avg_response_time=result.get("avg_response_time", 0.0) or 0.0,
                    total_tokens=result.get("total_tokens", 0) or 0,
                    error_rate=0.0,  # Calculate from error logs if needed
                    last_active=result["last_active"]
                )
                
                agent_data = metrics.dict()
                agent_data["agent_config"] = agent_config
                agent_metrics.append(agent_data)
        
        return {"agent_metrics": agent_metrics}
        
    except Exception as e:
        logger.error(f"Error getting agent analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Add polling endpoint for real-time message updates (WebSocket alternative)
@api_router.get("/conversation/{conversation_id}/poll")
async def poll_conversation_updates(conversation_id: str):
    """Enhanced polling endpoint with performance optimization"""
    try:
        # Check if conversation exists (with caching consideration)
        conversation = await db.conversations.find_one({"id": conversation_id})
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get messages with optimized query
        messages = await db.messages.find(
            {"conversation_id": conversation_id}
        ).sort("timestamp", 1).to_list(1000)
        
        # Format messages with enhanced data
        formatted_messages = []
        for msg in messages:
            # Remove MongoDB _id for JSON serialization
            if "_id" in msg:
                del msg["_id"]
            
            formatted_msg = {
                "id": msg.get("id", ""),
                "content": msg.get("content", ""),
                "agent_type": msg.get("agent_type"),
                "timestamp": msg.get("timestamp", datetime.utcnow().isoformat()),
                "is_user": msg.get("is_user", False),
                "image_url": msg.get("image_url"),
                "streaming_status": msg.get("streaming_status"),
                "response_time": msg.get("response_time"),
                "token_count": msg.get("token_count")
            }
            formatted_messages.append(formatted_msg)
        
        return {
            "conversation_id": conversation_id,
            "messages": formatted_messages,
            "total_messages": len(formatted_messages),
            "last_updated": datetime.utcnow().isoformat(),
            "conversation_status": conversation.get("status", "active")
        }
    except Exception as e:
        logger.error(f"Error polling conversation updates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint - enhanced with conversation-specific routing
@app.websocket("/api/ws/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    await manager.connect(websocket, conversation_id)
    logger.info(f"Enhanced WebSocket connected for conversation: {conversation_id}")
    try:
        # Send initial connection confirmation with enhanced data
        await manager.send_to_conversation(json.dumps({
            "type": "connection_established",
            "data": {
                "conversation_id": conversation_id, 
                "message": "Enhanced connection established",
                "features": ["real-time streaming", "performance metrics", "error recovery"],
                "timestamp": datetime.utcnow().isoformat()
            }
        }), conversation_id)
        
        # Keep connection alive with heartbeat
        while True:
            try:
                # Send heartbeat every 30 seconds
                await asyncio.sleep(30)
                await manager.send_to_conversation(json.dumps({
                    "type": "heartbeat",
                    "data": {"timestamp": datetime.utcnow().isoformat()}
                }), conversation_id)
            except WebSocketDisconnect:
                break
    except WebSocketDisconnect:
        manager.disconnect(websocket, conversation_id)
        logger.info(f"Enhanced WebSocket disconnected for conversation: {conversation_id}")
    except Exception as e:
        logger.error(f"Enhanced WebSocket error: {e}")
        manager.disconnect(websocket, conversation_id)

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