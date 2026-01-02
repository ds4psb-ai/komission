#!/usr/bin/env python3
"""
Coaching WebSocket Test Script

Tests the time-based checkpoint evaluation loop:
1. Connect to WebSocket
2. Send control.start
3. Wait for feedback messages
4. Check if coaching is triggered based on time
"""
import asyncio
import json
import sys

try:
    import websockets
except ImportError:
    print("Installing websockets...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets", "-q"])
    import websockets


async def test_coaching_websocket():
    session_id = "test_session_001"
    uri = f"ws://localhost:8000/api/v1/ws/coaching/{session_id}?language=ko&voice_style=friendly"
    
    print(f"\n{'='*60}")
    print(f"🎬 Coaching WebSocket Test")
    print(f"{'='*60}")
    print(f"URI: {uri}")
    print()
    
    try:
        async with websockets.connect(uri) as ws:
            print("✅ Connected to WebSocket")
            
            # 1. Receive initial status
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(msg)
            print(f"\n📩 Initial Status: {data.get('status')}")
            print(f"   Session ID: {data.get('session_id')}")
            
            # 2. Send control.start
            print("\n📤 Sending control.start...")
            await ws.send(json.dumps({
                "type": "control",
                "action": "start"
            }))
            
            # 3. Receive recording status
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(msg)
            print(f"📩 Recording Status: {data.get('status')}")
            print(f"   gemini_connected: {data.get('gemini_connected')}")
            print(f"   rules_count: {data.get('rules_count')}")
            print(f"   fallback_mode: {data.get('fallback_mode')}")
            print(f"   checkpoint_evaluation: {data.get('checkpoint_evaluation')}")
            
            # 4. Simulate audio chunks (to update recording time)
            print("\n🎙️ Simulating 10 seconds of recording...")
            print("   (Sending audio chunks to update recording_time)")
            
            feedback_received = []
            
            for sec in range(10):
                # Send dummy audio chunk (16kHz, 16-bit, 1 second = 32000 bytes)
                # We send base64 encoded "audio" - just dummy data to increment time
                import base64
                dummy_audio = base64.b64encode(b'\x00' * 32000).decode()
                
                await ws.send(json.dumps({
                    "type": "audio",
                    "data": dummy_audio
                }))
                
                # Check for feedback messages (non-blocking)
                try:
                    while True:
                        msg = await asyncio.wait_for(ws.recv(), timeout=0.5)
                        data = json.loads(msg)
                        
                        if data.get("type") == "feedback":
                            print(f"\n🗣️ COACHING @ {sec}s: {data.get('message')}")
                            print(f"   checkpoint_time: {data.get('checkpoint_time')}")
                            print(f"   audio_format: {data.get('audio_format')}")
                            has_audio = data.get('audio_b64') is not None
                            print(f"   has_audio: {has_audio}")
                            feedback_received.append(data)
                        elif data.get("type") == "audio_response":
                            print(f"\n🔊 Gemini Audio Response received")
                        elif data.get("type") == "error":
                            print(f"\n❌ Error: {data.get('message')}")
                        else:
                            print(f"\n📩 Other message: {data.get('type')}")
                            
                except asyncio.TimeoutError:
                    pass  # No more messages
                
                print(f"   [{sec+1}s] ...", end="", flush=True)
                await asyncio.sleep(0.5)  # Wait before next chunk
            
            print("\n")
            
            # 5. Send control.stop
            print("📤 Sending control.stop...")
            await ws.send(json.dumps({
                "type": "control",
                "action": "stop"
            }))
            
            # 6. Receive final status
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(msg)
            print(f"📩 Final Status: {data.get('status')}")
            if data.get('stats'):
                stats = data['stats']
                print(f"   total_time: {stats.get('total_time', 0):.1f}s")
                print(f"   interventions_sent: {stats.get('interventions_sent', 0)}")
                print(f"   rules_evaluated: {stats.get('rules_evaluated', 0)}")
            
            # 7. Summary
            print(f"\n{'='*60}")
            print(f"📊 TEST SUMMARY")
            print(f"{'='*60}")
            print(f"Total feedback messages: {len(feedback_received)}")
            
            if feedback_received:
                print("✅ Checkpoint evaluation loop is WORKING!")
                for i, fb in enumerate(feedback_received, 1):
                    print(f"   {i}. [{fb.get('checkpoint_time', '?')}s] {fb.get('message', '')[:40]}...")
            else:
                print("⚠️ No feedback received - check DirectorPack checkpoints")
            
            print()
            
    except ConnectionRefusedError:
        print("❌ Connection refused - is the server running?")
        print("   Run: cd /Users/ted/komission/backend && uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_coaching_websocket())
