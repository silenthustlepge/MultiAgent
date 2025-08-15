#!/usr/bin/env python3
"""
Final comprehensive backend test
"""

import asyncio
import httpx
import json

BACKEND_URL = "https://agent-nexus-6.preview.emergentagent.com/api"

async def final_test():
    client = httpx.AsyncClient(timeout=60.0)
    
    print("🚀 Final Backend Test - Multi-Agent Chat Platform")
    print("=" * 60)
    
    # Test 1: Core API endpoints
    tests_passed = 0
    total_tests = 0
    
    # Root endpoint
    total_tests += 1
    response = await client.get(f"{BACKEND_URL}/")
    if response.status_code == 200:
        tests_passed += 1
        print("✅ Root endpoint working")
    else:
        print("❌ Root endpoint failed")
    
    # Agents endpoint
    total_tests += 1
    response = await client.get(f"{BACKEND_URL}/agents")
    if response.status_code == 200:
        agents = response.json()
        if len(agents) == 4:
            tests_passed += 1
            print("✅ All 4 agents configured (Strategist, Creator, Analyst, Visualizer)")
        else:
            print(f"❌ Expected 4 agents, got {len(agents)}")
    else:
        print("❌ Agents endpoint failed")
    
    # Start conversation
    total_tests += 1
    payload = {
        "topic": "Final test of multi-agent collaboration",
        "agents": ["strategist", "creator"],
        "message_count": 2
    }
    response = await client.post(f"{BACKEND_URL}/conversation/start", json=payload)
    if response.status_code == 200:
        conversation_id = response.json()["conversation_id"]
        tests_passed += 1
        print(f"✅ Conversation started: {conversation_id}")
        
        # Add user message
        total_tests += 1
        message_payload = {"content": "What are the key benefits of AI collaboration?"}
        response = await client.post(f"{BACKEND_URL}/conversation/{conversation_id}/message", json=message_payload)
        if response.status_code == 200:
            tests_passed += 1
            print("✅ User message added")
        else:
            print("❌ User message failed")
        
        # Get messages
        total_tests += 1
        response = await client.get(f"{BACKEND_URL}/conversation/{conversation_id}/messages")
        if response.status_code == 200:
            messages = response.json()
            tests_passed += 1
            print(f"✅ Retrieved {len(messages)} messages")
        else:
            print("❌ Get messages failed")
        
        # Generate agent conversation (Together.ai test)
        total_tests += 1
        print("🔄 Testing Together.ai integration...")
        response = await client.post(f"{BACKEND_URL}/conversation/{conversation_id}/generate", timeout=90.0)
        if response.status_code == 200:
            tests_passed += 1
            print("✅ Agent conversation generated (Together.ai working)")
            
            # Check if messages were actually generated
            await asyncio.sleep(2)
            response = await client.get(f"{BACKEND_URL}/conversation/{conversation_id}/messages")
            if response.status_code == 200:
                messages = response.json()
                agent_messages = [msg for msg in messages if not msg.get("is_user", True)]
                print(f"   Generated {len(agent_messages)} agent messages")
        else:
            print(f"❌ Agent conversation failed: {response.status_code}")
        
        # Image generation (FLUX test)
        total_tests += 1
        print("🔄 Testing FLUX image generation...")
        image_payload = {
            "prompt": "A collaborative AI workspace with multiple agents working together",
            "conversation_id": conversation_id
        }
        response = await client.post(f"{BACKEND_URL}/image/generate", json=image_payload, timeout=90.0)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "image_generated":
                tests_passed += 1
                print(f"✅ Image generated: {data.get('url', 'No URL')}")
            else:
                print(f"❌ Image generation failed: {data}")
        else:
            print(f"❌ Image generation failed: {response.status_code}")
    
    # API Stats (Key pool test)
    total_tests += 1
    response = await client.get(f"{BACKEND_URL}/stats")
    if response.status_code == 200:
        stats = response.json()["api_keys"]
        total_requests = sum(key["requestCount"] for key in stats)
        keys_used = sum(1 for key in stats if key["requestCount"] > 0)
        tests_passed += 1
        print(f"✅ API Key Pool: {len(stats)} keys configured, {keys_used} keys used, {total_requests} total requests")
    else:
        print("❌ API stats failed")
    
    await client.aclose()
    
    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS")
    print("=" * 60)
    print(f"Tests Passed: {tests_passed}/{total_tests}")
    print(f"Success Rate: {(tests_passed/total_tests)*100:.1f}%")
    
    if tests_passed == total_tests:
        print("🎉 ALL TESTS PASSED - Backend is fully functional!")
    else:
        print(f"⚠️  {total_tests - tests_passed} tests failed")
    
    return tests_passed, total_tests

if __name__ == "__main__":
    asyncio.run(final_test())