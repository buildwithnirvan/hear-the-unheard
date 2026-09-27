"""
Connects to the real running backend's /ws/recognize endpoint and streams
actual frames from a real dataset clip, exactly as a browser would send
webcam frames. Verifies real status + recognition messages come back —
not a mock of the websocket, an actual client/server round trip.
"""
import asyncio
import json
import sys

import cv2
import websockets


async def stream_video(video_path: str, ws_url: str = "ws://127.0.0.1:8000/ws/recognize"):
    cap = cv2.VideoCapture(video_path)
    recognitions = []
    statuses = []

    async with websockets.connect(ws_url) as ws:
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            ok, jpeg = cv2.imencode(".jpg", frame)
            if not ok:
                continue
            await ws.send(jpeg.tobytes())
            frame_count += 1

            msg = json.loads(await ws.recv())
            if msg["type"] == "status":
                statuses.append(msg)
            elif msg["type"] == "recognition":
                recognitions.append(msg)
                print(f"  RECOGNIZED: {msg['gloss']} (confidence={msg['confidence']:.2f}, "
                      f"window={msg['window_frames']} frames)")
            elif msg["type"] == "error":
                print(f"  ERROR: {msg['detail']}")

        cap.release()

        # Explicit end-of-stream handshake: tells the server to flush any
        # sign that was still open when the clip ran out, and — critically
        # — we stay connected and keep listening for the response instead
        # of closing immediately, since a message sent after we've already
        # disconnected would just be lost.
        await ws.send(json.dumps({"type": "end_of_stream"}))
        while True:
            msg = json.loads(await ws.recv())
            if msg["type"] == "recognition":
                recognitions.append(msg)
                tag = " (flushed at stream end)" if msg.get("flushed_at_stream_end") else ""
                print(f"  RECOGNIZED: {msg['gloss']} (confidence={msg['confidence']:.2f}, "
                      f"window={msg['window_frames']} frames){tag}")
            elif msg["type"] == "stream_ended":
                break

    print(f"\nStreamed {frame_count} frames, got {len(statuses)} status messages, "
          f"{len(recognitions)} recognition(s)")
    return recognitions


if __name__ == "__main__":
    video_path = sys.argv[1] if len(sys.argv) > 1 else None
    if not video_path:
        print("Usage: python test_ws_client.py <path-to-video>")
        sys.exit(1)
    asyncio.run(stream_video(video_path))
