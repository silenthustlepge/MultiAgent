#!/usr/bin/env python3
"""
Enhanced Backend Test Suite for Multi-Agent Chat Platform v2.0
Tests all enhanced features including streaming, robustness, new endpoints, and analytics
"""

import asyncio
import httpx
import json
import time
import websockets
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from environment
BACKEND_URL = "https://fast-stream-logic.preview.emergentagent.com/api"
WEBSOCKET_URL = "wss://fast-stream-logic.preview.emergentagent.com/api/ws"

class EnhancedBackendTester:
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
        
    async def test_system_health(self):
        """Test GET /api/system/health endpoint - NEW ENHANCED ENDPOINT"""
        try:
            response = await self.client.get(f"{BACKEND_URL}/system/health")
            if response.status_code == 200:
                data = response.json()
                required_fields = ["status", "database", "api_keys", "websocket_connections", "timestamp"]
                
                if all(field in data for field in required_fields):
                    # Check detailed health metrics
                    api_keys_info = data.get("api_keys", {})
                    if "active" in api_keys_info and "total_requests" in api_keys_info:
                        health_details = f"Status: {data['status']}, DB: {data['database']}, Active Keys: {api_keys_info['active']}/{api_keys_info['total']}, Total Requests: {api_keys_info['total_requests']}"
                        await self.log_test("System Health", True, health_details, data)
                    else:
                        await self.log_test("System Health", False, "Missing API keys metrics in health response")
                else:
                    missing = [f for f in required_fields if f not in data]
                    await self.log_test("System Health", False, f"Missing required fields: {missing}")
            else:
                await self.log_test("System Health", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            await self.log_test("System Health", False, f"Exception: {str(e)}")

    async def test_enhanced_autonomous_collaboration(self):
        """Test POST /api/conversation/autonomous - ENHANCED AUTONOMOUS COLLABORATION"""
        try:
            payload = {
                "topic": "Future of AI-Human Collaboration in Creative Industries",
                "agents": ["strategist", "creator", "analyst", "visualizer"],
                "collaboration_mode": "autonomous",
                "max_rounds": 3,
                "consensus_threshold": 0.8,
                "streaming_enabled": True
            }
            
            print("🔄 Testing enhanced autonomous collaboration with streaming...")
            response = await self.client.post(f"{BACKEND_URL}/conversation/autonomous", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["conversation_id", "status", "mode", "agents", "streaming_enabled"]
                
                if all(field in data for field in required_fields):
                    self.conversation_id = data["conversation_id"]
                    if data["streaming_enabled"] and data["mode"] == "autonomous":
                        await self.log_test("Enhanced Autonomous Collaboration", True, 
                                          f"Started autonomous collaboration with streaming: {self.conversation_id}, Mode: {data['mode']}", data)
                        
                        # Wait for some autonomous messages to be generated
                        await asyncio.sleep(10)
                        
                        # Check if messages were generated autonomously
                        messages_response = await self.client.get(f"{BACKEND_URL}/conversation/{self.conversation_id}/messages")
                        if messages_response.status_code == 200:
                            messages = messages_response.json()
                            autonomous_messages = [msg for msg in messages if not msg.get("is_user", True)]
                            if len(autonomous_messages) > 0:
                                await self.log_test("Autonomous Message Generation", True, 
                                                  f"Generated {len(autonomous_messages)} autonomous messages")
                            else:
                                await self.log_test("Autonomous Message Generation", False, 
                                                  "No autonomous messages generated")
                    else:
                        await self.log_test("Enhanced Autonomous Collaboration", False, 
                                          f"Streaming not enabled or wrong mode: streaming={data.get('streaming_enabled')}, mode={data.get('mode')}")
                else:
                    missing = [f for f in required_fields if f not in data]
                    await self.log_test("Enhanced Autonomous Collaboration", False, f"Missing fields: {missing}")
            else:
                await self.log_test("Enhanced Autonomous Collaboration", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            await self.log_test("Enhanced Autonomous Collaboration", False, f"Exception: {str(e)}")

    async def test_conversation_summary(self):
        """Test GET /api/conversation/{id}/summary - NEW AI-POWERED SUMMARY"""
        if not self.conversation_id:
            await self.log_test("Conversation Summary", False, "No conversation ID available")
            return
            
        try:
            print("🔄 Testing AI-powered conversation summary generation...")
            response = await self.client.get(f"{BACKEND_URL}/conversation/{self.conversation_id}/summary")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["conversation_id", "summary", "key_insights", "agent_contributions", "consensus_reached"]
                
                if all(field in data for field in required_fields):
                    summary_length = len(data["summary"])
                    insights_count = len(data["key_insights"]) if isinstance(data["key_insights"], list) else 0
                    contributions_count = len(data["agent_contributions"]) if isinstance(data["agent_contributions"], dict) else 0
                    
                    if summary_length > 50 and insights_count > 0:
                        await self.log_test("Conversation Summary", True, 
                                          f"AI summary generated: {summary_length} chars, {insights_count} insights, {contributions_count} agent contributions", data)
                    else:
                        await self.log_test("Conversation Summary", False, 
                                          f"Summary too short or no insights: summary={summary_length} chars, insights={insights_count}")
                else:
                    missing = [f for f in required_fields if f not in data]
                    await self.log_test("Conversation Summary", False, f"Missing fields: {missing}")
            else:
                await self.log_test("Conversation Summary", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            await self.log_test("Conversation Summary", False, f"Exception: {str(e)}")

    async def test_conversation_export(self):
        """Test POST /api/conversation/{id}/export - NEW EXPORT FUNCTIONALITY"""
        if not self.conversation_id:
            await self.log_test("Conversation Export", False, "No conversation ID available")
            return
            
        try:
            # Test JSON export
            json_payload = {"conversation_id": self.conversation_id, "format": "json"}
            json_response = await self.client.post(f"{BACKEND_URL}/conversation/{self.conversation_id}/export", json=json_payload)
            
            if json_response.status_code == 200:
                json_data = json_response.json()
                if json_data.get("format") == "json" and "data" in json_data:
                    export_data = json_data["data"]
                    if "conversation" in export_data and "messages" in export_data:
                        await self.log_test("Conversation Export JSON", True, 
                                          f"JSON export successful with {len(export_data['messages'])} messages")
                    else:
                        await self.log_test("Conversation Export JSON", False, "Missing conversation or messages in export data")
                else:
                    await self.log_test("Conversation Export JSON", False, f"Invalid JSON export format: {json_data}")
            else:
                await self.log_test("Conversation Export JSON", False, f"JSON export failed: HTTP {json_response.status_code}")
            
            # Test Markdown export
            md_payload = {"conversation_id": self.conversation_id, "format": "markdown"}
            md_response = await self.client.post(f"{BACKEND_URL}/conversation/{self.conversation_id}/export", json=md_payload)
            
            if md_response.status_code == 200:
                md_data = md_response.json()
                if md_data.get("format") == "markdown" and "content" in md_data:
                    content_length = len(md_data["content"])
                    if content_length > 100 and "# Conversation:" in md_data["content"]:
                        await self.log_test("Conversation Export Markdown", True, 
                                          f"Markdown export successful: {content_length} characters")
                    else:
                        await self.log_test("Conversation Export Markdown", False, 
                                          f"Markdown content too short or invalid format: {content_length} chars")
                else:
                    await self.log_test("Conversation Export Markdown", False, f"Invalid markdown export: {md_data}")
            else:
                await self.log_test("Conversation Export Markdown", False, f"Markdown export failed: HTTP {md_response.status_code}")
                
        except Exception as e:
            await self.log_test("Conversation Export", False, f"Exception: {str(e)}")

    async def test_agent_analytics(self):
        """Test GET /api/analytics/agents - NEW AGENT PERFORMANCE ANALYTICS"""
        try:
            response = await self.client.get(f"{BACKEND_URL}/analytics/agents")
            
            if response.status_code == 200:
                data = response.json()
                if "agent_metrics" in data and isinstance(data["agent_metrics"], list):
                    metrics = data["agent_metrics"]
                    
                    if len(metrics) > 0:
                        # Check metrics structure
                        valid_metrics = 0
                        for metric in metrics:
                            required_fields = ["agent_type", "total_messages", "avg_response_time", "total_tokens", "error_rate"]
                            if all(field in metric for field in required_fields):
                                valid_metrics += 1
                        
                        if valid_metrics == len(metrics):
                            agent_types = [m["agent_type"] for m in metrics]
                            total_messages = sum(m["total_messages"] for m in metrics)
                            await self.log_test("Agent Analytics", True, 
                                              f"Analytics for {len(metrics)} agents: {agent_types}, Total messages: {total_messages}", data)
                        else:
                            await self.log_test("Agent Analytics", False, 
                                              f"Invalid metrics structure: {valid_metrics}/{len(metrics)} valid")
                    else:
                        await self.log_test("Agent Analytics", True, "No agent metrics available yet (expected for new system)")
                else:
                    await self.log_test("Agent Analytics", False, f"Missing or invalid agent_metrics field: {data}")
            else:
                await self.log_test("Agent Analytics", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            await self.log_test("Agent Analytics", False, f"Exception: {str(e)}")

    async def test_enhanced_stats(self):
        """Test GET /api/stats - ENHANCED WITH PERFORMANCE METRICS"""
        try:
            response = await self.client.get(f"{BACKEND_URL}/stats")
            
            if response.status_code == 200:
                data = response.json()
                if "api_keys" in data and "summary" in data:
                    # Check enhanced fields
                    enhanced_fields_found = 0
                    for key_info in data["api_keys"]:
                        enhanced_fields = ["totalRequests", "errors", "avgResponseTime", "status", "errorRate"]
                        if all(field in key_info for field in enhanced_fields):
                            enhanced_fields_found += 1
                    
                    summary = data["summary"]
                    summary_fields = ["total_keys", "active_keys", "total_requests", "total_errors", "avg_response_time"]
                    
                    if enhanced_fields_found > 0 and all(field in summary for field in summary_fields):
                        await self.log_test("Enhanced Stats", True, 
                                          f"Enhanced stats with performance metrics: {enhanced_fields_found} keys with full metrics, Summary includes: {list(summary.keys())}", data)
                    else:
                        await self.log_test("Enhanced Stats", False, 
                                          f"Missing enhanced fields: keys with metrics={enhanced_fields_found}, summary fields missing")
                else:
                    await self.log_test("Enhanced Stats", False, f"Missing api_keys or summary: {list(data.keys())}")
            else:
                await self.log_test("Enhanced Stats", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            await self.log_test("Enhanced Stats", False, f"Exception: {str(e)}")

    async def test_enhanced_websocket(self):
        """Test WebSocket /api/ws/{id} - ENHANCED WEBSOCKET WITH HEARTBEAT"""
        if not self.conversation_id:
            await self.log_test("Enhanced WebSocket", False, "No conversation ID available")
            return
            
        try:
            websocket_url = f"{WEBSOCKET_URL}/{self.conversation_id}"
            print(f"🔄 Testing enhanced WebSocket connection: {websocket_url}")
            
            # Test WebSocket connection with timeout
            try:
                async with websockets.connect(websocket_url) as websocket:
                    # Wait for connection confirmation
                    message = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(message)
                    
                    if data.get("type") == "connection_established":
                        connection_data = data.get("data", {})
                        if "features" in connection_data and "conversation_id" in connection_data:
                            features = connection_data["features"]
                            await self.log_test("Enhanced WebSocket Connection", True, 
                                              f"Connection established with features: {features}")
                            
                            # Wait for heartbeat (reduced timeout since heartbeat is every 30s)
                            try:
                                heartbeat = await asyncio.wait_for(websocket.recv(), timeout=10)
                                heartbeat_data = json.loads(heartbeat)
                                if heartbeat_data.get("type") == "heartbeat":
                                    await self.log_test("WebSocket Heartbeat", True, "Heartbeat system working")
                                else:
                                    await self.log_test("WebSocket Heartbeat", False, f"Expected heartbeat, got: {heartbeat_data.get('type')}")
                            except asyncio.TimeoutError:
                                await self.log_test("WebSocket Heartbeat", False, "No heartbeat received within 10 seconds (heartbeat every 30s)")
                        else:
                            await self.log_test("Enhanced WebSocket Connection", False, f"Missing features or conversation_id in connection data: {connection_data}")
                    else:
                        await self.log_test("Enhanced WebSocket Connection", False, f"Expected connection_established, got: {data.get('type')}")
                        
            except websockets.exceptions.WebSocketException as e:
                await self.log_test("Enhanced WebSocket", False, f"WebSocket connection failed: {str(e)}")
            except asyncio.TimeoutError:
                await self.log_test("Enhanced WebSocket", False, "WebSocket connection timeout")
                
        except Exception as e:
            await self.log_test("Enhanced WebSocket", False, f"Exception: {str(e)}")

    async def test_enhanced_polling(self):
        """Test GET /api/conversation/{id}/poll - ENHANCED POLLING WITH PERFORMANCE OPTIMIZATION"""
        if not self.conversation_id:
            await self.log_test("Enhanced Polling", False, "No conversation ID available")
            return
            
        try:
            response = await self.client.get(f"{BACKEND_URL}/conversation/{self.conversation_id}/poll")
            
            if response.status_code == 200:
                data = response.json()
                enhanced_fields = ["conversation_id", "messages", "total_messages", "last_updated", "conversation_status"]
                
                if all(field in data for field in enhanced_fields):
                    messages = data["messages"]
                    
                    # Check enhanced message format
                    enhanced_message_fields = ["id", "content", "agent_type", "timestamp", "is_user", "streaming_status", "response_time", "token_count"]
                    valid_enhanced_messages = 0
                    
                    for msg in messages:
                        if any(field in msg for field in ["streaming_status", "response_time", "token_count"]):
                            valid_enhanced_messages += 1
                    
                    await self.log_test("Enhanced Polling", True, 
                                      f"Enhanced polling working: {len(messages)} messages, {valid_enhanced_messages} with enhanced fields, Status: {data['conversation_status']}", data)
                else:
                    missing = [f for f in enhanced_fields if f not in data]
                    await self.log_test("Enhanced Polling", False, f"Missing enhanced fields: {missing}")
            else:
                await self.log_test("Enhanced Polling", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            await self.log_test("Enhanced Polling", False, f"Exception: {str(e)}")

    async def test_streaming_indicators(self):
        """Test streaming with visual indicators by monitoring WebSocket messages"""
        if not self.conversation_id:
            await self.log_test("Streaming Indicators", False, "No conversation ID available")
            return
            
        try:
            # Create a new conversation with streaming enabled
            payload = {
                "topic": "Testing Real-time Streaming Capabilities",
                "agents": ["strategist"],
                "collaboration_mode": "autonomous",
                "max_rounds": 1,
                "streaming_enabled": True
            }
            
            response = await self.client.post(f"{BACKEND_URL}/conversation/autonomous", json=payload)
            if response.status_code == 200:
                stream_conversation_id = response.json()["conversation_id"]
                
                # Monitor streaming via polling (since WebSocket might have auth issues)
                streaming_detected = False
                for attempt in range(10):  # Check for 10 seconds
                    await asyncio.sleep(1)
                    poll_response = await self.client.get(f"{BACKEND_URL}/conversation/{stream_conversation_id}/poll")
                    
                    if poll_response.status_code == 200:
                        poll_data = poll_response.json()
                        messages = poll_data.get("messages", [])
                        
                        # Look for streaming status indicators
                        for msg in messages:
                            if msg.get("streaming_status") in ["started", "streaming", "completed"]:
                                streaming_detected = True
                                break
                        
                        if streaming_detected:
                            break
                
                if streaming_detected:
                    await self.log_test("Streaming Indicators", True, "Streaming status indicators detected in messages")
                else:
                    await self.log_test("Streaming Indicators", False, "No streaming status indicators found")
            else:
                await self.log_test("Streaming Indicators", False, f"Failed to create streaming conversation: {response.status_code}")
                
        except Exception as e:
            await self.log_test("Streaming Indicators", False, f"Exception: {str(e)}")

    async def test_retry_logic(self):
        """Test retry logic and error handling by monitoring API key performance"""
        try:
            # Get initial stats
            initial_response = await self.client.get(f"{BACKEND_URL}/stats")
            if initial_response.status_code == 200:
                initial_stats = initial_response.json()
                initial_errors = sum(key["errors"] for key in initial_stats["api_keys"])
                
                # Make several requests to potentially trigger retries
                for i in range(5):
                    test_payload = {
                        "topic": f"Retry test {i}",
                        "agents": ["strategist"],
                        "message_count": 1
                    }
                    await self.client.post(f"{BACKEND_URL}/conversation/start", json=test_payload)
                    await asyncio.sleep(0.5)
                
                # Check final stats
                final_response = await self.client.get(f"{BACKEND_URL}/stats")
                if final_response.status_code == 200:
                    final_stats = final_response.json()
                    final_errors = sum(key["errors"] for key in final_stats["api_keys"])
                    total_requests = sum(key["totalRequests"] for key in final_stats["api_keys"])
                    
                    # Check if error handling is working (low error rate is good)
                    error_rate = (final_errors / max(total_requests, 1)) * 100
                    
                    if error_rate < 10:  # Less than 10% error rate is acceptable
                        await self.log_test("Retry Logic & Error Handling", True, 
                                          f"Error handling working well: {final_errors} errors out of {total_requests} requests ({error_rate:.1f}% error rate)")
                    else:
                        await self.log_test("Retry Logic & Error Handling", False, 
                                          f"High error rate detected: {error_rate:.1f}%")
                else:
                    await self.log_test("Retry Logic & Error Handling", False, "Could not get final stats")
            else:
                await self.log_test("Retry Logic & Error Handling", False, "Could not get initial stats")
                
        except Exception as e:
            await self.log_test("Retry Logic & Error Handling", False, f"Exception: {str(e)}")

    async def run_all_enhanced_tests(self):
        """Run all enhanced backend tests"""
        print("🚀 Starting Enhanced Multi-Agent Chat Platform Backend Tests v2.0")
        print(f"🔗 Testing against: {BACKEND_URL}")
        print("🔗 WebSocket URL: {WEBSOCKET_URL}")
        print("=" * 80)
        
        # Enhanced System Tests
        await self.test_system_health()
        await self.test_enhanced_stats()
        
        # Enhanced Autonomous Collaboration
        await self.test_enhanced_autonomous_collaboration()
        
        # New Enhanced Endpoints
        await self.test_conversation_summary()
        await self.test_conversation_export()
        await self.test_agent_analytics()
        
        # Enhanced Real-time Features
        await self.test_enhanced_websocket()
        await self.test_enhanced_polling()
        await self.test_streaming_indicators()
        
        # Robustness Features
        await self.test_retry_logic()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 ENHANCED TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Enhanced Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if total - passed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        else:
            print("\n🎉 ALL ENHANCED TESTS PASSED!")
        
        await self.client.aclose()
        return self.test_results

async def main():
    """Main enhanced test runner"""
    tester = EnhancedBackendTester()
    results = await tester.run_all_enhanced_tests()
    
    # Save results to file
    with open("/app/enhanced_backend_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: /app/enhanced_backend_test_results.json")
    
    # Return exit code based on results
    failed_tests = sum(1 for result in results if not result["success"])
    return 0 if failed_tests == 0 else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)