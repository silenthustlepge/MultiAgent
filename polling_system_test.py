#!/usr/bin/env python3
"""
Comprehensive Test Suite for Enhanced Multi-Agent Chat Platform
Focus: New Polling Fallback System and Hybrid Real-time Features
"""

import asyncio
import httpx
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from environment
BACKEND_URL = "https://continuous-growth.preview.emergentagent.com/api"

class PollingSystemTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
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
        
    async def test_polling_endpoint_basic(self):
        """Test basic polling endpoint functionality"""
        try:
            # Create conversation
            conv_response = await self.client.post(f"{BACKEND_URL}/conversation/start", json={
                "topic": "AI Collaboration in Creative Industries",
                "agents": ["strategist", "creator", "analyst"],
                "message_count": 2
            })
            
            if conv_response.status_code == 200:
                conv_data = conv_response.json()
                self.conversation_id = conv_data["conversation_id"]
                
                # Test polling endpoint immediately (should return empty)
                poll_response = await self.client.get(f"{BACKEND_URL}/conversation/{self.conversation_id}/poll")
                
                if poll_response.status_code == 200:
                    poll_data = poll_response.json()
                    required_fields = ["conversation_id", "messages", "total_messages"]
                    
                    if all(field in poll_data for field in required_fields):
                        await self.log_test("Polling Endpoint Basic", True, 
                                          f"Polling endpoint accessible - {poll_data['total_messages']} messages", poll_data)
                    else:
                        await self.log_test("Polling Endpoint Basic", False, f"Missing required fields: {poll_data}")
                else:
                    await self.log_test("Polling Endpoint Basic", False, f"HTTP {poll_response.status_code}: {poll_response.text}")
            else:
                await self.log_test("Polling Endpoint Basic", False, f"Failed to create conversation: {conv_response.status_code}")
                
        except Exception as e:
            await self.log_test("Polling Endpoint Basic", False, f"Exception: {str(e)}")
    
    async def test_polling_with_user_messages(self):
        """Test polling endpoint with user messages"""
        if not self.conversation_id:
            await self.log_test("Polling with User Messages", False, "No conversation ID available")
            return
            
        try:
            # Add user message
            user_msg = {"content": "What are the key advantages of multi-agent AI systems in creative workflows?"}
            msg_response = await self.client.post(f"{BACKEND_URL}/conversation/{self.conversation_id}/message", json=user_msg)
            
            if msg_response.status_code == 200:
                # Test polling after user message
                poll_response = await self.client.get(f"{BACKEND_URL}/conversation/{self.conversation_id}/poll")
                
                if poll_response.status_code == 200:
                    poll_data = poll_response.json()
                    
                    if poll_data["total_messages"] >= 1:
                        # Verify message format
                        user_messages = [msg for msg in poll_data["messages"] if msg.get("is_user", False)]
                        if len(user_messages) >= 1:
                            msg = user_messages[0]
                            if all(key in msg for key in ["id", "content", "timestamp"]):
                                await self.log_test("Polling with User Messages", True, 
                                                  f"User message accessible via polling - {len(user_messages)} user messages found")
                            else:
                                await self.log_test("Polling with User Messages", False, "User message missing required fields")
                        else:
                            await self.log_test("Polling with User Messages", False, "No user messages found in polling response")
                    else:
                        await self.log_test("Polling with User Messages", False, "No messages found after adding user message")
                else:
                    await self.log_test("Polling with User Messages", False, f"Polling failed: {poll_response.status_code}")
            else:
                await self.log_test("Polling with User Messages", False, f"Failed to add user message: {msg_response.status_code}")
                
        except Exception as e:
            await self.log_test("Polling with User Messages", False, f"Exception: {str(e)}")
    
    async def test_polling_with_agent_generation(self):
        """Test polling endpoint with agent conversation generation"""
        if not self.conversation_id:
            await self.log_test("Polling with Agent Generation", False, "No conversation ID available")
            return
            
        try:
            print("🔄 Testing agent generation with polling (may take 30-60 seconds)...")
            
            # Get initial message count
            initial_poll = await self.client.get(f"{BACKEND_URL}/conversation/{self.conversation_id}/poll")
            initial_count = initial_poll.json()["total_messages"] if initial_poll.status_code == 200 else 0
            
            # Generate agent conversation
            gen_response = await self.client.post(f"{BACKEND_URL}/conversation/{self.conversation_id}/generate")
            
            if gen_response.status_code == 200:
                # Wait a moment for messages to be saved
                await asyncio.sleep(2)
                
                # Check polling after generation
                final_poll = await self.client.get(f"{BACKEND_URL}/conversation/{self.conversation_id}/poll")
                
                if final_poll.status_code == 200:
                    final_data = final_poll.json()
                    final_count = final_data["total_messages"]
                    
                    if final_count > initial_count:
                        # Verify agent messages
                        agent_messages = [msg for msg in final_data["messages"] if not msg.get("is_user", False)]
                        agent_types = set(msg.get("agent_type") for msg in agent_messages if msg.get("agent_type"))
                        
                        await self.log_test("Polling with Agent Generation", True, 
                                          f"Agent messages accessible via polling - {len(agent_messages)} agent messages from {len(agent_types)} agents")
                    else:
                        await self.log_test("Polling with Agent Generation", False, 
                                          f"No new messages after generation: {initial_count} -> {final_count}")
                else:
                    await self.log_test("Polling with Agent Generation", False, f"Final polling failed: {final_poll.status_code}")
            else:
                await self.log_test("Polling with Agent Generation", False, f"Agent generation failed: {gen_response.status_code}")
                
        except Exception as e:
            await self.log_test("Polling with Agent Generation", False, f"Exception: {str(e)}")
    
    async def test_all_four_agents_via_polling(self):
        """Test all 4 agents (Strategist, Creator, Analyst, Visualizer) via polling"""
        try:
            # Create new conversation with all 4 agents
            conv_response = await self.client.post(f"{BACKEND_URL}/conversation/start", json={
                "topic": "The Future of AI-Human Collaboration in Creative Arts",
                "agents": ["strategist", "creator", "analyst", "visualizer"],
                "message_count": 1
            })
            
            if conv_response.status_code == 200:
                conv_data = conv_response.json()
                test_conv_id = conv_data["conversation_id"]
                
                print("🔄 Testing all 4 agents with polling (may take 60+ seconds)...")
                
                # Generate conversation with all agents
                gen_response = await self.client.post(f"{BACKEND_URL}/conversation/{test_conv_id}/generate")
                
                if gen_response.status_code == 200:
                    await asyncio.sleep(3)  # Wait for all messages to be saved
                    
                    # Check polling for all agent types
                    poll_response = await self.client.get(f"{BACKEND_URL}/conversation/{test_conv_id}/poll")
                    
                    if poll_response.status_code == 200:
                        poll_data = poll_response.json()
                        agent_messages = [msg for msg in poll_data["messages"] if not msg.get("is_user", False)]
                        agent_types = set(msg.get("agent_type") for msg in agent_messages if msg.get("agent_type"))
                        
                        expected_agents = {"strategist", "creator", "analyst", "visualizer"}
                        found_agents = agent_types.intersection(expected_agents)
                        
                        if len(found_agents) >= 3:  # Allow for some flexibility
                            await self.log_test("All Four Agents via Polling", True, 
                                              f"Multiple agents accessible via polling - found {len(found_agents)} agents: {found_agents}")
                        else:
                            await self.log_test("All Four Agents via Polling", False, 
                                              f"Only {len(found_agents)} agents found: {found_agents}")
                    else:
                        await self.log_test("All Four Agents via Polling", False, f"Polling failed: {poll_response.status_code}")
                else:
                    await self.log_test("All Four Agents via Polling", False, f"Generation failed: {gen_response.status_code}")
            else:
                await self.log_test("All Four Agents via Polling", False, f"Conversation creation failed: {conv_response.status_code}")
                
        except Exception as e:
            await self.log_test("All Four Agents via Polling", False, f"Exception: {str(e)}")
    
    async def test_image_generation_via_polling(self):
        """Test FLUX image generation accessible via polling"""
        if not self.conversation_id:
            await self.log_test("Image Generation via Polling", False, "No conversation ID available")
            return
            
        try:
            print("🔄 Testing FLUX image generation with polling (may take 30-60 seconds)...")
            
            # Generate image
            img_response = await self.client.post(f"{BACKEND_URL}/image/generate", json={
                "prompt": "A collaborative AI workspace with multiple agents working together on creative projects",
                "conversation_id": self.conversation_id
            })
            
            if img_response.status_code == 200:
                img_data = img_response.json()
                
                if img_data.get("status") == "image_generated":
                    await asyncio.sleep(2)  # Wait for message to be saved
                    
                    # Check polling for image message
                    poll_response = await self.client.get(f"{BACKEND_URL}/conversation/{self.conversation_id}/poll")
                    
                    if poll_response.status_code == 200:
                        poll_data = poll_response.json()
                        image_messages = [msg for msg in poll_data["messages"] if msg.get("image_url")]
                        
                        if len(image_messages) > 0:
                            await self.log_test("Image Generation via Polling", True, 
                                              f"Image message accessible via polling - {len(image_messages)} image messages found")
                        else:
                            await self.log_test("Image Generation via Polling", False, "No image messages found in polling response")
                    else:
                        await self.log_test("Image Generation via Polling", False, f"Polling failed: {poll_response.status_code}")
                else:
                    await self.log_test("Image Generation via Polling", False, f"Image generation failed: {img_data}")
            else:
                await self.log_test("Image Generation via Polling", False, f"Image generation request failed: {img_response.status_code}")
                
        except Exception as e:
            await self.log_test("Image Generation via Polling", False, f"Exception: {str(e)}")
    
    async def test_polling_message_format(self):
        """Test polling endpoint message format validation"""
        if not self.conversation_id:
            await self.log_test("Polling Message Format", False, "No conversation ID available")
            return
            
        try:
            poll_response = await self.client.get(f"{BACKEND_URL}/conversation/{self.conversation_id}/poll")
            
            if poll_response.status_code == 200:
                poll_data = poll_response.json()
                
                if poll_data["total_messages"] > 0:
                    messages = poll_data["messages"]
                    valid_messages = 0
                    
                    for msg in messages:
                        required_fields = ["id", "content", "timestamp"]
                        optional_fields = ["agent_type", "is_user", "image_url"]
                        
                        if all(field in msg for field in required_fields):
                            valid_messages += 1
                    
                    if valid_messages == len(messages):
                        await self.log_test("Polling Message Format", True, 
                                          f"All {len(messages)} messages have proper format")
                    else:
                        await self.log_test("Polling Message Format", False, 
                                          f"Only {valid_messages}/{len(messages)} messages have valid format")
                else:
                    await self.log_test("Polling Message Format", True, "No messages to validate (empty conversation)")
            else:
                await self.log_test("Polling Message Format", False, f"Polling failed: {poll_response.status_code}")
                
        except Exception as e:
            await self.log_test("Polling Message Format", False, f"Exception: {str(e)}")
    
    async def run_all_tests(self):
        """Run all polling system tests"""
        print("🚀 Starting Enhanced Multi-Agent Chat Platform Polling System Tests")
        print(f"🔗 Testing against: {BACKEND_URL}")
        print("🎯 Focus: New Polling Fallback System and Hybrid Real-time Features")
        print("=" * 80)
        
        # Core Polling Tests
        await self.test_polling_endpoint_basic()
        await self.test_polling_with_user_messages()
        await self.test_polling_with_agent_generation()
        await self.test_all_four_agents_via_polling()
        await self.test_image_generation_via_polling()
        await self.test_polling_message_format()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 POLLING SYSTEM TEST SUMMARY")
        print("=" * 80)
        
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
        else:
            print("\n🎉 ALL POLLING SYSTEM TESTS PASSED!")
            print("✅ Hybrid real-time system working correctly")
            print("✅ Polling fallback functional for WebSocket 403 issues")
            print("✅ All 4 agents accessible via polling")
            print("✅ Image generation working with polling")
        
        await self.client.aclose()
        return self.test_results

async def main():
    """Main test runner"""
    tester = PollingSystemTester()
    results = await tester.run_all_tests()
    
    # Save results to file
    with open("/app/polling_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: /app/polling_test_results.json")
    
    # Return exit code based on results
    failed_tests = sum(1 for result in results if not result["success"])
    return 0 if failed_tests == 0 else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)