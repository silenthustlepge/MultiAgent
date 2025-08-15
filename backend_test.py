#!/usr/bin/env python3
"""
Backend Test Suite for Multi-Agent Chat Platform
Tests all API endpoints, Together.ai integration, and key pool management
"""

import asyncio
import httpx
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from environment
BACKEND_URL = "https://fast-stream-logic.preview.emergentagent.com/api"

class BackendTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_results = []
        self.conversation_id = None
        
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
        
    async def test_root_endpoint(self):
        """Test GET /api/ endpoint"""
        try:
            response = await self.client.get(f"{BACKEND_URL}/")
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    await self.log_test("Root Endpoint", True, f"Status: {response.status_code}, Message: {data['message']}", data)
                else:
                    await self.log_test("Root Endpoint", False, f"Missing message field in response: {data}")
            else:
                await self.log_test("Root Endpoint", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            await self.log_test("Root Endpoint", False, f"Exception: {str(e)}")
    
    async def test_get_agents(self):
        """Test GET /api/agents endpoint"""
        try:
            response = await self.client.get(f"{BACKEND_URL}/agents")
            if response.status_code == 200:
                data = response.json()
                expected_agents = ["strategist", "creator", "analyst", "visualizer"]
                
                if all(agent in data for agent in expected_agents):
                    # Check agent structure
                    agent_details = []
                    for agent_key, agent_data in data.items():
                        if all(key in agent_data for key in ["name", "model", "role", "persona", "color"]):
                            agent_details.append(f"{agent_key}: {agent_data['name']} ({agent_data['model']})")
                        else:
                            await self.log_test("Get Agents", False, f"Agent {agent_key} missing required fields")
                            return
                    
                    await self.log_test("Get Agents", True, f"All 4 agents configured correctly: {', '.join(agent_details)}", data)
                else:
                    missing = [agent for agent in expected_agents if agent not in data]
                    await self.log_test("Get Agents", False, f"Missing agents: {missing}")
            else:
                await self.log_test("Get Agents", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            await self.log_test("Get Agents", False, f"Exception: {str(e)}")
    
    async def test_start_conversation(self):
        """Test POST /api/conversation/start endpoint"""
        try:
            payload = {
                "topic": "AI and the Future of Technology",
                "agents": ["strategist", "creator", "analyst"],
                "message_count": 3
            }
            
            response = await self.client.post(f"{BACKEND_URL}/conversation/start", json=payload)
            if response.status_code == 200:
                data = response.json()
                if "conversation_id" in data and "status" in data:
                    self.conversation_id = data["conversation_id"]
                    await self.log_test("Start Conversation", True, f"Conversation started with ID: {self.conversation_id}", data)
                else:
                    await self.log_test("Start Conversation", False, f"Missing required fields in response: {data}")
            else:
                await self.log_test("Start Conversation", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            await self.log_test("Start Conversation", False, f"Exception: {str(e)}")
    
    async def test_add_user_message(self):
        """Test POST /api/conversation/{id}/message endpoint"""
        if not self.conversation_id:
            await self.log_test("Add User Message", False, "No conversation ID available")
            return
            
        try:
            payload = {"content": "What are the key trends in AI development for 2025?"}
            
            response = await self.client.post(
                f"{BACKEND_URL}/conversation/{self.conversation_id}/message", 
                json=payload
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "message_added":
                    await self.log_test("Add User Message", True, "User message added successfully", data)
                else:
                    await self.log_test("Add User Message", False, f"Unexpected response: {data}")
            else:
                await self.log_test("Add User Message", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            await self.log_test("Add User Message", False, f"Exception: {str(e)}")
    
    async def test_get_messages(self):
        """Test GET /api/conversation/{id}/messages endpoint"""
        if not self.conversation_id:
            await self.log_test("Get Messages", False, "No conversation ID available")
            return
            
        try:
            response = await self.client.get(f"{BACKEND_URL}/conversation/{self.conversation_id}/messages")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    await self.log_test("Get Messages", True, f"Retrieved {len(data)} messages", {"message_count": len(data)})
                else:
                    await self.log_test("Get Messages", False, f"Expected list, got: {type(data)}")
            else:
                await self.log_test("Get Messages", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            await self.log_test("Get Messages", False, f"Exception: {str(e)}")
    
    async def test_api_stats(self):
        """Test GET /api/stats endpoint"""
        try:
            response = await self.client.get(f"{BACKEND_URL}/stats")
            if response.status_code == 200:
                data = response.json()
                if "api_keys" in data and isinstance(data["api_keys"], list):
                    key_count = len(data["api_keys"])
                    if key_count == 8:  # Expected 8 Together.ai keys
                        # Check key structure
                        valid_keys = 0
                        for key_info in data["api_keys"]:
                            if all(field in key_info for field in ["keyId", "requestCount", "rateLimit", "utilizationPercent"]):
                                valid_keys += 1
                        
                        if valid_keys == 8:
                            await self.log_test("API Stats", True, f"All 8 API keys properly configured and tracked", data)
                        else:
                            await self.log_test("API Stats", False, f"Only {valid_keys}/8 keys have valid structure")
                    else:
                        await self.log_test("API Stats", False, f"Expected 8 API keys, found {key_count}")
                else:
                    await self.log_test("API Stats", False, f"Missing or invalid api_keys field: {data}")
            else:
                await self.log_test("API Stats", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            await self.log_test("API Stats", False, f"Exception: {str(e)}")
    
    async def test_generate_conversation(self):
        """Test POST /api/conversation/{id}/generate endpoint - Together.ai Integration Test"""
        if not self.conversation_id:
            await self.log_test("Generate Conversation", False, "No conversation ID available")
            return
            
        try:
            print("🔄 Testing Together.ai integration - this may take 30-60 seconds...")
            response = await self.client.post(
                f"{BACKEND_URL}/conversation/{self.conversation_id}/generate",
                timeout=60.0
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "conversation_generated":
                    await self.log_test("Generate Conversation", True, "Agent conversation generated successfully - Together.ai integration working", data)
                    
                    # Verify messages were actually generated
                    await asyncio.sleep(2)  # Wait for messages to be saved
                    messages_response = await self.client.get(f"{BACKEND_URL}/conversation/{self.conversation_id}/messages")
                    if messages_response.status_code == 200:
                        messages = messages_response.json()
                        agent_messages = [msg for msg in messages if not msg.get("is_user", True)]
                        if len(agent_messages) > 0:
                            await self.log_test("Agent Message Generation", True, f"Generated {len(agent_messages)} agent messages")
                        else:
                            await self.log_test("Agent Message Generation", False, "No agent messages found after generation")
                else:
                    await self.log_test("Generate Conversation", False, f"Unexpected response: {data}")
            else:
                await self.log_test("Generate Conversation", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            await self.log_test("Generate Conversation", False, f"Exception: {str(e)}")
    
    async def test_polling_endpoint(self):
        """Test GET /api/conversation/{id}/poll endpoint - NEW Polling Fallback System"""
        if not self.conversation_id:
            await self.log_test("Polling Endpoint", False, "No conversation ID available")
            return
            
        try:
            print("🔄 Testing new polling endpoint for real-time updates...")
            response = await self.client.get(f"{BACKEND_URL}/conversation/{self.conversation_id}/poll")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["conversation_id", "messages", "total_messages"]
                
                if all(field in data for field in required_fields):
                    if data["conversation_id"] == self.conversation_id:
                        message_count = data["total_messages"]
                        messages = data["messages"]
                        
                        # Validate message format
                        if isinstance(messages, list):
                            valid_messages = 0
                            for msg in messages:
                                if all(key in msg for key in ["id", "content", "agent_type", "timestamp"]):
                                    valid_messages += 1
                            
                            if valid_messages == len(messages):
                                await self.log_test("Polling Endpoint", True, 
                                                  f"Polling endpoint working - retrieved {message_count} messages with proper format", data)
                            else:
                                await self.log_test("Polling Endpoint", False, 
                                                  f"Message format validation failed - {valid_messages}/{len(messages)} messages valid")
                        else:
                            await self.log_test("Polling Endpoint", False, f"Messages field is not a list: {type(messages)}")
                    else:
                        await self.log_test("Polling Endpoint", False, f"Conversation ID mismatch: expected {self.conversation_id}, got {data['conversation_id']}")
                else:
                    missing_fields = [field for field in required_fields if field not in data]
                    await self.log_test("Polling Endpoint", False, f"Missing required fields: {missing_fields}")
            else:
                await self.log_test("Polling Endpoint", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            await self.log_test("Polling Endpoint", False, f"Exception: {str(e)}")

    async def test_image_generation(self):
        """Test POST /api/image/generate endpoint - FLUX Model Test"""
        if not self.conversation_id:
            await self.log_test("Image Generation", False, "No conversation ID available")
            return
            
        try:
            payload = {
                "prompt": "A futuristic AI robot collaborating with humans in a modern office",
                "conversation_id": self.conversation_id
            }
            
            print("🔄 Testing FLUX image generation - this may take 30-60 seconds...")
            response = await self.client.post(
                f"{BACKEND_URL}/image/generate", 
                json=payload,
                timeout=60.0
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "image_generated" and "url" in data:
                    await self.log_test("Image Generation", True, f"Image generated successfully: {data['url']}", data)
                else:
                    await self.log_test("Image Generation", False, f"Image generation failed: {data}")
            else:
                await self.log_test("Image Generation", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            await self.log_test("Image Generation", False, f"Exception: {str(e)}")
    
    async def test_key_pool_management(self):
        """Test API key rotation by making multiple requests"""
        try:
            print("🔄 Testing API key pool management...")
            
            # Get initial stats
            initial_response = await self.client.get(f"{BACKEND_URL}/stats")
            if initial_response.status_code != 200:
                await self.log_test("Key Pool Management", False, "Could not get initial stats")
                return
            
            initial_stats = initial_response.json()["api_keys"]
            initial_total_requests = sum(key["requestCount"] for key in initial_stats)
            
            # Make several API calls to test rotation
            test_conversations = []
            for i in range(3):
                payload = {
                    "topic": f"Test topic {i+1}",
                    "agents": ["strategist"],
                    "message_count": 1
                }
                response = await self.client.post(f"{BACKEND_URL}/conversation/start", json=payload)
                if response.status_code == 200:
                    test_conversations.append(response.json()["conversation_id"])
                await asyncio.sleep(1)
            
            # Get final stats
            final_response = await self.client.get(f"{BACKEND_URL}/stats")
            if final_response.status_code == 200:
                final_stats = final_response.json()["api_keys"]
                final_total_requests = sum(key["requestCount"] for key in final_stats)
                
                if final_total_requests > initial_total_requests:
                    # Check if requests are distributed across keys
                    keys_with_requests = sum(1 for key in final_stats if key["requestCount"] > 0)
                    await self.log_test("Key Pool Management", True, 
                                      f"Key rotation working - {keys_with_requests} keys used, total requests increased from {initial_total_requests} to {final_total_requests}")
                else:
                    await self.log_test("Key Pool Management", False, "No increase in request count detected")
            else:
                await self.log_test("Key Pool Management", False, "Could not get final stats")
                
        except Exception as e:
            await self.log_test("Key Pool Management", False, f"Exception: {str(e)}")
    
    async def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Multi-Agent Chat Platform Backend Tests")
        print(f"🔗 Testing against: {BACKEND_URL}")
        print("=" * 60)
        
        # Core API Tests
        await self.test_root_endpoint()
        await self.test_get_agents()
        await self.test_start_conversation()
        await self.test_add_user_message()
        await self.test_get_messages()
        await self.test_polling_endpoint()  # NEW: Test polling fallback system
        await self.test_api_stats()
        
        # Advanced Integration Tests
        await self.test_key_pool_management()
        await self.test_generate_conversation()
        await self.test_image_generation()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
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
    """Main test runner"""
    tester = BackendTester()
    results = await tester.run_all_tests()
    
    # Save results to file
    with open("/app/backend_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: /app/backend_test_results.json")
    
    # Return exit code based on results
    failed_tests = sum(1 for result in results if not result["success"])
    return 0 if failed_tests == 0 else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)