#!/usr/bin/env python3
"""
Focused test for the previously failing endpoints
"""

import asyncio
import httpx
import json

BACKEND_URL = "https://keyvault-bulk.preview.emergentagent.com/api"

async def test_fixed_endpoints():
    client = httpx.AsyncClient(timeout=30.0)
    
    print("🔄 Testing fixed endpoints...")
    
    # Test 1: Start conversation
    payload = {
        "topic": "Testing fixed endpoints",
        "agents": ["strategist", "creator"],
        "message_count": 2
    }
    
    response = await client.post(f"{BACKEND_URL}/conversation/start", json=payload)
    if response.status_code == 200:
        conversation_id = response.json()["conversation_id"]
        print(f"✅ Conversation started: {conversation_id}")
        
        # Test 2: Add user message (previously failing)
        message_payload = {"content": "This is a test message to verify the datetime fix"}
        response = await client.post(f"{BACKEND_URL}/conversation/{conversation_id}/message", json=message_payload)
        if response.status_code == 200:
            print("✅ User message added successfully")
        else:
            print(f"❌ User message failed: {response.status_code} - {response.text}")
        
        # Test 3: Image generation (previously failing)
        image_payload = {
            "prompt": "A simple test image of a robot",
            "conversation_id": conversation_id
        }
        
        print("🔄 Testing image generation...")
        response = await client.post(f"{BACKEND_URL}/image/generate", json=image_payload, timeout=60.0)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "image_generated":
                print(f"✅ Image generated successfully: {data.get('url', 'No URL')}")
            else:
                print(f"❌ Image generation failed: {data}")
        else:
            print(f"❌ Image generation failed: {response.status_code} - {response.text}")
        
        # Test 4: Check API stats for key usage
        response = await client.get(f"{BACKEND_URL}/stats")
        if response.status_code == 200:
            stats = response.json()["api_keys"]
            total_requests = sum(key["requestCount"] for key in stats)
            keys_used = sum(1 for key in stats if key["requestCount"] > 0)
            print(f"✅ API Stats: {keys_used} keys used, {total_requests} total requests")
        else:
            print(f"❌ API stats failed: {response.status_code}")
    
    await client.aclose()

if __name__ == "__main__":
    asyncio.run(test_fixed_endpoints())