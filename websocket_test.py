#!/usr/bin/env python3
"""
WebSocket Test Suite for Multi-Agent Chat Platform
Tests the FIXED WebSocket endpoint at /api/ws/{conversation_id}
"""

import asyncio
import httpx
import json
import websockets
import time
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from environment
BACKEND_URL = "https://continuous-growth.preview.emergentagent.com/api"
WEBSOCKET_URL = "wss://agent-nexus-6.preview.emergentagent.com/api/ws"

class WebSocketTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_results = []
        self.conversation_id = None
        self.websocket_messages = []
        
    async def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}: {details}")
        
    async def setup_conversation(self):
        """Create a test conversation for WebSocket testing"""
        try:
            payload = {
                "topic": "Testing WebSocket Communication in Multi-Agent Systems",
                "agents": ["strategist", "creator", "analyst", "visualizer"],
                "message_count": 2
            }
            
            response = await self.client.post(f"{BACKEND_URL}/conversation/start", json=payload)
            if response.status_code == 200:
                data = response.json()
                self.conversation_id = data["conversation_id"]
                await self.log_test("Setup Conversation", True, f"Created conversation: {self.conversation_id}")
                return True
            else:
                await self.log_test("Setup Conversation", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            await self.log_test("Setup Conversation", False, f"Exception: {str(e)}")
            return False
    
    async def test_websocket_connection(self):
        """Test WebSocket connection to FIXED endpoint /api/ws/{conversation_id}"""
        if not self.conversation_id:
            await self.log_test("WebSocket Connection", False, "No conversation ID available")
            return False
            
        try:
            websocket_url = f"{WEBSOCKET_URL}/{self.conversation_id}"
            print(f"🔌 Connecting to WebSocket: {websocket_url}")
            
            async with websockets.connect(websocket_url) as websocket:
                # Wait for connection confirmation
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    
                    if data.get("type") == "connection_established":
                        await self.log_test("WebSocket Connection", True, 
                                          f"Successfully connected to FIXED endpoint /api/ws/{self.conversation_id}", data)
                        return True
                    else:
                        await self.log_test("WebSocket Connection", False, 
                                          f"Unexpected initial message: {data}")
                        return False
                        
                except asyncio.TimeoutError:
                    await self.log_test("WebSocket Connection", False, "No connection confirmation received within 5 seconds")
                    return False
                    
        except Exception as e:
            await self.log_test("WebSocket Connection", False, f"Connection failed: {str(e)}")
            return False
    
    async def test_websocket_user_message_broadcast(self):
        """Test WebSocket broadcasting when user message is added"""
        if not self.conversation_id:
            await self.log_test("WebSocket User Message Broadcast", False, "No conversation ID available")
            return False
            
        try:
            websocket_url = f"{WEBSOCKET_URL}/{self.conversation_id}"
            
            async with websockets.connect(websocket_url) as websocket:
                # Skip connection confirmation
                await websocket.recv()
                
                # Add user message via API
                payload = {"content": "Hello agents! Let's discuss the future of AI collaboration."}
                response = await self.client.post(
                    f"{BACKEND_URL}/conversation/{self.conversation_id}/message", 
                    json=payload
                )
                
                if response.status_code != 200:
                    await self.log_test("WebSocket User Message Broadcast", False, 
                                      f"Failed to add user message: {response.status_code}")
                    return False
                
                # Wait for WebSocket broadcast
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(message)
                    
                    # Verify message format
                    if (data.get("type") == "user_message" and 
                        "data" in data and 
                        data["data"].get("content") == payload["content"] and
                        data["data"].get("is_user") == True):
                        
                        await self.log_test("WebSocket User Message Broadcast", True, 
                                          "User message correctly broadcasted via WebSocket", data)
                        return True
                    else:
                        await self.log_test("WebSocket User Message Broadcast", False, 
                                          f"Invalid message format or content: {data}")
                        return False
                        
                except asyncio.TimeoutError:
                    await self.log_test("WebSocket User Message Broadcast", False, 
                                      "No WebSocket message received within 10 seconds")
                    return False
                    
        except Exception as e:
            await self.log_test("WebSocket User Message Broadcast", False, f"Exception: {str(e)}")
            return False
    
    async def test_websocket_agent_conversation_broadcast(self):
        """Test WebSocket broadcasting during agent conversation generation"""
        if not self.conversation_id:
            await self.log_test("WebSocket Agent Conversation Broadcast", False, "No conversation ID available")
            return False
            
        try:
            websocket_url = f"{WEBSOCKET_URL}/{self.conversation_id}"
            
            async with websockets.connect(websocket_url) as websocket:
                # Skip connection confirmation
                await websocket.recv()
                
                print("🤖 Starting agent conversation generation...")
                
                # Start agent conversation generation
                response = await self.client.post(
                    f"{BACKEND_URL}/conversation/{self.conversation_id}/generate",
                    timeout=60.0
                )
                
                if response.status_code != 200:
                    await self.log_test("WebSocket Agent Conversation Broadcast", False, 
                                      f"Failed to generate conversation: {response.status_code}")
                    return False
                
                # Collect WebSocket messages during generation
                agent_messages = []
                timeout_count = 0
                max_timeouts = 3
                
                while len(agent_messages) < 8 and timeout_count < max_timeouts:  # Expect 4 agents × 2 messages = 8
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                        data = json.loads(message)
                        
                        if data.get("type") == "agent_message":
                            agent_messages.append(data)
                            print(f"📨 Received agent message from {data['data'].get('agent_type', 'unknown')}")
                            
                    except asyncio.TimeoutError:
                        timeout_count += 1
                        print(f"⏰ Timeout {timeout_count}/{max_timeouts} waiting for agent messages")
                        continue
                
                if len(agent_messages) > 0:
                    # Verify message format
                    valid_messages = 0
                    for msg in agent_messages:
                        if (msg.get("type") == "agent_message" and 
                            "data" in msg and 
                            msg["data"].get("agent_type") in ["strategist", "creator", "analyst", "visualizer"] and
                            msg["data"].get("content") and
                            msg["data"].get("is_user") == False):
                            valid_messages += 1
                    
                    if valid_messages == len(agent_messages):
                        await self.log_test("WebSocket Agent Conversation Broadcast", True, 
                                          f"Received {len(agent_messages)} valid agent messages via WebSocket", 
                                          {"message_count": len(agent_messages), "agents": [msg["data"]["agent_type"] for msg in agent_messages]})
                        return True
                    else:
                        await self.log_test("WebSocket Agent Conversation Broadcast", False, 
                                          f"Only {valid_messages}/{len(agent_messages)} messages had valid format")
                        return False
                else:
                    await self.log_test("WebSocket Agent Conversation Broadcast", False, 
                                      "No agent messages received via WebSocket")
                    return False
                    
        except Exception as e:
            await self.log_test("WebSocket Agent Conversation Broadcast", False, f"Exception: {str(e)}")
            return False
    
    async def test_websocket_image_generation_broadcast(self):
        """Test WebSocket broadcasting during image generation"""
        if not self.conversation_id:
            await self.log_test("WebSocket Image Generation Broadcast", False, "No conversation ID available")
            return False
            
        try:
            websocket_url = f"{WEBSOCKET_URL}/{self.conversation_id}"
            
            async with websockets.connect(websocket_url) as websocket:
                # Skip connection confirmation
                await websocket.recv()
                
                print("🎨 Starting image generation...")
                
                # Generate image
                payload = {
                    "prompt": "A collaborative AI workspace with multiple agents working together",
                    "conversation_id": self.conversation_id
                }
                
                response = await self.client.post(
                    f"{BACKEND_URL}/image/generate", 
                    json=payload,
                    timeout=60.0
                )
                
                if response.status_code != 200:
                    await self.log_test("WebSocket Image Generation Broadcast", False, 
                                      f"Failed to generate image: {response.status_code}")
                    return False
                
                # Wait for WebSocket broadcast
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    data = json.loads(message)
                    
                    # Verify message format
                    if (data.get("type") == "agent_message" and 
                        "data" in data and 
                        data["data"].get("agent_type") == "visualizer" and
                        data["data"].get("image_url") and
                        data["data"].get("is_user") == False):
                        
                        await self.log_test("WebSocket Image Generation Broadcast", True, 
                                          f"Image generation message correctly broadcasted via WebSocket: {data['data']['image_url']}", 
                                          data)
                        return True
                    else:
                        await self.log_test("WebSocket Image Generation Broadcast", False, 
                                          f"Invalid image message format: {data}")
                        return False
                        
                except asyncio.TimeoutError:
                    await self.log_test("WebSocket Image Generation Broadcast", False, 
                                      "No WebSocket message received within 30 seconds")
                    return False
                    
        except Exception as e:
            await self.log_test("WebSocket Image Generation Broadcast", False, f"Exception: {str(e)}")
            return False
    
    async def test_end_to_end_websocket_flow(self):
        """Test complete end-to-end WebSocket flow"""
        if not self.conversation_id:
            await self.log_test("End-to-End WebSocket Flow", False, "No conversation ID available")
            return False
            
        try:
            websocket_url = f"{WEBSOCKET_URL}/{self.conversation_id}"
            all_messages = []
            
            async with websockets.connect(websocket_url) as websocket:
                # Skip connection confirmation
                await websocket.recv()
                
                print("🔄 Testing complete end-to-end WebSocket flow...")
                
                # Step 1: Add user message
                user_payload = {"content": "Let's create a comprehensive AI strategy for 2025"}
                await self.client.post(f"{BACKEND_URL}/conversation/{self.conversation_id}/message", json=user_payload)
                
                # Collect user message
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    user_msg = json.loads(message)
                    if user_msg.get("type") == "user_message":
                        all_messages.append(user_msg)
                        print("✅ User message received via WebSocket")
                except asyncio.TimeoutError:
                    print("❌ User message not received via WebSocket")
                
                # Step 2: Generate agent conversation
                await self.client.post(f"{BACKEND_URL}/conversation/{self.conversation_id}/generate", timeout=60.0)
                
                # Collect agent messages
                agent_count = 0
                timeout_count = 0
                while agent_count < 8 and timeout_count < 5:  # 4 agents × 2 messages
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                        agent_msg = json.loads(message)
                        if agent_msg.get("type") == "agent_message":
                            all_messages.append(agent_msg)
                            agent_count += 1
                            print(f"✅ Agent message {agent_count} received via WebSocket")
                    except asyncio.TimeoutError:
                        timeout_count += 1
                        continue
                
                # Step 3: Generate image
                image_payload = {
                    "prompt": "AI agents collaborating in a futuristic workspace",
                    "conversation_id": self.conversation_id
                }
                await self.client.post(f"{BACKEND_URL}/image/generate", json=image_payload, timeout=60.0)
                
                # Collect image message
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    image_msg = json.loads(message)
                    if image_msg.get("type") == "agent_message" and image_msg["data"].get("image_url"):
                        all_messages.append(image_msg)
                        print("✅ Image message received via WebSocket")
                except asyncio.TimeoutError:
                    print("❌ Image message not received via WebSocket")
                
                # Analyze results
                user_messages = [msg for msg in all_messages if msg.get("type") == "user_message"]
                agent_messages = [msg for msg in all_messages if msg.get("type") == "agent_message" and not msg["data"].get("image_url")]
                image_messages = [msg for msg in all_messages if msg.get("type") == "agent_message" and msg["data"].get("image_url")]
                
                success = len(user_messages) >= 1 and len(agent_messages) >= 4 and len(image_messages) >= 1
                
                if success:
                    await self.log_test("End-to-End WebSocket Flow", True, 
                                      f"Complete flow successful: {len(user_messages)} user, {len(agent_messages)} agent, {len(image_messages)} image messages", 
                                      {"total_messages": len(all_messages), "breakdown": {"user": len(user_messages), "agent": len(agent_messages), "image": len(image_messages)}})
                else:
                    await self.log_test("End-to-End WebSocket Flow", False, 
                                      f"Incomplete flow: {len(user_messages)} user, {len(agent_messages)} agent, {len(image_messages)} image messages")
                
                return success
                
        except Exception as e:
            await self.log_test("End-to-End WebSocket Flow", False, f"Exception: {str(e)}")
            return False
    
    async def run_websocket_tests(self):
        """Run all WebSocket tests"""
        print("🚀 Starting WebSocket Tests for Multi-Agent Chat Platform")
        print(f"🔗 Backend: {BACKEND_URL}")
        print(f"🔌 WebSocket: {WEBSOCKET_URL}")
        print("=" * 70)
        
        # Setup
        if not await self.setup_conversation():
            print("❌ Cannot proceed without conversation setup")
            return self.test_results
        
        # WebSocket Tests
        await self.test_websocket_connection()
        await self.test_websocket_user_message_broadcast()
        await self.test_websocket_agent_conversation_broadcast()
        await self.test_websocket_image_generation_broadcast()
        await self.test_end_to_end_websocket_flow()
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 WEBSOCKET TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if total - passed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        await self.client.aclose()
        return self.test_results

async def main():
    """Main WebSocket test runner"""
    tester = WebSocketTester()
    results = await tester.run_websocket_tests()
    
    # Save results to file
    with open("/app/websocket_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: /app/websocket_test_results.json")
    
    # Return exit code based on results
    failed_tests = sum(1 for result in results if not result["success"])
    return 0 if failed_tests == 0 else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)