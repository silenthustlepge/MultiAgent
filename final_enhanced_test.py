#!/usr/bin/env python3
"""
Final Enhanced Backend Test - Focus on working features
"""

import asyncio
import httpx
import json
from datetime import datetime

BACKEND_URL = "https://fast-stream-logic.preview.emergentagent.com/api"

async def run_final_test():
    """Run final comprehensive test of all working enhanced features"""
    client = httpx.AsyncClient(timeout=60.0)
    results = []
    
    def log_result(test_name, success, details):
        results.append({"test": test_name, "success": success, "details": details})
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}: {details}")
    
    try:
        print("🚀 Final Enhanced Multi-Agent Chat Platform Test")
        print("=" * 60)
        
        # 1. System Health Check
        response = await client.get(f"{BACKEND_URL}/system/health")
        if response.status_code == 200:
            data = response.json()
            log_result("System Health Endpoint", True, f"Status: {data['status']}, DB: {data['database']}")
        else:
            log_result("System Health Endpoint", False, f"HTTP {response.status_code}")
        
        # 2. Enhanced Stats
        response = await client.get(f"{BACKEND_URL}/stats")
        if response.status_code == 200:
            data = response.json()
            if "summary" in data and "avg_response_time" in data["summary"]:
                log_result("Enhanced API Stats", True, f"Enhanced stats with performance metrics")
            else:
                log_result("Enhanced API Stats", False, "Missing enhanced fields")
        else:
            log_result("Enhanced API Stats", False, f"HTTP {response.status_code}")
        
        # 3. Enhanced Autonomous Collaboration
        payload = {
            "topic": "AI-Powered Creative Collaboration Tools",
            "agents": ["strategist", "creator", "analyst"],
            "collaboration_mode": "autonomous",
            "max_rounds": 2,
            "streaming_enabled": True
        }
        
        response = await client.post(f"{BACKEND_URL}/conversation/autonomous", json=payload)
        if response.status_code == 200:
            data = response.json()
            conversation_id = data["conversation_id"]
            log_result("Enhanced Autonomous Collaboration", True, f"Started with streaming: {conversation_id}")
            
            # Wait for completion
            await asyncio.sleep(15)
            
            # 4. Conversation Summary
            response = await client.get(f"{BACKEND_URL}/conversation/{conversation_id}/summary")
            if response.status_code == 200:
                summary_data = response.json()
                if len(summary_data["summary"]) > 100:
                    log_result("AI-Powered Conversation Summary", True, f"Generated {len(summary_data['summary'])} char summary")
                else:
                    log_result("AI-Powered Conversation Summary", False, "Summary too short")
            else:
                log_result("AI-Powered Conversation Summary", False, f"HTTP {response.status_code}")
            
            # 5. Conversation Export - JSON
            export_payload = {"conversation_id": conversation_id, "format": "json"}
            response = await client.post(f"{BACKEND_URL}/conversation/{conversation_id}/export", json=export_payload)
            if response.status_code == 200:
                export_data = response.json()
                if export_data["format"] == "json" and "data" in export_data:
                    log_result("Conversation Export JSON", True, f"Exported {len(export_data['data']['messages'])} messages")
                else:
                    log_result("Conversation Export JSON", False, "Invalid export format")
            else:
                log_result("Conversation Export JSON", False, f"HTTP {response.status_code}")
            
            # 6. Conversation Export - Markdown
            export_payload = {"conversation_id": conversation_id, "format": "markdown"}
            response = await client.post(f"{BACKEND_URL}/conversation/{conversation_id}/export", json=export_payload)
            if response.status_code == 200:
                export_data = response.json()
                if export_data["format"] == "markdown" and len(export_data["content"]) > 200:
                    log_result("Conversation Export Markdown", True, f"Generated {len(export_data['content'])} char markdown")
                else:
                    log_result("Conversation Export Markdown", False, "Markdown too short")
            else:
                log_result("Conversation Export Markdown", False, f"HTTP {response.status_code}")
            
            # 7. Enhanced Polling
            response = await client.get(f"{BACKEND_URL}/conversation/{conversation_id}/poll")
            if response.status_code == 200:
                poll_data = response.json()
                enhanced_fields = ["conversation_id", "messages", "total_messages", "last_updated", "conversation_status"]
                if all(field in poll_data for field in enhanced_fields):
                    log_result("Enhanced Polling System", True, f"All enhanced fields present, {poll_data['total_messages']} messages")
                else:
                    log_result("Enhanced Polling System", False, "Missing enhanced fields")
            else:
                log_result("Enhanced Polling System", False, f"HTTP {response.status_code}")
        
        else:
            log_result("Enhanced Autonomous Collaboration", False, f"HTTP {response.status_code}")
        
        # 8. Agent Analytics
        response = await client.get(f"{BACKEND_URL}/analytics/agents")
        if response.status_code == 200:
            analytics_data = response.json()
            if "agent_metrics" in analytics_data:
                log_result("Agent Performance Analytics", True, f"Analytics for {len(analytics_data['agent_metrics'])} agents")
            else:
                log_result("Agent Performance Analytics", False, "Missing agent_metrics")
        else:
            log_result("Agent Performance Analytics", False, f"HTTP {response.status_code}")
        
        # 9. Connection Pooling & Performance (test multiple requests)
        start_time = datetime.now()
        tasks = []
        for i in range(5):
            tasks.append(client.get(f"{BACKEND_URL}/agents"))
        
        responses = await asyncio.gather(*tasks)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        successful_requests = sum(1 for r in responses if r.status_code == 200)
        if successful_requests == 5 and duration < 5:
            log_result("Connection Pooling & Performance", True, f"5 concurrent requests in {duration:.2f}s")
        else:
            log_result("Connection Pooling & Performance", False, f"Only {successful_requests}/5 successful in {duration:.2f}s")
        
        # 10. Error Handling & Retry Logic (check stats for error rates)
        response = await client.get(f"{BACKEND_URL}/stats")
        if response.status_code == 200:
            stats_data = response.json()
            total_requests = stats_data["summary"]["total_requests"]
            total_errors = stats_data["summary"]["total_errors"]
            error_rate = (total_errors / max(total_requests, 1)) * 100
            
            if error_rate < 10:  # Less than 10% error rate
                log_result("Error Handling & Retry Logic", True, f"Low error rate: {error_rate:.1f}% ({total_errors}/{total_requests})")
            else:
                log_result("Error Handling & Retry Logic", False, f"High error rate: {error_rate:.1f}%")
        else:
            log_result("Error Handling & Retry Logic", False, "Could not get stats")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 FINAL TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in results if r["success"])
        total = len(results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if total - passed > 0:
            print("\n❌ FAILED TESTS:")
            for result in results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        else:
            print("\n🎉 ALL TESTS PASSED!")
        
        print("\n✅ WORKING ENHANCED FEATURES:")
        for result in results:
            if result["success"]:
                print(f"  ✓ {result['test']}")
        
    except Exception as e:
        print(f"❌ Exception in final test: {str(e)}")
    
    finally:
        await client.aclose()
    
    return results

if __name__ == "__main__":
    asyncio.run(run_final_test())