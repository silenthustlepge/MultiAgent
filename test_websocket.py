#!/usr/bin/env python3

import asyncio
import websockets
import json

async def test_websocket():
    uri = "wss://keyvault-bulk.preview.emergentagent.com/api/ws/test-conversation"
    print(f"Testing WebSocket connection to: {uri}")
    
    try:
        # Try to connect to WebSocket
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connection established successfully!")
            
            # Wait for initial message
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📨 Received message: {message}")
                data = json.loads(message)
                print(f"📋 Parsed data: {data}")
            except asyncio.TimeoutError:
                print("⏰ No initial message received within 5 seconds")
            
            # Send a test message
            test_message = json.dumps({
                "type": "test",
                "data": {"message": "Hello WebSocket"}
            })
            await websocket.send(test_message)
            print(f"📤 Sent test message: {test_message}")
            
            # Try to receive response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                print(f"📨 Received response: {response}")
            except asyncio.TimeoutError:
                print("⏰ No response received within 3 seconds")
                
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ WebSocket connection failed with status code: {e.status_code}")
        print(f"   Headers: {e.response_headers}")
    except Exception as e:
        print(f"❌ WebSocket connection failed: {str(e)}")
        print(f"   Error type: {type(e).__name__}")

if __name__ == "__main__":
    asyncio.run(test_websocket())