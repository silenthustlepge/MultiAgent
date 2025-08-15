#!/usr/bin/env python3
"""
Streaming Test - Test streaming indicators specifically
"""

import asyncio
import httpx
import json
from datetime import datetime

BACKEND_URL = "https://fast-stream-logic.preview.emergentagent.com/api"

async def test_streaming_indicators():
    """Test streaming indicators with a longer conversation"""
    client = httpx.AsyncClient(timeout=60.0)
    
    try:
        # Create autonomous conversation with more rounds
        payload = {
            "topic": "Comprehensive Analysis of AI Ethics and Future Implications",
            "agents": ["strategist", "creator", "analyst"],
            "collaboration_mode": "autonomous",
            "max_rounds": 5,
            "streaming_enabled": True
        }
        
        print("🔄 Creating autonomous conversation with streaming...")
        response = await client.post(f"{BACKEND_URL}/conversation/autonomous", json=payload)
        
        if response.status_code == 200:
            conversation_id = response.json()["conversation_id"]
            print(f"✅ Created conversation: {conversation_id}")
            
            # Monitor for streaming indicators over time
            streaming_indicators_found = []
            
            for attempt in range(30):  # Monitor for 30 seconds
                await asyncio.sleep(1)
                
                poll_response = await client.get(f"{BACKEND_URL}/conversation/{conversation_id}/poll")
                if poll_response.status_code == 200:
                    data = poll_response.json()
                    messages = data.get("messages", [])
                    
                    for msg in messages:
                        streaming_status = msg.get("streaming_status")
                        if streaming_status and streaming_status not in streaming_indicators_found:
                            streaming_indicators_found.append(streaming_status)
                            print(f"🔍 Found streaming indicator: {streaming_status}")
                    
                    # Also check for response_time and token_count (performance indicators)
                    performance_indicators = []
                    for msg in messages:
                        if msg.get("response_time") is not None:
                            performance_indicators.append("response_time")
                        if msg.get("token_count") is not None:
                            performance_indicators.append("token_count")
                    
                    if performance_indicators:
                        print(f"🔍 Found performance indicators: {set(performance_indicators)}")
                    
                    print(f"📊 Attempt {attempt+1}: {len(messages)} messages, Status: {data.get('conversation_status')}")
                    
                    if data.get('conversation_status') == 'completed':
                        print("✅ Conversation completed")
                        break
            
            print(f"\n📋 Final Results:")
            print(f"Streaming indicators found: {streaming_indicators_found}")
            print(f"Total messages: {len(messages)}")
            
            # Final detailed check
            final_response = await client.get(f"{BACKEND_URL}/conversation/{conversation_id}/poll")
            if final_response.status_code == 200:
                final_data = final_response.json()
                final_messages = final_data.get("messages", [])
                
                print(f"\n🔍 Detailed Message Analysis:")
                for i, msg in enumerate(final_messages):
                    print(f"Message {i+1}:")
                    print(f"  - Agent: {msg.get('agent_type', 'user')}")
                    print(f"  - Content length: {len(msg.get('content', ''))}")
                    print(f"  - Streaming status: {msg.get('streaming_status')}")
                    print(f"  - Response time: {msg.get('response_time')}")
                    print(f"  - Token count: {msg.get('token_count')}")
                    print()
        
        else:
            print(f"❌ Failed to create conversation: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    finally:
        await client.aclose()

if __name__ == "__main__":
    asyncio.run(test_streaming_indicators())